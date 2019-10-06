#!/usr/bin/env python3

import os
import sys
from pathlib import Path
import subprocess
import tempfile

from common import Timer, TestSystem, main
from common import Token, Morph, Sentence, rftag2stts, string2doc

CORENLP_HOME = "/opt/stanford-corenlp-full-2018-10-05"

# gold annotations to hide from the test systems
HIDDEN_FIELDS = ["lemma", "upos", "xpos", "feats", "head", "deprel", "deps"]


class StanfordNLP(TestSystem):
    def __init__(self):
        self.name = "stanfordnlp"
        with Timer() as self.model_load_time:
            from stanfordnlp import Pipeline

            self.processor = Pipeline(
                lang="de",
                tokenize_pretokenized=True,
                processors="tokenize,mwt,pos,lemma",
            )

    def postprocess(self):
        self.data = string2doc(self.output_data.conll_file.conll_as_string())


class RFTagger(TestSystem):
    def __init__(self):
        self.home = Path("/opt/RFTagger")
        with Timer() as self.model_load_time:
            # just load the model
            CLASSPATH = ":".join(
                [
                    str(self.home / "jars/rft-java-beta13.jar"),
                    str(self.home / "jars/jna-4.5.1.jar"),
                ]
            )
            import jpype

            jpype.startJVM(
                jpype.getDefaultJVMPath(), "-ea", "-Djava.class.path=" + CLASSPATH
            )
            rftagger = jpype.JPackage("de.sfb833.a4").RFTagger
            fn = jpype.java.io.File(str(self.home / "lib/german.par"))
            model = rftagger.Model(fn)
            self.tagger = rftagger.RFTagger(model)

            # conversion to STTS
            self.stts_converter = rftagger.tagsetconv.ConverterFactory.getConverter(
                "stts"
            )

            # tag corrector
            self.tag_corrector = rftagger.tagcorrector.TagCorrectorFactory.getTagCorrector(
                "german"
            )

            # lemmatizer
            self.lemmatizer = rftagger.lemmatizer.LemmatizerFactory.getLemmatizer(
                "german",
                jpype.java.io.File(
                    str(self.home / "lib/german-rft-tagger-lemma-lexicon-corrected.txt")
                ),
            )

            def myprocessor(myinput):
                # assuming myinput is one sent per line with
                # space-separated tokens
                result = list()
                for sent in myinput.split("\n"):
                    tokens = jpype.java.util.ArrayList()
                    for token in sent.split():
                        tokens.add(token)
                    newsent = list()
                    for entry in zip(tokens, self.tagger.getTags(tokens)):
                        tok, tag = entry
                        corrected_tag = self.tag_corrector.correctTag(tag)
                        stts = self.stts_converter.rftag2tag(tag)
                        lemma = self.lemmatizer.getLemma(tok, corrected_tag)
                        newsent.append((tok, tag, stts, lemma))
                    result.append(newsent)
                return result

            self.processor = myprocessor

    # def __del__(self):
    #     jpype.shutdownJVM()  # not sure if this is the right way
    # (or necessary)

    def postprocess(self):
        self.data = list()
        for sent in self.output_data:
            mytokens = list()
            for tok in sent:
                text, rftmorph, stts, lemma = tok
                mytokens.append(
                    Token(
                        word=text,
                        xpos=stts,
                        feats=str(Morph.from_rftag(rftmorph)),
                        lemma=lemma,
                    )
                )
            self.data.append(Sentence(mytokens))


class TreeTagger(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            import treetaggerwrapper

            self.tagger = treetaggerwrapper.TreeTagger(TAGLANG="de")

            def myprocessor(myinput):
                sents = myinput.split("\n")
                return self.tagger.tag_text(" </s> ".join(sents).split(), tagonly=True)

            self.processor = myprocessor

    def postprocess(self):
        self.data = list()
        senttokens = list()
        for token in self.output_data:
            if token == "</s>":
                self.data.append(Sentence(senttokens))
                senttokens = list()
            else:
                tok, tag, lemma = token.split("\t")
                senttokens.append(Token(word=tok, xpos=tag, lemma=lemma))
        if senttokens:  # add last sentence
            self.data.append(Sentence(senttokens))


class RNNTagger(TestSystem):
    def __init__(self):
        self.home = Path("/opt/RNNTagger")
        with Timer() as self.model_load_time:
            sys.path.insert(0, str(self.home))
            sys.path.insert(0, str(self.home / "PyNMT"))
            import torch
            from PyRNN.Data import Data
            from PyRNN.rnn_annotate import annotate_sentence

            self.vector_mappings = Data(str(self.home / "lib/PyRNN/german.io"))
            self.model = torch.load(str(self.home / "lib/PyRNN/german.rnn"))
            torch.cuda.set_device(0)
            self.model = self.model.cuda()
            self.model.eval()
            print("RNNTagger using GPU:", self.model.on_gpu(), file=sys.stderr)

            def myprocessor(myinput):
                output = list()
                for line in myinput.split("\n"):
                    if line:
                        tokens = line.strip().split()
                        tags = annotate_sentence(
                            self.model, self.vector_mappings, tokens
                        )
                        tagged_sent = "\n".join(
                            tok + "\t" + tag for tok, tag in zip(tokens, tags)
                        )
                        output.append(tagged_sent)
                _, tmp_tagged_path = tempfile.mkstemp(text=True)
                with open(tmp_tagged_path, "w", encoding="utf-8") as tmpfile:
                    print("\n\n".join(output), file=tmpfile)
                result = subprocess.run(
                    ["bash", "rnn-tagger-lemmatizer.sh", tmp_tagged_path],
                    capture_output=True,
                    text=True,
                )
                os.remove(tmp_tagged_path)
                return result.stdout

            self.processor = myprocessor

    def postprocess(self):
        self.data = list()
        for sent in self.output_data.rstrip().split("\n\n"):
            mytokens = list()
            for token_entry in sent.split("\n"):
                tok, tag, lemma = token_entry.split("\t")
                maintag = tag.split(".")[0]
                # kleine korrektur
                stts = "$." if maintag == "$" else maintag
                mytokens.append(
                    Token(
                        word=tok,
                        xpos=stts,
                        lemma=lemma,
                        feats=str(Morph.from_tigertag(tag)),
                    )
                )
            self.data.append(Sentence(mytokens))


class SoMeWeTa(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            from someweta import ASPTagger

            # TODO: decide where to store models (prob not here)
            model = "/home/roussel/Downloads/german_newspaper_2018-12-21.model"
            self.tagger = ASPTagger(beam_size=5, iterations=10)
            self.tagger.load(model)

            def myprocessor(myinput):
                sentences = [line.split() for line in myinput.split("\n")]
                return [self.tagger.tag_sentence(sent) for sent in sentences]

            self.processor = myprocessor

    def postprocess(self):
        """re-format output_data so that it conforms to eval format"""
        self.data = list()
        for sent in self.output_data:
            self.data.append(Sentence(Token(word=tok, xpos=tag) for tok, tag in sent))


class CoreNLP(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            os.environ["CORENLP_HOME"] = CORENLP_HOME
            from stanfordnlp.server import CoreNLPClient

            self.client = CoreNLPClient(
                annotators="tokenize,ssplit,pos,lemma",
                timeout=30000,
                be_quiet=True,
                properties={
                    "tokenize.whitespace": "true",
                    "tokenize.keepeol": "true",
                    "pos.model": "edu/stanford/nlp/models/pos-tagger/german/german-hgc.tagger",
                },
            )
            self.processor = self.client.annotate

    def postprocess(self):
        self.data = list()
        for sent in self.output_data.sentence:
            self.data.append(
                Sentence(Token(word=tok.word, xpos=tok.pos) for tok in sent.token)
            )


class Spacy(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            # https://spacy.io/usage/linguistic-features#own-annotations
            import spacy
            from spacy.tokens import Doc

            activated = spacy.prefer_gpu()
            print("spaCy using GPU:", activated, file=sys.stderr)
            self.nlp = spacy.load("de_core_news_md", disable=["parser", "ner"])

            def myprocessor(myinput):
                results = list()
                # this way we preserve sent boundaries
                # could also set sent bounds like this: token.is_sent_start = True
                # but this seems easier
                for line in myinput.rstrip().split("\n"):
                    doc = Doc(self.nlp.vocab, words=line.split())
                    results.append(self.nlp.pipeline[0][1](doc))
                return results

            self.processor = myprocessor

    def postprocess(self):
        self.data = list()
        for sent_doc in self.output_data:
            self.data.append(
                Sentence(
                    Token(word=str(tok), xpos=tok.tag_, upos=tok.pos_, lemma=tok.lemma_)
                    for tok in sent_doc
                )
            )


class Clevertagger(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            sys.path.insert(0, "/opt/clevertagger-master")
            import clevertagger

            self.tagger = clevertagger.Clevertagger()

            def myprocessor(myinput):
                return self.tagger.tag([line for line in myinput.rstrip().split("\n")])

            self.processor = myprocessor

    def postprocess(self):
        self.data = list()
        for sent in self.output_data:
            senttokens = list()
            for tok in sent.split("\n"):
                token, tag = tok.split("\t")
                stts = rftag2stts(tag)
                senttokens.append(
                    Token(word=token, xpos=stts, feats=str(Morph.from_rftag(tag)))
                )
            self.data.append(Sentence(senttokens))


class UDPipe(TestSystem):
    pass  # TODO


if __name__ == "__main__":
    main(
        # "tokens",
        "pos",
        [
            StanfordNLP,
            RFTagger,
            TreeTagger,
            RNNTagger,
            SoMeWeTa,
            CoreNLP,
            Clevertagger,
            Spacy,
        ],
    )

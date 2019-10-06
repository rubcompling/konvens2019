#!/usr/bin/env python3

import sys
from pathlib import Path

import common
from common import Timer, TestSystem, main
from common import Sentence, Token, Morph, string2doc, doc2string
from adjust_tokens import add_upos_tags

from spacy.symbols import TAG
import numpy as np
from spacy.tokens import Doc


HIDDEN_FIELDS = ["head", "deprel", "deps"]


class StanfordNLP(TestSystem):
    def __init__(self):
        self.name = "stanfordnlp"
        with Timer() as self.model_load_time:
            from stanfordnlp import Pipeline, Document
            from stanfordnlp.models.common.conll import CoNLLFile

            self.pipeline = Pipeline(
                lang="de",
                tokenize_pretokenized=True,
                processors="depparse",
                # lower batch size so our GPU can cope
                depparse_batch_size=1000,
            )

            def myprocessor(myinput):
                # run input through converter to hide fields, etc.
                self.input_doc = common.Document(myinput, hidden_fields=HIDDEN_FIELDS)
                modified_input = doc2string(self.input_doc)
                self.snlp_doc = Document("")
                self.snlp_doc.conll_file = CoNLLFile(input_str=modified_input)
                self.snlp_doc.load_annotations()
                return self.pipeline(self.snlp_doc)

            self.processor = myprocessor

    def postprocess(self):
        self.data = list()
        for sent in self.output_data.sentences:
            self.data.append(
                Sentence(
                    Token(
                        id=tok.index,
                        word=tok.text,
                        lemma=tok.lemma,
                        feats=tok.feats,
                        head=str(tok.governor),
                        deprel=tok.dependency_relation,
                    )
                    for tok in sent.words
                )
            )


class CoreNLP(TestSystem):
    def __init__(self):
        self.home = Path("/opt/stanford-corenlp-full-2018-10-05/")
        with Timer() as self.model_load_time:
            import jpype

            jpype.startJVM(
                jpype.getDefaultJVMPath(),
                "-ea",
                "-Djava.class.path=" + str(self.home / "stanford-corenlp-3.9.2.jar"),
            )

            ling = jpype.JPackage("edu").stanford.nlp.ling
            nndep = jpype.JPackage("edu").stanford.nlp.parser.nndep

            self.parser = nndep.DependencyParser.loadFromModelFile(
                str(
                    self.home
                    / "stanford-german-corenlp-2018-10-05-models"
                    / "edu/stanford/nlp/models/parser/nndep/UD_German.gz"
                )
            )

            def myprocessor(myinput):
                results = list()
                for sent in string2doc(myinput, hide_fields=HIDDEN_FIELDS):
                    sent_arr = jpype.java.util.ArrayList()
                    for tok in sent:
                        sent_arr.add(ling.TaggedWord(tok.word, tok.xpos))
                    results.append(self.parser.predict(sent_arr))
                return results

            self.processor = myprocessor

    def postprocess(self):
        self.data = list()
        for sent in self.output_data:
            self.data.append(
                Sentence(
                    Token(
                        id=str(rel.dep().index()),
                        word=rel.dep().word(),
                        # don't write out gold pos
                        #   xpos=rel.dep().tag(),
                        head=str(rel.gov().index()),
                        deprel=str(rel.reln()),
                    )
                    for rel in sent.typedDependencies()
                )
            )


class Spacy(TestSystem):
    # how to preserve existing pos tags? necessary?
    def __init__(self):
        with Timer() as self.model_load_time:
            # https://spacy.io/usage/linguistic-features#own-annotations
            # https://spacy.io/usage/processing-pipelines#wrapping-models-libraries
            # https://github.com/explosion/spacy-stanfordnlp/blob/master/spacy_stanfordnlp/language.py
            import spacy

            self.nlp = spacy.load("de", disable=["tagger", "ner"])

            def myprocessor(myinput):
                mydoc = self.read_conlldoc(myinput)
                return self.nlp.pipeline[0][1](mydoc)

            self.processor = myprocessor

    def read_conlldoc(self, inputdoc):
        words = list()
        sentbounds = list()
        #    pos = list()
        tags = list()
        #    lemmas = list()
        for sent in string2doc(inputdoc, hide_fields=HIDDEN_FIELDS):
            for i, tok in enumerate(sent):
                if i == 0:
                    sentbounds.append(True)
                else:
                    sentbounds.append(False)
                words.append(tok.word)
                tags.append(self.nlp.vocab.strings.add(tok.xpos))
                # pos.append(self.nlp.vocab.strings.add(conv_table.get(tok.xpos, "_")))
        #            lemmas.append(self.nlp.vocab.strings.add(tok.lemma))
        # attrs = [POS, TAG]
        attrs = [TAG]
        # arr = np.array(list(zip(pos, tags)), dtype="uint64")
        arr = np.array(tags, dtype="uint64")
        sdoc = Doc(self.nlp.vocab, words=words).from_array(attrs, arr)
        for i, sb in enumerate(sentbounds):
            if sb:
                sdoc[i].is_sent_start = True
            else:
                # these must be set to False, since,
                # if left as None, spaCy will add further sentbounds
                sdoc[i].is_sent_start = False
        #    lemma_array = np.array([[lemma] for lemma in lemmas], dtype="uint64")
        #    sdoc.from_array([LEMMA], lemma_array)
        if any(tags):
            sdoc.is_tagged = True
        return sdoc

    def postprocess(self):
        self.data = list()
        for sent in self.output_data.sents:
            self.data.append(
                Sentence(
                    Token(
                        word=tok.text,
                        lemma=tok.lemma_,
                        # upos=tok.pos_,
                        #   xpos=tok.tag_,
                        head=str(tok.head.i - sent[0].i + 1),
                        deprel=tok.dep_,
                    )
                    for tok in sent
                )
            )


class ParZu(TestSystem):
    # has option for tagged input text, inputformat = tagged
    def __init__(self):
        with Timer() as self.model_load_time:
            sys.path.insert(0, "/opt/ParZu")
            from parzu_class import process_arguments, Parser

            self.opts = process_arguments(commandline=False)
            self.parser = Parser(self.opts)

            def myprocessor(myinput):
                newinput = list()
                for sent in string2doc(myinput, hide_fields=HIDDEN_FIELDS):
                    sent_strs = list()
                    for tok in sent:
                        sent_strs.append(tok.word + "\t" + tok.xpos)
                    newinput.append("\n".join(sent_strs))
                reformatted_input = "\n\n".join(newinput)

                return self.parser.main(
                    reformatted_input, inputformat="tagged", outputformat="conll"
                )

            self.processor = myprocessor

    def postprocess(self):
        self.data = list()
        for sent in self.output_data:
            mytokens = list()
            for tok in sent.rstrip().split("\n"):
                (
                    index,
                    word,
                    lemma,
                    upos,
                    xpos,
                    feats,
                    head,
                    deprel,
                    deps,
                    misc,
                ) = tok.split("\t")
                mytokens.append(
                    Token(
                        id=index,
                        word=word,
                        lemma=lemma,
                        # don't write out gold pos
                        # upos=upos, xpos=xpos,
                        feats=str(Morph.from_parzu(xpos + "|" + feats)),
                        head=head,
                        deprel=deprel,
                        deps=deps,
                        misc=misc,
                    )
                )
            self.data.append(Sentence(mytokens))


class UDPipe(TestSystem):
    # maybe
    pass


if __name__ == "__main__":
    main("depparse", [CoreNLP, ParZu, Spacy, StanfordNLP])

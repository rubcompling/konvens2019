#!/usr/bin/env python3

from common import Timer, TestSystem, main


class Spacy(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            import spacy

            nlp = spacy.load("de", disable=["tagger", "parser", "ner"])
            nlp.add_pipe(nlp.create_pipe("sentencizer"))
            self.processor = nlp

    def postprocess(self):
        self.data = "\n".join(
            " ".join(tok.text for tok in sent) for sent in self.output_data.sents
        )


class SpacyDepSents(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            import spacy

            nlp = spacy.load("de_core_news_md", disable=["tagger", "ner"])
            self.processor = nlp

    def postprocess(self):
        self.data = "\n".join(
            " ".join(tok.text for tok in sent) for sent in self.output_data.sents
        )


class NLTK(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            from nltk.tokenize import word_tokenize, sent_tokenize

            # NB: processor functions are always defined this way so
            # they can be factored into model load times --
            # important since some systems will actually load models
            # here (if they use them)
            def myprocessor(myinput):
                sentences = sent_tokenize(myinput, language="german")
                return [word_tokenize(sent, language="german") for sent in sentences]

            self.processor = myprocessor

    def postprocess(self):
        out_sentences = list()
        for sent in self.output_data:
            out_sentences.append(
                " ".join(tok.replace("``", '"').replace("''", '"') for tok in sent)
            )
        self.data = "\n".join(out_sentences)


class StanfordNLP(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            from stanfordnlp import Pipeline

            self.processor = Pipeline(
                lang="de",
                # 'mwt' processor would expand things
                # like 'am' to 'an dem'
                processors="tokenize",
            )

    def postprocess(self):
        self.data = "\n".join(
            " ".join(tok.text for tok in sent.words)
            for sent in self.output_data.sentences
        )


class Syntok(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            from syntok.tokenizer import Tokenizer
            import syntok.segmenter as segmenter

            def myprocessor(myinput):
                tokenizer = Tokenizer(
                    emit_hyphen_or_underscore_sep=True, replace_not_contraction=False
                )
                tokenized = tokenizer.tokenize(myinput)
                return segmenter.segment(tokenized)

            self.processor = myprocessor

    def postprocess(self):
        self.data = "\n".join(
            " ".join(tok.value for tok in sent) for sent in self.output_data
        )


class CoreNLP(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            from stanfordnlp.server import CoreNLPClient

            client = CoreNLPClient(
                annotators=["tokenize", "ssplit"],
                timeout=30000,
                memory="2G",
                properties={"tokenize.language": "de", "outputFormat": "text"},
            )
            self.processor = client.annotate

    def postprocess(self):
        self.data = "\n".join(
            " ".join(tok.originalText for tok in sent.token)
            for sent in self.output_data.sentence
        )


class SoMaJo(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            from somajo import Tokenizer, SentenceSplitter

            def myprocessor(myinput):
                tokenizer = Tokenizer(language="de")
                sentsplitter = SentenceSplitter(language="de")
                tokenized = tokenizer.tokenize_paragraph(myinput)
                sentsplit = sentsplitter.split(tokenized)
                return sentsplit

            self.processor = myprocessor

    def postprocess(self):
        """re-format output_data so that it conforms to eval format"""
        self.data = "\n".join(" ".join(sent) for sent in self.output_data)


class Baseline(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:

            def myprocessor(myinput):
                tokens = myinput.split()
                sents = list()
                stack = list()
                for tok in tokens:
                    stack.append(tok)
                    if tok.endswith((".", "?", "!")):
                        sents.append(stack)
                        stack = list()
                sents.append(stack)
                return sents
            
            self.processor = myprocessor

    def postprocess(self):
        self.data = "\n".join(" ".join(sent) for sent in self.output_data)


# seems to *always* expand multi-word tokens
# (apparently a UD standard to do this)
# we'll just skip this tokenizer and test the other components
# def UDPipe(TestSystem):
#     def __init__(self):
#         with Timer() as self.model_load_time:


if __name__ == "__main__":
    main(
        "tokens",
        [Spacy, SpacyDepSents, NLTK, StanfordNLP, Syntok, CoreNLP, SoMaJo, Baseline],
    )

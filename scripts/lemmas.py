#!/usr/bin/env python3

"""
Für unabhängige Lemmatizer
"""


import os
import sys
from pathlib import Path

from common import Timer, TestSystem, main
from common import string2doc, doc2string

# hide these gold annotations in system output
HIDDEN_FIELDS = ["upos", "xpos", "feats", "head", "deprel", "deps"]


class GermaLemma(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            import germalemma
            # NB: pattern module causes exception in python3 (maybe?)
            self.lemmatizer = germalemma.GermaLemma(pickle=os.environ["GERMALEMMA_MODEL"],
                                                    use_pattern_module=True)

            def myprocessor(myinput):
                mydoc = string2doc(myinput)
                for sent in mydoc:
                    for tok in sent:
                        try:
                            tok.lemma = self.lemmatizer.find_lemma(tok.word, tok.xpos)
                        except ValueError:
                            # unsupported POS
                            # use empty lemma
                            tok.lemma = "_"
                        # don't repeat gold pos in output
                        tok.hide_fields(HIDDEN_FIELDS)
                return mydoc

            self.processor = myprocessor

    def postprocess(self):
        self.data = doc2string(self.output_data)


class CustomLemmatizer(TestSystem):
    def __init__(self):
        self.home = Path("/opt/BOling")
        with Timer() as self.model_load_time:
            sys.path.insert(0, str(self.home / "src"))
            from lemmatize import lemmatize_sentence

            def myprocessor(myinput):
                mydoc = string2doc(myinput)
                for sent in mydoc:
                    tokens = [t.word for t in sent]
                    tags = [t.xpos for t in sent]
                    lemmas = lemmatize_sentence(tokens, tags)
                    for tok, lem in zip(sent, lemmas):
                        tok.hide_fields(HIDDEN_FIELDS)
                        tok.lemma = lem
                return mydoc

            self.processor = myprocessor

    def postprocess(self):
        self.data = doc2string(self.output_data)


class IWNLP(TestSystem):
    def __init__(self):
        with Timer() as self.model_load_time:
            from iwnlp.iwnlp_wrapper import IWNLPWrapper
            from stts2upos import conv_table
            # "/opt/iwnlp/IWNLP.Lemmatizer_20181001.json"
            data_loc = os.environ["IWNLP_MODEL"] 
            self.lemmatizer = IWNLPWrapper(lemmatizer_path=data_loc)

            def myprocessor(myinput):
                mydoc = string2doc(myinput)
                for sent in mydoc:
                    for tok in sent:
                        try:
                            matching_lemmas = self.lemmatizer.lemmatize(tok.word, conv_table.get(tok.xpos))
                            if matching_lemmas is None:
                                tok.lemma = "_"
                                # elif len(matching_lemmas) > 1:
                                #     print("lots o lemmas!", matching_lemmas)
                            else:
                                # unclear how to select best alternative
                                # just use first item in list
                                tok.lemma = matching_lemmas[0]
                        except ValueError:
                            tok.lemma = "_"
                        # don't repeat gold pos in output
                        tok.hide_fields(HIDDEN_FIELDS)
                return mydoc

            self.processor = myprocessor

    def postprocess(self):
        self.data = doc2string(self.output_data)


if __name__ == "__main__":
    main("lemmas", [GermaLemma, CustomLemmatizer, IWNLP])

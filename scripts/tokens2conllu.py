#!/usr/bin/env python3

"""
Simple script for converting from one-sentence-per-line format to CoNLL-U
"""

import sys

# standard Doc is a list of lists of these
# each sublist = sentence
class Token:
    fields = "id word lemma upos xpos feats head deprel deps misc".split()

    def __init__(self, **kwargs):
        for key in Token.fields:
            self.__dict__[key] = kwargs.get(key, "_")

        # disable morph interpretation here
        # self.feats = str(Morph(from_string=self.feats))

    def __str__(self):
        return "\t".join(self.__dict__.get(key, "_") for key in Token.fields)

    @classmethod
    def from_str(cls, instring):
        return cls(**dict(zip(Token.fields, instring.rstrip().split("\t"))))


class Sentence:
    """Use this class instead of plain lists to make sure
       tokens get correct IDs. """

    def __init__(self):
        self.i = 1
        self.tokens = list()

    def add(self, token):
        if token.id == "_":
            token.id = str(self.i)
            self.i += 1
        elif "-" in token.id:
            self.i = int(token.id.split("-")[1]) + 1
        else:
            self.i = int(token.id) + 1
        # make sure `head` is also `int`-like
        if token.head == "_":
            token.head = token.id
        self.tokens.append(token)

    def __iter__(self):
        return iter(self.tokens)

    def __str__(self):
        return "\n".join(str(entry) for entry in self.tokens) + "\n\n"


for line in sys.stdin:
    line = line.rstrip().split()
    if line:
        print(Sentence(Token(word=tok) for tok in line), end="")

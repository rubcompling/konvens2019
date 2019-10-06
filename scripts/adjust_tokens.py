#!/usr/bin/env python3

import sys
from common import Document, Token, doc2string
from eval_annotations import APPRARTMAP
from stts2upos import conv_table


def retokenize(input_data) -> Document:
    #  get input from stdin
    doc = Document(input_data)

    # for tok in Doc
    #  if tok is APPRART
    #   use map to find new tokens
    #   replace xpos with APPR + ART
    #   set feats on ART
    for sent in doc.sentences:
        new_tok_locations = list()
        for i, tok in enumerate(sent):
            if tok.xpos == "APPRART":
                try:
                    appr, art = APPRARTMAP.get(tok.word.lower())
                    if tok.word[0].isupper():
                        appr = appr.capitalize()
                except TypeError:
                    print(tok, file=sys.stderr)
                    exit(1)

                new_tok = Token(word=art, lemma="der", xpos="ART", feats=tok.feats, head=tok.head)

                tok.word = appr
                tok.xpos = "APPR"
                tok.feats = "_"
                # assuming that the article will point to the noun,
                # set the preposition to point to the article
                tok.head = new_tok.id

                sent.tokens.insert(i + 1, new_tok)
                # remember where new tokens were added!
                # -> all head references afterwards must be updated!
                new_tok_locations.append(i)

            # TODO also handle PTKA="am", as in "am besten" -> "an dem besten"

        # then renumber tokens per sentence before sending to output
        for i, tok in enumerate(sent):
            tok.id = str(i + 1)
            if tok.head.isdigit():
                for new_tok_index in new_tok_locations:
                    if int(tok.head) > new_tok_index:
                        tok.head = str(int(tok.head) + 1)

    return doc

def add_upos_tags(a_doc):
    for sent in a_doc.sentences:
        for token in sent.tokens:
            token.upos = conv_table.get(token.xpos, "_")
    return a_doc


if __name__ == "__main__":
    # no need to do this after all, it seems
    # ud_tokenized_doc = retokenize(sys.stdin)
    # ud_tokenized_doc = add_upos_tags(ud_tokenized_doc)
    input_data = Document(sys.stdin)
    ud_tokenized_doc = add_upos_tags(input_data)
    print(doc2string(ud_tokenized_doc), file=sys.stdout)

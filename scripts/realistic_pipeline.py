
import argparse
from pathlib import Path

from common import doc2string
from tokens import Syntok
from pos import RNNTagger
from depparse import Spacy

tokenizer = Syntok()
tagger = RNNTagger()
parser = Spacy()

argparser = argparse.ArgumentParser()
argparser.add_argument("inputfiles", nargs="+", type=Path)
argparser.add_argument("-o", "--outpath", default="../data/tmp/", type=Path)
args = argparser.parse_args()

for fp in args.inputfiles:
    print(f"processing {fp} ...")
    rawtext = Path(fp).open(encoding="utf-8").read()
    # remove the BOM
    rawtext = rawtext.replace("\ufeff", "")

    tokenizer.process(rawtext)
    tokenizer.postprocess()

    tagger.process(tokenizer.data)
    tagger.postprocess()

    parser.process(doc2string(tagger.data))
    parser.postprocess()

    # the default postprocessing function omits the input POS,
    # since we ordinarily assume these to be gold POS and we don't
    # want those in our evaluation -- here we also want the 
    # input POS, so we recover it from the tagger
    for tagged_sent, parsed_sent in zip(tagger.data, parser.data):
        for tagged_tok, parsed_tok in zip(tagged_sent, parsed_sent):
            parsed_tok.lemma = tagged_tok.lemma
            parsed_tok.upos = tagged_tok.upos
            parsed_tok.xpos = tagged_tok.xpos
            parsed_tok.feats = tagged_tok.feats
    
    with open(args.outpath.joinpath(fp.stem + ".conll"), "w", encoding="utf-8") as outfile:
        print(doc2string(tagger.data), file=outfile)

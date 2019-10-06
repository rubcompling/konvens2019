#!/usr/bin/env python3

from depparse import StanfordNLP, CoreNLP
from common import main

class StanfordNLP_UD(StanfordNLP):
    pass

class CoreNLP_UD(CoreNLP):
    pass

if __name__ == "__main__":
    main("depparseud", [CoreNLP_UD, StanfordNLP_UD])

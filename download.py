#!/usr/bin/env python3

import nltk
import stanfordnlp
import spacy

nltk.download("punkt")
stanfordnlp.download("de", force=True)
spacy.download('de_core_news_md')

#!/usr/bin/env python3

import nltk
import stanfordnlp
from spacy.cli import download as spacy_download

nltk.download("punkt")
stanfordnlp.download("de", force=True)
spacy_download('de_core_news_md')

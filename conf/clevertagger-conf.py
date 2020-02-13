
from os import environ as env
# Path to compact SMOR model. You can download a pre-compiled SMOR model (with Zmorge lexicon) from http://kitt.ifi.uzh.ch/kitt/zmorge/
#SMOR_MODEL = '/data/tools/morphology/zmorge-20140120-smor_newlemma.ca'

# SMOR_MODEL = '/opt/zmorge/zmorge-20150315-smor_newlemma.ca'
SMOR_MODEL = env["SMOR_MODEL"]

# Morphisto uses UTF-8 encoding, SMOR with Stuttgart lexicon uses latin-1. Set accordingly.
# The clevertagger frontend always uses UTF-8 encoding for input/output, regardless of the encoding of the morphology tool.
SMOR_ENCODING = 'UTF-8'

# Path to fst-infl2-daemon (SFST >= 1.3)
SFST_BIN = 'fst-infl2-daemon'

# Used for fst-infl2-daemon (the socket server that provides the analyses).
PORT = 9010         # The default port; if busy, port will be incremented by 1 until available port is found

# Code for feature extraction with Gertwol is still included, but support is deprecated
GERTWOL_BIN = '/opt/bin/uis-gertwol'

# Two CRF tools are currently supported: CRF++ and Wapiti
# Options: 'crf++', 'wapiti'
CRF_BACKEND = 'wapiti'

# executable file of CRF tool (typically 'wapiti' for wapiti, and 'crf_test' for crf++.
# may be relative path to clevertagger directory
CRF_BACKEND_EXEC = 'wapiti'

# location of the trained model (see README for training instructions)
# CRF_MODEL = '/opt/wapiti/model-pos.de'
CRF_MODEL = env["WAPITI_MODEL"]

FROM ubuntu:19.10
MAINTAINER Adam Roussel (roussel@linguistics.rub.de)

RUN apt-get update && apt-get install -y \
    git wget unzip \
    python3-pip python3-dev build-essential \
    default-jdk default-jre \
    # dependency for clevertagger
    sfst \
    # for parzu
    swi-prolog

RUN useradd --create-home --shell /bin/bash tester
USER tester
WORKDIR /home/tester
ENV PATH $PATH:/home/tester/.local/bin
# make sure that tester can work in this dir
RUN mkdir tools

ENV TOOLS_HOME /home/tester/tools
COPY data data
COPY scripts scripts
COPY download.py download.sh $TOOLS_HOME/
RUN mkdir eval

# install tools that are on pypi
RUN pip3 install -U \
        syntok \
        # for clevertagger
        pexpect \
        SoMeWeTa==1.5.0 SoMaJo \
        iwnlp \
        nltk \
        stanfordnlp \
        # (NB: the `stanfordnlp` package also includes the interface to CoreNLP)
        germalemma PatternLite \
        spacy spacy-lookups-data \
        treetaggerwrapper \
        # required for running RFTagger
        JPype1

WORKDIR $TOOLS_HOME
# download models for nltk, stanfordnlp, and spacy
RUN python3 download.py
# download other systems/models
RUN bash download.sh

# configure model locations
ENV GERMALEMMA_HOME /home/tester/.local/lib/python3.7/site-packages/germalemma/
ENV GERMALEMMA_MODEL $GERMALEMMA_HOME/data/lemmata.pickle
ENV SOMEWETA_MODEL $TOOLS_HOME/SoMeWeTa/german_newspaper_2018-12-21.model
ENV IWNLP_MODEL $TOOLS_HOME/iwnlp/IWNLP.Lemmatizer_20181001.json
ENV SMOR_MODEL $TOOLS_HOME/zmorge-20150315-smor_newlemma.ca
ENV WAPITI_MODEL $TOOLS_HOME/wapiti-1.5.0/model-pos.de
ENV CLEVERTAGGER_HOME $TOOLS_HOME/clevertagger
ENV CORENLP_HOME $TOOLS_HOME/stanford-corenlp-full-2018-10-05
ENV RNNTAGGER_HOME $TOOLS_HOME/RNNTagger

# pickle-ize model for germalemma
COPY tiger_release_aug07.corrected.16012013.conll09 .
RUN python3 $GERMALEMMA_HOME/__init__.py tiger_release_aug07.corrected.16012013.conll09

# compile wapiti
USER root
WORKDIR $TOOLS_HOME/wapiti-1.5.0
RUN make && make install
USER tester
WORKDIR $TOOLS_HOME

# install clevertagger config
COPY conf/clevertagger-conf.py clevertagger/config.py

# unpack corrected rftagger lexicon
COPY rftagger-lexicon.tar.gz RFTagger/lib/
RUN tar xOzf rftagger-lexicon.tar.gz > RFTagger/lib/german-rft-tagger-lemma-lexicon-corrected.txt


WORKDIR /home/tester/scripts
ENTRYPOINT ["bash"]

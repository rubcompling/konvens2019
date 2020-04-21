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

# download nltk models
RUN python3 -m nltk.downloader punkt

# stanfordnlp model
RUN python3 -c "import stanfordnlp; stanfordnlp.download('de', force=True)"

# Spacy model
RUN python3 -m spacy download de_core_news_md

# download corpus for germalemma model
RUN mkdir $TOOLS_HOME/germalemma
WORKDIR $TOOLS_HOME/germalemma
RUN wget -qO - https://www.ims.uni-stuttgart.de/documents/ressourcen/korpora/TIGERCorpus/download/tigercorpus-2.2.conll09.tar.gz | tar xz
ENV GERMALEMMA_HOME /home/tester/.local/lib/python3.7/site-packages/germalemma/
RUN python3 $GERMALEMMA_HOME/__init__.py tiger_release_aug07.corrected.16012013.conll09
ENV GERMALEMMA_MODEL $GERMALEMMA_HOME/data/lemmata.pickle

# SoMeWeTa model
RUN mkdir $TOOLS_HOME/SoMeWeTa
WORKDIR $TOOLS_HOME/SoMeWeTa
RUN wget -q http://corpora.linguistik.uni-erlangen.de/someweta/german_newspaper_2018-12-21.model
ENV SOMEWETA_MODEL $TOOLS_HOME/SoMeWeTa/german_newspaper_2018-12-21.model

# model for iwnlp
RUN mkdir $TOOLS_HOME/iwnlp
WORKDIR $TOOLS_HOME/iwnlp
RUN wget -q http://lager.cs.uni-duesseldorf.de/NLP/IWNLP/IWNLP.Lemmatizer_20181001.zip
RUN unzip IWNLP.Lemmatizer_20181001.zip && rm IWNLP.Lemmatizer_20181001.zip
ENV IWNLP_MODEL $TOOLS_HOME/iwnlp/IWNLP.Lemmatizer_20181001.json

# install dependencies for clevertagger
WORKDIR $TOOLS_HOME
RUN wget -q https://pub.cl.uzh.ch/users/sennrich/zmorge/transducers/zmorge-20150315-smor_newlemma.ca.zip
RUN unzip zmorge-20150315-smor_newlemma.ca.zip
ENV SMOR_MODEL $TOOLS_HOME/zmorge-20150315-smor_newlemma.ca
RUN wget -qO - https://wapiti.limsi.fr/wapiti-1.5.0.tar.gz | tar xz
WORKDIR $TOOLS_HOME/wapiti-1.5.0
USER root
RUN make && make install
USER tester
RUN wget -qO - https://wapiti.limsi.fr/model-pos.de.gz | zcat > model-pos.de
ENV WAPITI_MODEL $TOOLS_HOME/wapiti-1.5.0/model-pos.de

# install clevertagger
WORKDIR $TOOLS_HOME
RUN git clone --depth 1 -q https://github.com/rsennrich/clevertagger
WORKDIR clevertagger/
COPY conf/clevertagger-conf.py config.py
RUN git checkout -q b45832ef1f89dcc5ad8fde9a1b19cdd847720ecc
ENV CLEVERTAGGER_HOME $TOOLS_HOME/clevertagger

# install corenlp
WORKDIR $TOOLS_HOME
RUN wget -q http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip
RUN unzip stanford-corenlp-full-2018-10-05.zip && rm stanford-corenlp-full-2018-10-05.zip
WORKDIR stanford-corenlp-full-2018-10-05
RUN wget -q http://nlp.stanford.edu/software/stanford-german-corenlp-2018-10-05-models.jar
ENV CORENLP_HOME $TOOLS_HOME/stanford-corenlp-full-2018-10-05

# treetaggerwrapper should find treetagger automatically
RUN mkdir $TOOLS_HOME/treetagger
WORKDIR $TOOLS_HOME/treetagger
RUN wget -qO - https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.2.tar.gz | tar xz
RUN wget -qO - https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz | tar xz
RUN wget -qO - https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/german.par.gz | zcat > lib/german.par

# RFTagger
RUN wget -qO - https://www.cis.uni-muenchen.de/~schmid/tools/RFTagger/data/RFTagger.tar.gz | tar xz
RUN mkdir $TOOLS_HOME/RFTagger
WORKDIR $TOOLS_HOME/RFTagger
ENV RFTAGGER_HOME $TOOLS_HOME/RFTagger
RUN mkdir lib
COPY rftagger-lexicon.tar.gz lib/
WORKDIR lib
RUN tar xOzf rftagger-lexicon.tar.gz > german-rft-tagger-lemma-lexicon-corrected.txt
RUN mkdir $RFTAGGER_HOME/jars
WORKDIR $RFTAGGER_HOME/jars
RUN wget -q https://repo1.maven.org/maven2/net/java/dev/jna/jna/4.5.1/jna-4.5.1.jar
RUN wget -q http://sifnos.sfs.uni-tuebingen.de/resource/A4/rftj/data/rft-java-beta13.jar

# ParZu install
WORKDIR $TOOLS_HOME
RUN git clone -q https://github.com/rsennrich/ParZu
WORKDIR ParZu
RUN bash install.sh

# RNNTagger
# RUN mkdir $TOOLS_HOME/RNNTagger
WORKDIR $TOOLS_HOME
RUN wget https://www.cis.uni-muenchen.de/~schmid/tools/RNNTagger/data/RNNTagger.zip
RUN unzip RNNTagger.zip && rm RNNTagger.zip
# WORKDIR $TOOLS_HOME/RNNTagger
ENV RNNTAGGER_HOME $TOOLS_HOME/RNNTagger

WORKDIR /home/tester/scripts
ENTRYPOINT ["bash"]

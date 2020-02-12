FROM ubuntu:19.10

RUN apt update && apt install -y \
    build-essential python3-dev python3-pip fish git wget \
    default-jdk default-jre \
    # dependency for clevertagger
    sfst \
    nltk
RUN apt update && apt install -y fish

RUN useradd --create-home --shell /usr/bin/fish tester
USER tester
WORKDIR /home/tester

ENV TOOLS_HOME /home/tester/tools
COPY data data
COPY scripts scripts
RUN mkdir eval && mkdir $TOOLS_HOME

WORKDIR $TOOLS_HOME

# install dependencies for clevertagger
RUN wget https://wapiti.limsi.fr/wapiti-1.5.0.tar.gz
RUN tar xfz wapiti-1.5.0.tar.gz
WORKDIR wapiti-1.5.0
RUN wget https://wapiti.limsi.fr/model-pos.de.gz
RUN gunzip model-pos.de.gz
ENV WAPITI_MODEL $TOOLS_HOME/wapiti-1.5.0/model-pos.de


# install clevertagger
WORKDIR $TOOLS_HOME
RUN git clone https://github.com/rsennrich/clevertagger
WORKDIR clevertagger/
RUN git checkout b45832ef1f89dcc5ad8fde9a1b19cdd847720ecc
ENV CLEVERTAGGER_HOME $TOOLS_HOME/clevertagger

# install corenlp
WORKDIR $TOOLS_HOME
RUN wget http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip
RUN unzip stanford-corenlp-full-2018-10-05.zip
WORKDIR stanford-corenlp-full-2018-10-05
RUN wget http://nlp.stanford.edu/software/stanford-german-corenlp-2018-10-05-models.jar
ENV CORENLP_HOME $TOOLS_HOME/stanford-corenlp-full-2018-10-05

# RFTagger
WORKDIR $TOOLS_HOME
RUN wget http://sifnos.sfs.uni-tuebingen.de/resource/A4/rftj/data/rft-java-beta13.jar
ENV RFTAGGER_HOME $TOOLS_HOME/RFTagger


# download nltk models
RUN python3 -m nltk.downloader punkt

# install tools that are on pypi
RUN pip3 install -U stanfordnlp \
                    syntok \
                    SoMeWeTa SoMaJo \
                    iwnlp \
                    germalemma PatternLite \
                    spacy spacy-lookups-data \
                    treetaggerwrapper \
                    # required for running RFTagger
                    jpype
# (NB: the `stanfordnlp` package also includes the interface to CoreNLP)

# download corpus for germalemma model
WORKDIR $TOOLS_HOME/germalemma
# TODO maybe just include the lemmata.pickle?
RUN wget https://www.ims.uni-stuttgart.de/documents/ressourcen/korpora/TIGERCorpus/download/tigercorpus-2.2.conll09.tar.gz
RUN tar xfz tigercorpus-2.2.conll09.tar.gz
RUN python3 germalemma.py tiger_release_aug07.corrected.16012013.conll09


# Spacy model
RUN python3 -m spacy download de_core_news_md

# SoMeWeTa model
RUN mkdir $TOOLS_HOME/SoMeWeTa
WORKDIR $TOOLS_HOME/SoMeWeTa
RUN wget http://corpora.linguistik.uni-erlangen.de/someweta/german_newspaper_2018-12-21.model
ENV SOMEWETA_MODEL $TOOLS_HOME/SoMeWeTa/german_newspaper_2018-12-21.model

# iwnlp needs this model
RUN mkdir $TOOLS_HOME/iwnlp 
WORKDIR $TOOLS_HOME/iwnlp
RUN wget http://lager.cs.uni-duesseldorf.de/NLP/IWNLP/IWNLP.Lemmatizer_20181001.zip
RUN unzip IWNLP.Lemmatizer_20181001.zip
ENV IWNLP_MODEL $TOOLS_HOME/iwnlp/IWNLP.Lemmatizer_20181001.json

WORKDIR /home/tester/scripts
ENTRYPOINT ["fish"]

MODEL_FILES := tigercorpus-2.2.conll09.tar.gz german_newspaper_2018-12-21.model
MODEL_FILES += IWNLP.Lemmatizer_20181001.json zmorge-20150315-smor_newlemma.ca
MODEL_FILES += model-pos.de

# download *most* stuff ahead of time
download:
	wget https://www.ims.uni-stuttgart.de/documents/ressourcen/korpora/TIGERCorpus/download/tigercorpus-3.2.conll09.tar.gz
	wget http://corpora.linguistik.uni-erlangen.de/someweta/german_newspaper_2018-12-21.model
    wget http://lager.cs.uni-duesseldorf.de/NLP/IWNLP/IWNLP.Lemmatizer_20181001.zip
    wget https://pub.cl.uzh.ch/users/sennrich/zmorge/transducers/zmorge-20150315-smor_newlemma.ca.zip
    wget https://wapiti.limsi.fr/wapiti-1.5.0.tar.gz
    wget https://wapiti.limsi.fr/model-pos.de.gz
    git clone --depth 1 -q https://github.com/rsennrich/clevertagger
    wget https://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip
    wget https://nlp.stanford.edu/software/stanford-german-corenlp-2018-10-05-models.jar
    wget https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.2.tar.gz
    wget https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz
    wget https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/german.par.gz


image: $(MODEL_FILES)
    sudo docker build -t konvens2019 .

run:
    sudo docker run -v tools/:/home/tester/tools/ konvens2019

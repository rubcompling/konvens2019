#!/bin/bash

# germalemma
echo "downloading tiger corpus for germalemma..."
wget -qO - https://www.ims.uni-stuttgart.de/documents/ressourcen/korpora/TIGERCorpus/download/tigercorpus-2.2.conll09.tar.gz | tar xz
# leave it here for pickleizer script

# SoMeWeTa
echo "downloading german_newspaper_2018-12-21.model for SoMeWeTa..."
wget -q http://corpora.linguistik.uni-erlangen.de/someweta/german_newspaper_2018-12-21.model
mkdir SoMeWeTa
mv german_newspaper_2018-12-21.model SoMeWeTa/

# iwnlp
wget -q http://lager.cs.uni-duesseldorf.de/NLP/IWNLP/IWNLP.Lemmatizer_20181001.zip
unzip -d iwnlp IWNLP.Lemmatizer_20181001.zip
rm IWNLP.Lemmatizer_20181001.zip

# clevertagger
wget -q https://pub.cl.uzh.ch/users/sennrich/zmorge/transducers/zmorge-20150315-smor_newlemma.ca.zip
unzip zmorge-20150315-smor_newlemma.ca.zip
wget -qO - https://wapiti.limsi.fr/wapiti-1.5.0.tar.gz | tar xz
wget -qO - https://wapiti.limsi.fr/model-pos.de.gz | zcat > wapiti-1.5.0/model-pos.de

wget -q https://github.com/rsennrich/clevertagger/archive/b45832ef1f89dcc5ad8fde9a1b19cdd847720ecc.zip
unzip -d clevertagger b45832ef1f89dcc5ad8fde9a1b19cdd847720ecc.zip
rm b45832ef1f89dcc5ad8fde9a1b19cdd847720ecc.zip

# corenlp
wget -q http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip
unzip stanford-corenlp-full-2018-10-05.zip
rm stanford-corenlp-full-2018-10-05.zip
wget -qO - http://nlp.stanford.edu/software/stanford-german-corenlp-2018-10-05-models.jar > stanford-corenlp-full-2018-10-05/stanford-german-corenlp-2018-10-05-models.jar

# treetagger
mkdir treetagger
wget -qO - https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.2.tar.gz | tar xz
wget -qO - https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz | tar xz
# TODO is this right? what comes out of these archives?
mv tree-tagger-linux-3.2.2 tagger-scripts treetagger/
wget -qO - https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/german.par.gz | zcat > treetagger/lib/german.par

# RFTagger
wget -qO - https://www.cis.uni-muenchen.de/~schmid/tools/RFTagger/data/RFTagger.tar.gz | tar xz
wget -q https://repo1.maven.org/maven2/net/java/dev/jna/jna/4.5.1/jna-4.5.1.jar
wget -q http://sifnos.sfs.uni-tuebingen.de/resource/A4/rftj/data/rft-java-beta13.jar
mv jna-4.5.1.jar rft-java-beta13.jar RFTagger/jars/

# ParZu
git clone -q --depth 1 https://github.com/rsennrich/ParZu
cd ParZu
bash install.sh
cd -
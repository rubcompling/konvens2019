TRIALS = 1 2 3 4 5
SYSOUTPUT = $(shell find ../data/system/ -type f -name '*.conll')
LEMMATIZERS = customlemmatizer germalemma iwnlp

all: tokens pos lemmas depparse
	@echo "all done"

tokens:
	$(foreach i, $(TRIALS), ./tokens.py ../data/gold/balanced/txt/;)

pos:
	$(foreach i, $(TRIALS), ./pos.py ../data/gold/balanced/tokens/;)

lemmas:
	$(foreach i, $(TRIALS), ./lemmas.py ../data/gold/balanced/annotations/;)

depparse:
	$(foreach i, $(TRIALS), ./depparse.py ../data/gold/balanced/annotations/;)

depparseud:
	$(foreach i, $(TRIALS), ./depparse_ud.py ../data/gold/balanced/ud-tokenized/;)

evaluate: $(SYSOUTPUT)
	# copy parser output to 'pos' folder so morph gets evaluated
	rm -rf ../data/system/parzu/pos
	mkdir ../data/system/parzu/pos
	cp ../data/system/parzu/depparse/* ../data/system/parzu/pos/

	# copy lemmatizer output to 'pos' for lemmatizers
	$(foreach name, $(LEMMATIZERS), rm -rf ../data/system/$(name)/pos;)
	$(foreach name, $(LEMMATIZERS), mkdir ../data/system/$(name)/pos;)
	$(foreach name, $(LEMMATIZERS), cp ../data/system/$(name)/lemmas/* ../data/system/$(name)/pos/;)

	# clean up old results
	-rm ../eval/results.csv

	python3 eval_bounds.py | python3 eval_annotations.py > ../eval/results.csv

analysis: ../eval/results.csv ../eval/timing.csv
	python3 analysis.py

clean:
	-rm ../eval/timing.csv
	-rm ../eval/results.csv

'''
Created on 24.06.2019

@author: Katrin Ortmann
'''

import os

###############################

def import_file(filename):
    """
    Input: Filename (including the path if necessary) of the file.
    Output: File object.
    """
    try:
        file = open(filename, mode="r", encoding="utf-8")
        return file
    except FileNotFoundError:
        print("ERROR: File not found.")
        return None
    except:
        print("ERROR")
        return None

##############################

def get_sentences(file):

    sentences = []
    sentence = []

    for line in file:
        if not line.strip() and sentence:
            sentences.append(sentence)
            sentence = []
        else:
            sentence.append(line.strip().split())

    return sentences

##############################

def merge(pos_filename, lemmas_filename, morph_filename, output):

    pos_file = import_file(pos_filename)
    lemma_file = import_file(lemmas_filename)
    morph_file = import_file(morph_filename)

    pos_sentences = get_sentences(pos_file)
    lemma_sentences = get_sentences(lemma_file)
    morph_sentences = get_sentences(morph_file)

    outfile = open(output, mode="w", encoding="utf-8")

    for pos_sent, lemma_sent, morph_sent in zip(pos_sentences, lemma_sentences, morph_sentences):

        for pos, lemma, morph in zip(pos_sent, lemma_sent, morph_sent):

            #Check consistency first
            if pos[1] != lemma[1] or pos[1] != morph[1] or lemma[1] != morph[1]:
                print("Token differs in", pos_filename, pos, ":", pos[1], lemma[1], morph[1])
                i = input()
            if pos[4] != lemma[4] or pos[4] != morph[4] or lemma[4] != morph[4]:
                print("POS differs in", pos_filename, pos, ":", pos[4], lemma[4], morph[4])
                i = input()

            print(pos[0], pos[1], lemma[2], "_", pos[4], morph[5], "_", "_", "_", "_", sep="\t", file=outfile)

        print(file=outfile)

    outfile.close()

##############################
##############################
if __name__ == '__main__':
    pos_folder = r"C:\Users\Katrin\Documents\Git\konvens2019\data\gold\pos"
    pos_files = [pos_folder + "/" + filename for filename in os.listdir(pos_folder)]
    lemma_folder = r"C:\Users\Katrin\Documents\Git\konvens2019\data\gold\lemmas"
    lemma_files = [lemma_folder + "/" + filename for filename in os.listdir(lemma_folder)]
    morph_folder = r"C:\Users\Katrin\Desktop\morph"
    morph_files = [morph_folder + "/" + filename for filename in os.listdir(morph_folder)]

    for pos, lemma, morph in zip(pos_files, lemma_files, morph_files):
        merge(pos, lemma, morph, \
              output = r"C:\Users\Katrin\Desktop\annotations"+ "/" + pos.split("/")[-1][:-10]+".conll")
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

def convert_conll2000_to_conllu(filename):

    file = import_file(filename)

    sentences = get_sentences(file)

    outfile = open(filename, mode="w", encoding="utf-8")

    for sentence in sentences:

        for t, token in enumerate(sentence):
            print(str(t+1), token[0], "_", "_", token[1], "_", "_", "_", "_", "_", sep="\t", file=outfile)
        print(file=outfile)

    outfile.close()

##############################
##############################
if __name__ == '__main__':
    convert_conll2000_to_conllu(r"C:\Users\Katrin\Desktop\wikipedia_pos.conll")
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

def token_stats(filenames, out="./text_stats.txt"):

    tokens = list()
    tokens_no_punct = list()
    lemmas = list()
    pos = dict()

    tokens_pos = dict()
    tokens_lemmas = dict()


    outfile = open(out, mode="w", encoding="utf-8")

    for filename in filenames:
        file = import_file(filename)

        sentences = get_sentences(file)

        for sentence in sentences:

            for token in sentence:
                
                tokens.append(token[1])
                if not token[4].startswith("$"): tokens_no_punct.append(token[1])
                lemmas.append(token[2])

                if token[1] in tokens_lemmas:
                    tokens_lemmas[token[1]].add(token[2])
                else:
                    tokens_lemmas[token[1]] = {token[2]}

                if not token[4] in pos:
                    pos[token[4]] = 1
                else:
                    pos[token[4]] += 1

                if token[1] in tokens_pos:
                    tokens_pos[token[1]].add(token[4])
                else:
                    tokens_pos[token[1]] = {token[4]}

    #Print for each text and overall
    #tokens
    print("Tokens:", len(tokens), file=outfile)
    #tokens without punctuation
    print("Tokens without punctuation:", len(tokens_no_punct), file=outfile)
    #types
    print("Types:", len(set(tokens)), file=outfile)
    #types without punctuation
    print("Types (without punctuation):", len(set(tokens_no_punct)), file=outfile)
    #types lowercased
    print("Types lowercased:", len(set([tok.lower() for tok in tokens])), file=outfile)
    #types lowercased without punctuation
    print("Types lowercased (without punctuation):", len(set([tok.lower() for tok in tokens_no_punct])), file=outfile)
    #lemmas
    print("Different lemmas:", len(set(lemmas)), file=outfile)
    #tokens with more than 1 lemma
    toks_mult_lemmas = [tok for tok,lems in tokens_lemmas.items() if len(lems) > 1]
    print("Tokens with more than one lemma:", len(toks_mult_lemmas), toks_mult_lemmas, file=outfile)
    #pos
    print("POS:", len(pos), file = outfile)
    #tokens with more than 1 pos
    toks_mult_pos = [tok for tok,pos in tokens_pos.items() if len(pos) > 1]
    print("Tokens with more than one POS:", len(toks_mult_pos), toks_mult_pos, file=outfile)
    #frequency of pos
    print("POS frequencies:", file=outfile)
    for p, freq in sorted(pos.items(), key=lambda l: l[1], reverse=True):
        print("", p, freq, sep="\t", file=outfile)
    
    #morphology annotations
    #tokens with different morph annotations

    
    outfile.close()

##############################
##############################
if __name__ == '__main__':
    token_stats([r"C:\Users\Katrin\Desktop\annotations\wikipedia.conll"], out=r"C:\Users\Katrin\Desktop\wiki_stats.txt")
    token_stats([r"C:\Users\Katrin\Desktop\annotations\ted.conll"], out=r"C:\Users\Katrin\Desktop\ted_stats.txt")
    token_stats([r"C:\Users\Katrin\Desktop\annotations\sermononline.conll"], out=r"C:\Users\Katrin\Desktop\sermon_stats.txt")
    token_stats([r"C:\Users\Katrin\Desktop\annotations\novelette.conll"], out=r"C:\Users\Katrin\Desktop\novelette_stats.txt")
    token_stats([r"C:\Users\Katrin\Desktop\annotations\opensubtitles.conll"], out=r"C:\Users\Katrin\Desktop\subtitle_stats.txt")    
    token_stats([r"C:\Users\Katrin\Desktop\annotations" + "/"+ p for p in ["wikipedia.conll", "ted.conll", "sermononline.conll", "novelette.conll", "opensubtitles.conll"]], \
                 out=r"C:\Users\Katrin\Desktop\overall_stats.txt")
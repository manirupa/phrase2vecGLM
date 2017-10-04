#!/usr/local/bin/python

import time
import operator
import sys, re, os
from textblob import *


def check():
    if (len(sys.argv)<2):
        print "usage: %s <input_source_data_file>" % sys.argv[0]
        exit()
    return

def write_to_file(str_to_print,filename):
    f = open(filename, 'ab')
    f.write(str_to_print)
    f.close()
    
def embed_phrases(line, phrase_list):
    phrase_words_list = [x.split("_") for x in phrase_list]
    finaltokens = []
    tokens = line.split()
    pc = 0
    i = 0
    n = len(tokens)
    npl = len(phrase_list)
    last_phrase_length = len(phrase_words_list[-1])
    print "length of document = %s " % n , " phrases = %s " % npl

    while pc < npl:
        #while i < n-last_phrase_length:
        while i < n-last_phrase_length+1:
            #matching 1st token of phrase
            #print 'tokens[%s] , phrase_words_list[%s][%s]' % (i,pc,0), tokens[i] , phrase_words_list[pc][0]
            if (str(tokens[i]) == str(phrase_words_list[pc][0])):
                #advance token counter by length of phrase
                print 'found match: ', tokens[i] , phrase_words_list[pc]
                finaltokens.append(phrase_list[pc])
                newi = i + len(phrase_words_list[pc])
                pc += 1
            else:
                finaltokens.append(tokens[i])
                newi = i + 1
            i = newi
            if (pc == npl):
                for i in range(newi,n):
                    finaltokens.append(tokens[i])
            #print 'i, newi, pc: ', i, newi, pc, finaltokens, line
            
    newpline = ' '.join(finaltokens)
    print "length of document = %s " % n , " phrases = %s " % npl
    return newpline

def do_this():
    check()
    input_file = sys.argv[1]
    output_file = input_file.replace('.txt', '_phrase-embedded.txt')
    just_phrases_file = input_file.replace('.txt', '_just-phrases.txt')
    logfile = output_file.replace('txt', 'log.txt')

    init_stdout = sys.stdout
    logfile = file(logfile,'w')
    sys.stdout = logfile
    tic = time.time()

    
    input_lines = open(input_file).readlines()
    
    for line in input_lines:
        temp = line.split("|")
        pmcid = temp[0]
        linetext = temp[1].strip()
        print temp, '\n', linetext, '\n', len(temp)
        if (len(linetext) > 0):
            blob = TextBlob(linetext)
            nplist = blob.noun_phrases
            if(len(nplist) > 0):
                print '\n\nnplist: ', nplist
                phrase_list = []
                for np in nplist:
                    phrase_terms = np.split()
                    ptl = len(phrase_terms)
                    #only include NPs with length between 2 and 3
                    if( ptl >= 2 and ptl <= 3): 
                        phrase = "_".join(phrase_terms)
                        phrase_list.append(phrase)
                print 'phrase_list: ', phrase_list, '\n', linetext
                if(len(phrase_list) > 0):
                    phrase_embedded_line = embed_phrases(linetext,phrase_list)
                    print phrase_embedded_line
                    write_to_file('%s|%s\n' % (pmcid,','.join(phrase_list)), just_phrases_file)
                    write_to_file('%s|%s\n' % (pmcid,phrase_embedded_line), output_file)
                else:
                    write_to_file('%s|%s\n' % (pmcid,','.join(linetext.split())), just_phrases_file)
                    write_to_file('%s|%s\n' % (pmcid,linetext), output_file)
                    
    toc = time.time()
    print "Total Time elapsed for phrase generation: ", toc - tic
    sys.stdout = init_stdout
    logfile.close()

do_this()






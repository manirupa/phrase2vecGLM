#!/usr/local/bin/python

import sys
import nltk
import string

from collections import Counter

def get_tokens(infile):
   tokens=[]
   lines = open(infile).readlines()
   for i in range(len(lines)):
       temp = lines[i].split(',')
       print 'line no', i
       tokens = tokens + temp[1].split()
   return tokens

def check():
    if (len(sys.argv)<3):
        print "usage: %s <input_text_file> <vocabfile> " % sys.argv[0]
        exit()
    return

check()
infile = sys.argv[1]
vocabfile = sys.argv[2]

doc_term_matrix = []
tokens = get_tokens(infile)
count = Counter(tokens)
print count.most_common(10)
print "counter obj:", count, "size of counter: ", len(count)

for c in count:
    print c, count[c]
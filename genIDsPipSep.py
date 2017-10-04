#!/usr/local/bin/python

"""
@author: Manirupa Das
Script to fine tune and generate final concept on a set of scored (ranked) documents 

Note: Assumes that the script documents_genscores_GLM.py has already been run prior.

"""
import time
import datetime
import operator
import sys, re, os
from textblob import *
from math import *
# gensim modules
from gensim import utils
from gensim.models.doc2vec import LabeledSentence
#from gensim.models import Doc2Vec
from gensim.models import *
from gensim.models.word2vec import Word2Vec
from nltk.corpus import stopwords

# numpy
import numpy as np

# random
from random import shuffle

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H-%M-%S')

#set of english stopwords
stop = stopwords.words('english')

def introspect(desc, list):
    print desc
    for i in range(len(list)):
        print 'Record %s: %s\n' % (i+1, list[i])
    print 'Length ', len(list)

def check():
    if (len(sys.argv)<3):
        print "usage: %s <RankedIDListFile_TopicID_TAB_PMCID> <outfile> " % sys.argv[0]
        exit()
    return

def write_to_file(str_to_print,filename):
    f = open(filename, 'ab')
    f.write(str_to_print)
    f.close()
    
def extract_concepts(query_docid,query,scores_list,model,ordered_vocab,doctermsfreqs):
    #print "scores_list: ", scores_list
    matching_doc_ids = [item[0] for item in scores_list]
    #print "matching_doc_ids: ", matching_doc_ids
    best_matches = {}
    stoplist = stop + query
    topterms = []
    for q in query:
        topsimscores = []
        for md in matching_doc_ids:
            #print "processing query term: %s for document: %s " % (q,md)
            doctermsinds = [int(item[0]) for item in doctermsfreqs[md]] #all the term indices in this matching doc
            docterms = [ordered_vocab[t_ind] for t_ind in doctermsinds]
            #add MAX similarity value of that query term with all terms in document to simscore list
            simslist = [(float(model.similarity(q,term)),term,md) for term in docterms if term not in stoplist]
            simslist.sort(key=operator.itemgetter(0), reverse=True)
            #print 'simslist', simslist
            highest = simslist[0]
            #print 'highest:' , highest
            hterm = highest[1] #just the term 
            try:
                if hterm not in topterms:          
                    topterms.append(hterm)
                    topsimscores.append(highest)
                else:
                    highest = simslist[1]
                    hterm = highest[1]
                    topterms.append(hterm)
                    topsimscores.append(highest)
            except:
                continue
        topsimscores.sort(key=operator.itemgetter(0), reverse=True)
        qmatch_highest = topsimscores[0] #[topsimscores[0],topsimscores[1]]
        best_matches[q] = qmatch_highest
    print query, best_matches
    return best_matches

def do_this():
    check()
    infile = sys.argv[1]
    outfile = sys.argv[2]
    idlist = {}
    for i in range(1,31):
        idlist[i] =[]
    
    lines = open(infile).readlines()
    for line in lines:
         rec = line.split()
         id = int(rec[0])
         pmcid = rec[1]
         idlist[id].append(pmcid)

    f = open(outfile,'wb')
     
    for k in idlist.keys():        
        idstr = "|".join(idlist[k])
        print idstr
        f.write('%s\t%s\n' %(k,idstr))
    
    f.close()
    
    return

do_this()


#eng.quit()

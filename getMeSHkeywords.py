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
    if (len(sys.argv)<4):
        print "usage: %s <Pipe-Separated_RankedIDListFile_TopicID_TAB_PMCID> <inputfile_PMCID_TAB_MeSHkeywords> <outfile> " % sys.argv[0]
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
    pipesepidfile = sys.argv[1]
    meshkwdfile = sys.argv[2]
    outfile = sys.argv[3]
    
        
    pipesepidlist = {}
    pipeseplines = open(pipesepidfile).readlines()
    for line in pipeseplines:
        rec = line.split()
        topic_id = int(rec[0])
        #get list of ids for topic
        pipesepidlist[topic_id] = [int(x) for x in rec[1].split("|")]
        print 'pipesepidlist[topic_id]', pipesepidlist[topic_id]
    
    meshkwds = {}
    meshlines = open(meshkwdfile).readlines()
    for line in meshlines[1:]:
         rec = line.split()
         pmcid = int(rec[0])
         try:
             mesh_keywords = rec[1]
             meshkwds[pmcid] = mesh_keywords
         except:
             meshkwds[pmcid] = ''
    print 'meshkwds', meshkwds.keys()[0:10], meshkwds.values()[0:10]
             
    #print 'meshkwds', meshkwds[3916001], meshkwds[2803851], meshkwds[3915995], meshkwds[4768661]
    
    f = open(outfile,'wb')
     
    for topic in pipesepidlist.keys():    
        idlist_for_topic = pipesepidlist[topic]
        print 'idlist_for_topic ', topic, idlist_for_topic
        keywords_for_idlist = []
        for id in idlist_for_topic:
            try:
                keywords_for_idlist.append(meshkwds[id])
            except:
                "Print %s not found " % id
        print 'keywords_for_idlist', keywords_for_idlist
        finalkwdstr = "|".join(keywords_for_idlist)
        test = "|".join([str(x) for x in pipesepidlist[topic]])
        print finalkwdstr, test
        f.write('%s\t%s\t%s\n' %(topic,test,finalkwdstr))
    
    f.close()
    
    return

do_this()


#eng.quit()

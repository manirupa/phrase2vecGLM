#!/usr/local/bin/python

import time
import operator
import sys, re, os
from textblob import *


def check():
    if (len(sys.argv)<4):
        print "usage: %s <input_docid_file (one id per line)> <model_topntfidf_file> <output_query_file>" % sys.argv[0]
        exit()
    return

def get_queries(docids, topnlines, query_file):
    queries = []
    for d in docids:
        #This is the query
        try:
            topnqws = [item[4] for item in topnlines[d]]
            query = topnqws#[0:4]
            entry = (d, query)
            queries.append(entry)
            write_to_file('%s\n' % str(entry), query_file)
        except: 
            print "Problem encountered with doc %s: " % d
    return queries

def write_to_file(str_to_print,filename):
    f = open(filename, 'ab')
    f.write(str_to_print)
    f.close()
    
def do_this():
    check()
    docidlistfile = sys.argv[1]
    topn_tfidfs_file = sys.argv[2]
    query_file = sys.argv[3]

    docids = [int(docid.strip()) for docid in open(docidlistfile).readlines()]
    
    topnfile = open(topn_tfidfs_file)
    
    topnlines = {}
    bad_doc_ids = []
    lines = open(topn_tfidfs_file).readlines()
    for line in lines:
        rec = eval(str(line))
        d = int(rec[0])
        tfterms = rec[1]
        if(len(tfterms) < 4): #Only 1 tfidf term, e.g.(2542398,[[84552, 7.3982, 7.3982, 38, 'ondansetron']])
            bad_doc_ids.append(d)
        else:
            topnlines[d] = tfterms
        
    print "check topnlines: ", topnlines.keys()[0:5], '\n' ,topnlines.values()[0:5]
    
    bad_doc_ids.sort()
    
    print "check bad docids: ", len(bad_doc_ids), bad_doc_ids[0:10]
    
    queries = get_queries(docids, topnlines, query_file)

do_this()
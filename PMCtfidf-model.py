#!/usr/local/bin/python

import nltk
import string
import time
import datetime
import operator
import sys, re, os
from math import *

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H-%M-%S')

from collections import Counter

collection_term_matrix = {}

def check():
    if (len(sys.argv)<6):
        print "usage: %s <prefix> (model folder) <input_text_file> <vocabfile> (full path to vocab.txt) <description_text (for unique run)> <topN>" % sys.argv[0]
        exit()
    return

# def get_tokens(infile):
#    tokens=[]
#    lines = open(infile).readlines()
#    for i in range(len(lines)):
#        temp = lines[i].split(',')
#        print 'line no', i
#        tokens = tokens + temp[1].split()
#    return tokens


def make_doc_term_entry(line,vocab,n):
    temp = line.split('|') #discard pmcid
    id = temp[0]
    tokens = temp[1].split() #get all the tokens in this document
    n = float(len(tokens))
    counts = Counter(tokens) #get their counts
    tc = []
    print tokens, counts
    for c in counts:
        index = vocab.index(c)
        raw_count = counts.get(c, 0)
        freq = round(float(raw_count)/n, 4)
        #print "freq ", freq 
        tc.append([index,raw_count,freq]) #add tuple for (index, count for token c, freq for token c) to tf entry
        #increment #-of-docs-found-in counter for the token
        collection_term_matrix[c][1] += 1
    return str((id, len(tokens), tc))

def make_doc_term_matrix(infile,vocab,ndims,output_folder,prefix,desc):
    doc_term_matrix = []
    f = open(infile)
    path = '%s/%s_%s_doc_term_counts_freqs.txt' % (output_folder, prefix, desc)
    i = 0
    for line in f:
        entry = '%s\n' % make_doc_term_entry(line,vocab,ndims)
        print entry
        if (i % (floor(log(ndims)) * 2) == 0):
            print "tf entry: %s" % i, entry
        write_to_file(str(entry),path)
        i += 1
    return path

def make_collection_term_matrix(doc_term_matrix_file,vocab,output_folder,prefix, desc):
    f = open(doc_term_matrix_file)
    doc_count = 0 
    for e in f:
        doc_count += 1
        entry = eval(e)[2] #3rd entry of tuple
        #print e
        #check for valid probability distribution
        check_prob = 0
        for j in range(len(entry)):
            #print entry[j]
            #update collection term counter
            collection_term_matrix[vocab[entry[j][0]]][0] += int(entry[j][1]) 
            check_prob += entry[j][2] 
        print "Document %s, tf probabilities: " % eval(e)[0], check_prob
    #By this time we have counts for number of docs each term occurs in, 
    #and the total number of docs
    print "Total number of documents: %s " % doc_count  
    #Now ready to calc idf for each term 
    calc_idf(vocab,doc_count)
    path = '%s/%s_%s_coll_terms_freqs.txt' % (output_folder, prefix, desc)
    write_to_file(str(collection_term_matrix),path)
    return path

def calc_idf(vocab,N):
    for vw in vocab:
        if (collection_term_matrix[vw][1] == 0):
            print vw, collection_term_matrix[vw][1]
            collection_term_matrix[vw][1] += 1
        scale = collection_term_matrix[vw][1]
        expr = round(log(N/scale),4)
        collection_term_matrix[vw][2] = expr
    return

def calc_tfidf(vocab,doc_term_matrix_file,tfidf_file):
    f = open(doc_term_matrix_file)
    for e in f:        
        line = eval(e)
        docid = line[0]
        tflist = line[2]
        tfidf_values = []
        for doc_term_entry in tflist:
            index = doc_term_entry[0]
            word = vocab[index] #entry[0] is the index into the vocab
            #tf-idf is product of tf (=doc_term_entry[2]) and idf (=collection_term_matrix[word][2])
            tfidf = doc_term_entry[2] * collection_term_matrix[word][2] 
            tfidf_values.append([index,tfidf,collection_term_matrix[word][2],collection_term_matrix[word][1]])
        tfidf_entry = (docid, tfidf_values)
        str_to_print = '%s\n' % str(tfidf_entry)
        write_to_file(str_to_print,tfidf_file)
    return
    
def write_to_file(str_to_print,filename):
    f = open(filename, 'ab')
    f.write(str_to_print)
    f.close()
    return
    
def top_tfidf(tfidf_file,vocab,topn):
    file = open(tfidf_file)
    outputfile = tfidf_file.replace('tfidf', 'topn_tfidf')
    for row in file:
        tfidfs = eval(row)
        docid = tfidfs[0]
        lists = tfidfs[1]
        lists.sort(key=operator.itemgetter(1), reverse=True)
        finaln = lists[0:topn]
        for i in range(len(finaln)):
            finaln[i].append(vocab[finaln[i][0]])            
        str_to_print = '(%s,%s)\n' % (docid,finaln)
        write_to_file(str_to_print,outputfile)
    return

def do_this():
    check()
    prefix = sys.argv[1] #give it model folder as prefix
    infile = sys.argv[2] #give it the text file produced by the word2vec model
    vocabfile = sys.argv[3] #give it full path to vocab.txt (1 word per line)   
    desc = sys.argv[4] #job desc - useful prefix
    topn = int(sys.argv[5]) #get a value for top tfidf terms to produce
    
    output_folder = 'models/%s' % prefix

    vocab = open(vocabfile).readlines()
    vocab = [x.strip() for x in vocab]
    vocab.append('unknown')

    vocab.sort() #sort the vocab list
    ndims = len(vocab)
    
    for i in range(len(vocab)):
        str_to_print = '(%s,%s)\n' % (vocab[i],i)
        write_to_file(str_to_print, '%s/indexed_vocab.txt' % output_folder)
 
    #populate collection term matrix for cf, # of docs counts for terms for idf calc, idf    
    for vw in vocab:
        collection_term_matrix[vw] = [0,0,0]
 
    orig_stdout = sys.stdout
    logfile = file('%s/%s_%s_tfidf_log.txt' % (output_folder,prefix,desc), 'w')
    sys.stdout = logfile
 
    print "Arguments: ", sys.argv
    print "Vocab snapshot:", vocab[0:10]
    print "Vocab size: ", ndims
     
    doc_term_matrix_file = make_doc_term_matrix(infile,vocab,ndims,output_folder,prefix,desc)
    coll_term_matrix_file = make_collection_term_matrix(doc_term_matrix_file,vocab,output_folder,prefix,desc)
    print "Document term raw counts & frequencies are in: %s " % doc_term_matrix_file
    print "Collection term frequencies and IDFs are in: %s " % coll_term_matrix_file
     
    tfidf_file = '%s/%s_%s_tfidf.txt' % (output_folder,prefix,desc)
    calc_tfidf(vocab,doc_term_matrix_file,tfidf_file)
    print "TF-IDF values of terms per document are in: %s " % tfidf_file
         
    keyfile = '%s/%s_coll_key.txt' % (output_folder,desc)
    for i in range(ndims):
        str_to_print = 'word %s = %s, count: %s\n' % (i, vocab[i], collection_term_matrix[vocab[i]])
        write_to_file(str_to_print,keyfile)
 
    top_tfidf(tfidf_file,vocab,topn)

    sys.stdout = orig_stdout
    logfile.close()
    
do_this()


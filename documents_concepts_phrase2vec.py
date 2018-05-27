#!/usr/local/bin/python

"""
@author: Manirupa Das
Script to perform concept discovery on a set of documents in the corpus using only the learnt Phrase2Vec model 
prior to generation of the GLM 

These are chosen as terms for query expansion, which are essentially the discovered concepts for the original query doc.

"""
import time
import datetime
import operator
import sys, re, os
#from textblob import *
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

#set of english stopwords
stop = stopwords.words('english')

# random
from random import shuffle

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H-%M-%S')


def introspect(desc, list):
    print desc
    for i in range(len(list)):
        print 'Record %s: %s\n' % (i+1, list[i])
    print 'Length ', len(list)

def check():
    if (len(sys.argv)<6):
        print "usage: %s <prefix> (just model folder name) <phrvecmodel+sim_run_prefix> <query_file> <query_length (upto 5 for F/B), ~25 for direct> <unique run description>" % sys.argv[0]
        exit()
    return

def write_to_file(str_to_print,filename):
    f = open(filename, 'ab')
    f.write(str_to_print)
    f.close()
        
def write_model(model,modelname,suffix):
    filename = '%s_%s' % (modelname,suffix)
    vocab = list(model.vocab.keys())
    n = len(vocab)
    print "n = %s" % n
    for i in range(n):
        print "i=%s, word=%s" %(i, vocab[i])
        wordvec = model[vocab[i]]
        str_to_print = '%s, %s\n' % (vocab[i],wordvec.tolist())
        write_to_file(str_to_print,filename)
    return

def do_this():
    check()
    folder_prefix = sys.argv[1] #Give it a model folder as prefix
    run_prefix = sys.argv[2] #Same job desc that was used to run tfidf and sigma
    query_file = sys.argv[3]
    query_length = int(sys.argv[4])
    run_desc = sys.argv[5]
    #Make folder and file names
    model_folder = 'models/%s' % folder_prefix
    #Model folder should already exist from word2vec run, so no need to create it
    modelfile = '%s/%s.bin.model.txt' % (model_folder,folder_prefix)
    vocabfile = '%s/indexed_vocab.txt' % model_folder
    collection_sigmas_file =  '%s/%s_%s_collection_sigmas.txt' % (model_folder,folder_prefix,run_prefix)
    document_sigmas_file = '%s/%s_%s_document_sigmas.txt' % (model_folder,folder_prefix,run_prefix)
    collection_freqs_file =  '%s/%s_%s_coll_terms_freqs.txt' % (model_folder,folder_prefix,run_prefix)
    document_freqs_file = '%s/%s_%s_doc_term_counts_freqs.txt' % (model_folder,folder_prefix,run_prefix)
    tfidfs_file = '%s/%s_%s_tfidf.txt' % (model_folder,folder_prefix,run_prefix)
    topn_tfidfs_file = '%s/%s_%s_topn_tfidf.txt' % (model_folder,folder_prefix,run_prefix)
    
    output_folder = model_folder 

    concept_file = '%s/phrase2vec_concepts_%s_%s_%s.txt' % (model_folder,run_desc,folder_prefix,run_prefix)

    logfilename = concept_file.replace('txt','log.txt')

    #create log file
    orig_stdout = sys.stdout
    logfile = file('%s' % logfilename, 'w')
    sys.stdout = logfile 
    
    print 'sys.argv: ', sys.argv
    print 'run_prefix: ', run_prefix
    print 'model_folder: ', model_folder
    print 'modelfile: ', modelfile
    print 'vocabfile: ', vocabfile
    #print 'collection_sigmas_file: ', collection_sigmas_file
    #print 'document_sigmas_file: ', document_sigmas_file
    #print 'collection_freqs_file: ', collection_freqs_file
    #print 'document_freqs_file: ', document_freqs_file
    #print 'tfidfs_file: ', tfidfs_file
    #print 'topn_tfidfs_file: ', topn_tfidfs_file
    #print 'param_file: ', param_file
    print 'output_folder: ', output_folder
    print 'logfilename: ', logfilename
    #print 'docidlistfile: ', docidlistfile
    print 'concept_file: ', concept_file
    print 'query_file: ', query_file
    print 'query_length: ', query_length
    
    tic_start = time.time()

    #Load word2vec model
    model = Word2Vec.load(modelfile) 
    
    #Test neighborhood similarities for a single term
    print 'child', model.most_similar(positive=['child'], topn=3)

    phrase2vec_concepts_by_query = []

    queries = []
    querieslines = open(query_file).readlines()
    for q in querieslines:
        queries.append(eval(q))

    concepts_str = ''
    for j in range(len(queries)):   #range(10):
        tic = time.time()
        query = queries[j][1][0:query_length]
        query_docid = queries[j][0]
        
        best_matches = []
        for qt in query:
            print "query term: %s, most similar: %s" % (qt,model.most_similar(positive=[qt], topn=3))
            best_matches.append(model.most_similar(positive=[qt], topn=1)[0][0]) #first list element, #first tuple element
        concept_tuple = (query_docid,query,best_matches)
        discovered_concepts = best_matches
        print "Top discovered concepts for document %s by phrase2vec, query - %s :\n" % (query_docid,query), discovered_concepts, concept_tuple
        
        toc = time.time()
        te = toc - tic 
        print "Time elapsed for phrase2vec discovered concepts for this document: %s sec" % te 
        phrase2vec_concepts_by_query.append(concept_tuple)
        concepts_str += '%s\n' % str(concept_tuple)

    write_to_file('%s\n' % concepts_str, concept_file)
        
    te = toc - tic_start
    print "\nTotal time elapsed for performing concept discovery on all documents: %s sec" % te
    phrase2vec_concepts_by_query_file = concept_file.replace('concepts','concepts_by_query_list')
    write_to_file(str(phrase2vec_concepts_by_query), phrase2vec_concepts_by_query_file)
    
    sys.stdout = orig_stdout
    logfile.close()

do_this()
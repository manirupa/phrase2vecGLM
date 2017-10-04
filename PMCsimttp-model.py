#!/usr/local/bin/python

"""
@author: Manirupa Das
This script calculates the sigma terms for each term in vocabulary, by document and Collection,
using the word2vec model, for use in eqns 3,4,5,6
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

# numpy
import numpy as np

# random
from random import shuffle

# classifier
from sklearn.linear_model import LogisticRegression

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H-%M-%S')


def introspect(desc, list):
    print desc
    for i in range(len(list)):
        print 'Record %s: %s\n' % (i+1, list[i])
    print 'Length ', len(list)

def check():
    if (len(sys.argv)<3):
        print "usage: %s <prefix> (just model folder name) <documents_file_full_path> <description_text (for unique run)>" % sys.argv[0]
        exit()
    return

def write_to_file(str_to_print,filename):
    f = open(filename, 'ab')
    f.write(str_to_print)
    f.close()
    
def format_vec(id, vec):
    ftdvec = id[0]
    for v in vec:
        ftdvec = '%s,%s' % (ftdvec,v)
    return ftdvec
    
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
    prefix = sys.argv[1]
    documentfile = sys.argv[2]
    desc = sys.argv[3]
    model_folder = 'models/%s' % prefix
    #model folder should already exist from word2vec run, so no need to create it
    modelfile = '%s/%s.bin.model.txt' % (model_folder,prefix)
    #documentfile = '%s/%s.txt' % (model_folder,prefix)
    vocabfile = '%s/indexed_vocab.txt' % model_folder
    
    '''
    RESC02NW2PMG3QP:model_w2v_vs50_cw4_xyz_10abstracts_tab mxd074$ cut -d, -f 1 model_w2v_vs50_cw4_xyz_10abstracts_tab.vectors.txt > vocab.txt
    RESC02NW2PMG3QP:model_w2v_vs50_cw4_xyz_10abstracts_tab mxd074$ wc -l vocab.txt model_w2v_vs50_cw4_xyz_10abstracts_tab.vectors.txt 
     924 vocab.txt
     924 model_w2v_vs50_cw4_xyz_10abstracts_tab.vectors.txt
    '''
    output_folder = 'models/%s' % prefix 
    output_file = '%s/%s_%s_simttp.txt' % (output_folder, prefix, desc)
    logfilename = output_file.replace('txt','log.txt')
    
    #create log file
    orig_stdout = sys.stdout
    logfile = file(logfilename, 'w')
    sys.stdout = logfile 
    
    print 'sys.argv:', sys.argv
    print 'prefix:', prefix
    print 'model_folder:', model_folder
    print 'modelfile:', modelfile
    print 'output_folder:', output_folder
    print 'output_file:', output_file
    print 'documentfile:', documentfile
    print 'vocabfile:', vocabfile
    print 'logfilename:', logfilename
 
    vocab = open(vocabfile).readlines()
    vocab = [x.strip() for x in vocab]
   
    mapped_vocab = {}
     
    for ind in range(len(vocab)):
         tupl = vocab[ind].lstrip('(').rstrip(')').split(',')
         print tupl
         mapped_vocab[tupl[0]] = int(tupl[1])
        
    mapped_vocab_file = '%s/mapped_vocab.txt' % model_folder
 
    write_to_file(str(mapped_vocab), mapped_vocab_file)
    
    #Load word2vec model
    model = Word2Vec.load(modelfile) 
    
    #Test neighborhood similarities for a single term
    print model.most_similar(positive=['lack', 'focus'], negative=['learn'])
    print 'focus', model.most_similar(positive=['focus'], topn=3)
    print "vector for focus: ", model['focus']
    print 'random vector', model.seeded_vector('focus')
    unk_vec = model.seeded_vector('focus')
    print 'vector for UNK', unk_vec
    
    tic = time.time()
    #Get neighborhood similarities for each term in vocabulary, 
    #This is useful for collection sampling probs, store in file
    collection_sigma_file = '%s/%s_%s_collection_sigmas.txt' % (model_folder,prefix,desc)
    
    collection_sigma = {}
    for v in sorted(mapped_vocab.keys()):
        print v, mapped_vocab[v]
        if v != 'unknown':
            try:
                most_sim_list = model.most_similar(positive=[v], topn=3)
            except:
                most_sim_list = model.most_similar(positive=[unk_vec], topn=3)
        else:
            most_sim_list = model.most_similar(positive=[unk_vec], topn=3)
        sim_sum = 0
        sim_list = []
        for m in most_sim_list:
            sim_list.append(m[0])
            sim_sum += m[1]
        collection_sigma[v] = (sim_sum, sim_list)
    write_to_file(str(collection_sigma), collection_sigma_file)
    
    #Get a square upper-triangular matrix of term-term' similarities - store this in a file
    #Entries of the form {vocab_index0:{vocab_index0: sim_val, vocab_index1: sim_val, ....}}
    #                    {vocab_index1:{vocab_index1: sim_val, vocab_index2: sim_val, ....}}
    #OR THIS MAY NOT EVEN BE NEEDED -- ACTUALLY, HOLD OFF FOR NOW, JUST QUERY MODEL INSTEAD
    
    #Now load document file to process t,tp similarities for documents and Sigma(Nt) for corpus 
    docfile = open(documentfile)
    
    #Get document-wise term transformation probabilities, use random vector for unknown term 
    #Get entries of the form (docid, [(word_vocab_index_t1, denom-Sigma(sim(t1,t'')), (...), .....]
    #Can get denom-Sigma(sim(t1,t'')) by summing appropriate values in above upper-triangular matrix, 
    #or directly querying the model.
    #From above can get probabilities by querying the model prob( similarities for each term in vocabulary, 
    document_denom_file = '%s/%s_%s_document_sigmas.txt' % (model_folder,prefix,desc)
    
    for doc in docfile:
        splitvars = doc.split('|')
        docid = splitvars[0]
        try:
            temp = splitvars[1]
        except:
            temp = "A problem occurred"
        dwlist = temp.split()
        print docid, dwlist[0:10], len(dwlist)
        denoms_tuple_list = []
        for qt in dwlist:
            vocab_ind = mapped_vocab[qt]
            denom_qt = 0
            for term in dwlist:
                denom_qt += model.similarity(qt,term)
            denoms_tuple_list.append((vocab_ind, denom_qt))
        doc_entry = (docid, denoms_tuple_list)
        write_to_file('%s\n' % str(doc_entry),document_denom_file)


    toc = time.time()
    te = toc - tic 
    print "Time elapsed for processing denoms: ", te 

    sys.stdout = orig_stdout
    logfile.close()
    
    return

do_this()

#eng.quit()

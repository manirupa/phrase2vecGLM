#!/usr/local/bin/python

"""
@author: Manirupa Das
This script normalizes data, and given experimental settings, performs 
word2vec training on sets of documents

TO-DO: Additionally find the top-K, word similarities
for this training
"""
import time
import operator
import sys, re, os
from textblob import *
import datetime
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

#matlab integration
#import matlab.engine
#eng = matlab.engine.start_matlab()

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H-%M-%S')

ENT_RE = re.compile(r'[;,.\"\!\?\(\)\{\}\\\[\]]')
NUM_RE = re.compile(r'[0-9]')

def remove_entities(text):
    text = text.lower() #already lower-casing
    return ENT_RE.sub('', text)

def clean_data(pmcid, text, desc):
    text = text.lower()
    finaltokens = []
    #first chunk by space
    chunks = text.split()
    #split by period
    for c in chunks:
        byperiod = c.split('.')
        for m in byperiod:
            finaltokens.append(m)               
    #split by comma
    chunks = finaltokens
    finaltokens = []    
    for c in chunks:
        bycomma = c.split(',')
        for m in bycomma:
            finaltokens.append(m)                  
    #split by colon
    chunks = finaltokens
    finaltokens = []
    for c in chunks:
        bycolon = c.split(':')
        for m in bycolon:
            finaltokens.append(m)                  
    #split by semi-colon    
    chunks = finaltokens
    finaltokens = []
    for c in chunks:
        bysemi = c.split(';')
        for m in bysemi:
            finaltokens.append(m)     
    #split by frontslash    
    chunks = finaltokens
    finaltokens = []
    for c in chunks:
        byfs = c.split('/')
        for m in byfs:
            finaltokens.append(m)     
    for i in range(len(finaltokens)):
        finaltokens[i] = ENT_RE.sub('', finaltokens[i])     
        #finaltokens[i] = NUM_RE.sub('2',finaltokens[i])      
    print "Num tokens:", len(finaltokens), finaltokens[0:10]
    str_to_print = '%s,%s\n' % (pmcid, ' '.join(finaltokens))
    filename = '%s_%s.txt' %(desc,st)
    write_to_file(str_to_print, filename)
    return finaltokens

def introspect(desc, list):
    print desc
    for i in range(len(list)):
        print 'Record %s: %s\n' % (i+1, list[i])
    print 'Length ', len(list)

def check():
    if (len(sys.argv)<4):
        print "usage: %s <input_text_file> <experimental_setting_`list format`_file> <description_text>" % sys.argv[0]
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

def process_data(lines, desc):
    data = []
    documents = []
    
    for i in range(len(lines)):
        temp = lines[i].split('\t')
        #print temp
        try:
            pmcid = temp[0].strip()
        except:
            pmcid = 't999999'
            print i, 'pmcid', pmcid
        try:
            text = temp[1].strip()
        except:
            text = 'Text999999'
            print 'text: ', text[0:5]
        data.append((pmcid, text))
        #text = text.lower()
        #words = text.split()
        #for i in range(len(words)):
        #    wordtext = words[i]
        #    words[i] = remove_entities(wordtext)
        words = clean_data(pmcid, text, desc)
        documents.append(words)
    return [data,documents]

def do_this():
    check()
    infile = sys.argv[1]
    exps_list = eval(open(sys.argv[2]).read())
    run_desc = sys.argv[3]
    lines = open(infile).readlines()
    processed_data = process_data(lines, run_desc)
    documents = processed_data[1]
    
    introspect("processed data[0:10]", processed_data[0][0:10])
    introspect("documents[0:10]", documents[0:10])


    #Train different models, by setting up different experimental settings here
    #exps_list = [{'size': 30, 'cw':2},{'size': 50, 'cw':2},{'size': 200, 'cw':2}]
    #exps_list = [{'min_count': 2,'size': 50, 'window':4}]

    #Run deep learning training for each experimental setting
    for setting in exps_list:
        min_count = int(setting['min_count'])
        size = int(setting['size'])
        window = int(setting['window'])
        orig_stdout = sys.stdout
        suffix = (os.path.basename(infile))
        model_folder = 'model_w2v_vs%s_cw%s_%s_%s' % (size,window,run_desc,suffix.replace('.txt',''))
        os.system('mkdir %s' % model_folder)
        #create log file
        f = file('%s/model_w2v_vs%s_cw%s_%s_%s.log.txt' % (model_folder,size,window,run_desc,suffix.replace('.txt','')), 'w')
        sys.stdout = f
        print "Model params: min_count - %s, vector size - %s, window - %s, corpus - %s" % (min_count,size,window,suffix)
        print "sys.argv: " , sys.argv 
        print "length data: ", len(processed_data), " length docs:", len(documents)
        print "length data[0]: ", len(processed_data[0]), " length data[1]:", len(processed_data[1])
        
        tic = time.time()
        #train the model over all genes for this experiment setting
        #model = doc2vec.Doc2Vec(documents, min_count = 1, window = window, size = size, workers=20, \
        #                            dm_concat = 1 , dbow_words = 1) 
        model = Word2Vec(documents, min_count=min_count, size=size, window=window)
        model.init_sims(replace=True)
        toc = time.time()
        te = toc - tic 
        
        #create vector representation files
        modelfile = '%s/%s' % (model_folder,'model_w2v_vs%s_cw%s' % (size,window))
        print "\nModel file for settings (%s): %s" % (setting,modelfile)
        write_model(model,modelfile,'%s_%s' % (run_desc,suffix))
        
        vocab = list(model.vocab.keys())
        n = len(vocab)
        str_to_print = vocab
        vocabfilename = '%s_%s_%s.vocab.txt' % (modelfile,run_desc,suffix.replace('.txt',''))
        write_to_file(repr(str_to_print),vocabfilename)
        write_to_file('\nVocab size: %s\n' %n ,vocabfilename)

        #test model
        print model['yellow']
        print list(model.vocab.keys())[0:10]
        print documents[0][1], documents[1][10]
        model.similarity(documents[0][1], documents[1][10])

        print "Time elapsed for training model: ", te 
        sys.stdout = orig_stdout
        f.close()

    return

do_this()

#eng.quit()

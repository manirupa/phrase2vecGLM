#!/usr/local/bin/python

"""
@author: Manirupa Das
This script normalizes data, and given experimental settings, performs 
word2vec training on sets of documents
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
from nltk.stem import WordNetLemmatizer

lemmatizer = WordNetLemmatizer()

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

ENT_RE = re.compile(r'[\^\#\*\"\'\(\)\{\}\[\]]')

ENT_RE = re.compile(r'[\,\:\;\!\?\|\+\&\@\_\~\^\#\*\"\'\(\)\{\}\[\]]')

NUM_RE = re.compile(r'[0-9]')

DECIMAL_RE = re.compile(r"([0-9]+\.[0-9]+)") #Catch Decimals

stop = ['and', 'the', 'of', 'for', 'from', 'at', 'by', 'as', 'is',\
        'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',\
        'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', \
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', \
        'how', 'all', 'any', 'both', 'each']

def remove_entities(text):
    text = text.lower() #already lower-casing
    return ENT_RE.sub('', text)

def clean_data(pmcid, text, filename):
    text = text.lower()
    text = DECIMAL_RE.sub(' decimal-value ', text) #decimal number processing
    text = text.replace('.', ' . ') #process any remaining periods as tokens
    text = text.rstrip('.') #remove any trailing periods for end of sentence
    #text = text.replace(',', ' , ')
    #text = text.replace(',', '  ') # causes troubles otherwise
    #text = text.replace(':', ' : ')
    #text = text.replace(';', ' ; ')
    #text = text.replace('!', ' ! ')
    #text = text.replace('?', ' ? ')
    #text = text.replace('-', ' - ')
    #text = text.replace('+', ' + ')
    text = text.replace('%', ' % ')
    text = text.replace('$', ' $ ')
    #text = text.replace('&', ' & ')
    text = text.replace('>', ' > ')
    text = text.replace('<', ' < ')
    text = text.replace('=', ' = ')
    #text = text.replace('@', ' @ ')
    #text = text.replace('_', ' _ ')
    #text = text.replace('~', ' ~ ')
    text = text.replace('/', ' / ')
    text = text.replace('\\', ' \\ ')

    finaltokens = []
    #first chunk by space
    tokens = text.split()
    finaltokens = []
    
    for i in range(len(tokens)):
        if(tokens[i] not in stop):
            tokens[i] = ENT_RE.sub('', tokens[i])     
            #finaltokens[i] = NUM_RE.sub('2',finaltokens[i]) #keep numbers as-is otherwise molecule names messed up
            #tokens[i] = DECIMAL_RE.sub('decimal_value', tokens[i])
            token = tokens[i].rstrip('.') #remove trailing periods after decimal processing
            token = token.lstrip('.') #remove beginning periods after decimal processing
            token = token.lstrip('-') #remove beginning hyphen after decimal processing
#             try:
#                 tokens[i] = str((lemmatizer.lemmatize(token)).decode('utf-8'))
#             except:
#                 try:
#                     tokens[i] = str(token.decode('utf-8'))
#                 except:
#                     tokens[i] = "failed-token"
            try:
                tokens[i] = str(token.decode('utf-8'))
            except:
                tokens[i] = "failed-token"

            finaltokens.append(tokens[i])
    
    print "PMCID: ", pmcid, "Num tokens:", len(finaltokens), finaltokens[0:10]
    
    try:
        str_to_print = '%s|%s\n' % (pmcid, ' '.join(finaltokens)) #pipe-sep instead of comma-sep
    except:
        str_to_print = '%s|%s\n' % (pmcid, ' '.join([str(token) for token in finaltokens]))
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
        #temp = lines[i].split('\t')
        temp = lines[i].split('|')
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
        filename = '%s_%s.txt' %(desc,st)
        words = clean_data(pmcid, text, filename)
        documents.append(words)
    return [data,documents]

def do_this():
    check()
    infile = sys.argv[1]
    exps_list = eval(open(sys.argv[2]).read())
    run_desc = sys.argv[3]
    lines = open(infile).readlines()
    init_stdout = sys.stdout
    logfile = file('models/logs/%s_%s_log.txt' % (run_desc,st),'w')
    sys.stdout = logfile
    tic1 = time.time()
    processed_data = process_data(lines, run_desc)
    toc1 = time.time()
    print "Time elapsed for processing data: ", toc1 - tic1
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
        workers = int(setting['workers'])
        sg = int(setting['sg'])
        negatives = int(setting['negative'])
        orig_stdout = sys.stdout
        suffix = (os.path.basename(infile))
        model_folder = 'models/model_w2v_vs%s_cw%s_%s_%s' % (size,window,run_desc,suffix.replace('.txt',''))
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
        if(sg==0): #for CBOW, set cbow_mean parameter
             model = Word2Vec(documents, min_count=min_count, size=size, window=window, \
                              cbow_mean=1, workers=workers, sg=sg, negative=negatives)
             
        model = Word2Vec(documents, min_count=min_count, size=size, window=window, \
                         workers=workers, sg=sg, negative=negatives)
        model.init_sims(replace=True)
        toc = time.time()
        te = toc - tic 
        
        #create vector representation files
        modelfile = '%s/%s' % (model_folder,'model_w2v_vs%s_cw%s' % (size,window))
        print "\nModel file for settings (%s): %s" % (setting,modelfile)
        write_model(model,modelfile,'%s_%s' % (run_desc,suffix.replace('txt','vectors.txt')))
        
        #Save model
        model.save('%s_%s_%s.model.txt' % (modelfile,run_desc,suffix.replace('txt','bin')))
        
        vocab = list(model.vocab.keys())
        #print model.vocab
        vocab.sort()
        n = len(vocab)
        str_to_print = vocab
        vocabfilename = '%s_%s_%s.vocab_as_list.txt' % (modelfile,run_desc,suffix.replace('.txt',''))
        write_to_file(repr(str_to_print),vocabfilename)
        write_to_file('\nVocab size: %s\n' %n ,vocabfilename)
        
        #Make indexed_vocab file
        for i in range(len(vocab)):
            str_to_print = '(%s,%s)\n' % (vocab[i],i)
            write_to_file(str_to_print, '%s/indexed_vocab_w2v.txt' % model_folder)
        
        finaldocs_oldfilename = '%s_%s.txt' %(run_desc,st)
        finaldocs_newfilename = '%s/%s_%s.txt' %(model_folder,run_desc,st)
        
        #Add processed input file to model folder
        os.system('cp %s %s' % (finaldocs_oldfilename,finaldocs_newfilename))
        #Add original input file to model folder
        os.system('cp %s %s/%s' % (infile,model_folder,os.path.basename(infile)))

        #test model
        testword = vocab[0]
        print testword, model[testword]
        print list(model.vocab.keys())[0:10]
        print 'vocab words: ', vocab[10], vocab[20]
        model.similarity(vocab[10], vocab[20])

        #write out the vocab into vocab.txt
        tempfilename = '%s_%s_%s.model.txt' % (modelfile,run_desc,suffix.replace('txt','bin'))
        vectors_file = tempfilename.replace('bin.model', 'vectors')                             
        os.system('cut -d, -f 1 %s/%s > %s/vocab.txt' % (model_folder,vectors_file,model_folder) )
        
        print "Time elapsed for training model: ", te 
        sys.stdout = orig_stdout
        f.close()
        
    os.system('rm %s' % finaldocs_oldfilename) #Remove the processed input file
    print "Total Time elapsed for training: ", toc - tic1
    sys.stdout = init_stdout
    logfile.close()

    return

do_this()

#eng.quit()

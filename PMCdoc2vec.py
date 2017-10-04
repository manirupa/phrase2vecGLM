#!/usr/local/bin/python

"""
@author: Manirupa Das
This script normalizes data, and given experimental settings, performs 
doc2vec training on sets of GenRIFs across dataset of genes (between-gene)

Additionally find the top-K, within-gene and across-gene similarities
for this type of training
"""
import time
import operator
import sys, re, os
from textblob import *

# gensim modules
from gensim import utils
from gensim.models.doc2vec import LabeledSentence
#from gensim.models import Doc2Vec
from gensim.models import *

# numpy
import numpy

# random
from random import shuffle

# classifier
from sklearn.linear_model import LogisticRegression

# matlab integration
#import matlab.engine
#eng = matlab.engine.start_matlab()

ENT_RE = re.compile(r'[,;.(){}]')

def remove_entities(text):
    text = text.lower() #already lower-casing
    return ENT_RE.sub('', text)

def introspect(desc, list):
    print desc
    for i in range(len(list)):
        print 'Record %s: %s\n' % (i+1, list[i])
    print 'Length ', len(list)

def check():
    if (len(sys.argv)<3):
        print "usage: %s <input_text_file> <experimental_setting_`list format`_file>" % sys.argv[0]
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
    
def write_model(model,modelname,suffix,tags):
    filename = '%s_%s' % (modelname,suffix)
    n = len(tags)
    print "n = %s" % n
    for i in range(n):
        print "tags[all][%s]" % i, tags[i]
        docvec = model.docvecs[i]
        str_to_print = '%s\n' % format_vec(tags[i],docvec)
        write_to_file(str_to_print,filename)
    return

def process_data(lines, origlines):
    data = []
    documents = []
    #also makes sets by geneid
    sets = {}
    tags = {}
    descs = {}
    #uniqtext = []
    
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
        text = remove_entities(text)
        record = '%s %s' % (pmcid,text)
        
        #check for dupes, if not dupe then add
        #data already de-duped so skip
        if (record):
            #uniqtext.append(record)
            origrecord = origlines[i]
            #print record[0:8], origrecord[:-8]
            label = '%s' % (pmcid)
            thewords = text.split()
            data.append([thewords,[label]])
            lbldsent = LabeledSentence(words=thewords, tags=[label])
            id = pmcid.strip()
            try:
               (sets['all']).append(lbldsent)            
            except:
                print "yoohoo"
                sets['all'] = []
                (sets['all']).append(lbldsent)    
            try:
                (tags['all']).append([pmcid])
            except:
                print "yoohoo"
                tags['all'] = []
                (tags['all']).append([pmcid])
            try:
                temp = origrecord.strip().split('\t')
                desc = 'PMCID - %s, Content - %s' % (label, text)
                (descs[id]).append(desc)
            except:
                descs[id] = []
                temp = origrecord.strip().split('\t')
                desc = 'PMID - %s, Content - %s' % (label, text)
                (descs[id]).append(desc)
            documents.append(lbldsent)
        else:
            pass
    #introspect('uniqtext:', uniqtext[:-10])
    return [data,documents,sets,tags,descs]


def do_this():
    check()
    infile = sys.argv[1]
    #origfile=re.sub(r'\d+-gram.','',infile)
    #ids = eval(open(sys.argv[2]).read())
    #print geneids
    exps_list = eval(open(sys.argv[2]).read())
    lines = open(infile).readlines()
    origlines = open(infile).readlines()
    processed_data = process_data(lines, origlines)
    documents = processed_data[1]
    sets = processed_data[2] #sets of RIFS for each gene
    tags = processed_data[3] #set of corresponding tags
    descs = processed_data[4]
    
    introspect("processed data[0:10]", processed_data[0][0:10])
    introspect("documents[0:10]", documents[0:10])
    print("sets", [sets['all'][x] for x in range(10)])
    print("tags", [tags['all'][x] for x in range(10)])
    
    print("descs 10", [descs[x] for x in descs.keys()[0:10]])
    print("Various Lengths:", len(sets['all']), len(descs.keys()), len(tags['all']))

    #Train different models, by setting up different experimental settings here
    #exps_list = [{'size': 30, 'cw':2},{'size': 50, 'cw':2},{'size': 200, 'cw':2}]
    exps_list = [{'size': 500, 'cw':5}]
    #Run deep learning training for each experimental setting
    for setting in exps_list:
        size = int(setting['size'])
        window = int(setting['cw'])
        orig_stdout = sys.stdout
        suffix = (os.path.basename(infile))
        model_folder = 'model_all_vs%s_cw%s_%s' % (size,window,suffix.replace('.txt',''))
        os.system('mkdir %s' % model_folder)
        #create log file
        f = file('%s/model_all_vs%s_cw%s_%s.log.txt' % (model_folder,size,window,suffix.replace('.txt','')), 'w')
        sys.stdout = f
        print "Model params: vector size - %s, window - %s, corpus - %s" % (size,window,suffix)
        print "length data: ", len(processed_data), " length docs:", len(documents)
        print "length data[0]: ", len(processed_data[0]), " length data[1]:", len(processed_data[1])
        
        tic = time.time()
        #train the model over all genes for this experiment setting
        model = doc2vec.Doc2Vec(documents, min_count = 1, window = window, size = size, workers=20, \
                                    dm_concat = 1 , dbow_words = 1) 
        toc = time.time()
        te = toc - tic 
        
        #create vector representation files
        modelfile = '%s/%s' % (model_folder,'model_all_vs%s_cw%s' % (size,window))
        print "\nModel file for settings (%s): %s" % (setting,modelfile)
        write_model(model,modelfile,suffix,tags['all'])
            
#             #NOW GET WITHIN-GENE SIMILARITIES FROM THIS MODEL FILE
#             modelfile = '%s_%s' % (modelfile,suffix)            
#             lines = open(modelfile).readlines() #Get vector reps for this gene
#             query_idx = len(tagset) - 1
#             print "Query GeneRIF index - %s" % query_idx
#             query_tag = tags[g][query_idx][0]
#             record = descs[g][query_idx]
#             print "Query GeneRIF: %s \n" % record

#             K = 10
#             ret = eng.cosine(modelfile,query_idx,K) #Get top-K results
#             indices = []
#             distances = []
#             #Now just get records from the indices
#             for i in ret:
#                 rec = i.split("=")
#                 indices.append(int(rec[0]))
#                 distances.append(float(rec[1].strip()))
#             print "Indices", indices[0:K]
#             print "Distances", distances[0:K]
            
#             topk_indices = indices[0:K]
#             print "\nMost similar RIFs (WITHIN-GENE) to query RIF - (%s, %s):\n" % (query_tag, record)
#             for i in range(K):
#                 print "(Distance: %s, Record: %s)" % (distances[i], descs[g][topk_indices[i]])

        print "Time elapsed for training model: ", te 
        sys.stdout = orig_stdout
        f.close()

    return

do_this()

#eng.quit()

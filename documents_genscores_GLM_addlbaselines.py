#!/usr/local/bin/python

"""
@author: Manirupa Das
Script to perform concept discovery on a set of documents in the corpus

Each document to be concept-tagged is treated as a query into the word-embedding based GLM, 
query = top 4 (variable k) tfidf terms for that document.

Using this GLM, the query is used to score all the documents and obtain a ranking
of the top k docs related to the query. 2 schemes are employed to obtain the top matching concepts:
1) The top 1 nearest word-embedding to each of the query terms picked from the top K ranked set of 
   relevant docs for query doc
2) The top 1 or 2 tfidf terms associated with each of the top K ranked set of relevant docs for query doc

These are chosen as terms for query expansion, which are essentially the discovered concept for the original query doc.

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
    if (len(sys.argv)<8):
        print "usage: %s <prefix> (just model folder name) <phrvecmodel+sim_run_prefix> <run_description (LM)> <LM parameters file e.g. 3ql> <doc id list file (one per line) [obsolete]> <query_file> <query_length (upto 5)>" % sys.argv[0]
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

def make_unk_vec(mapped_vocab,model,N,model_folder):
    #make average vector - representative for UNK
    key0 = mapped_vocab.keys()[0]
    unk_vec = model[key0]
    print '%s, starting unk vec:' % key0, unk_vec
    for vw in mapped_vocab.keys()[1:100]: 
        unk_vec = unk_vec + model[vw]
    print 'ending unk vec', unk_vec
    unk_vec = unk_vec/N
    print 'final averaged vector for UNK', unk_vec
    write_to_file(str(unk_vec), '%s/unk_vec.txt' % model_folder)    
    return unk_vec

def lookupcs(collfreqs,qt,Ndocs):
    val = 0
    if int(collfreqs[qt][0]) == 0:
        val = float(0.1/float(Ndocs))
    else:
        #print 'all good', collfreqs[qt][0]
        val = float(float(collfreqs[qt][0])/float(Ndocs))
    return val

def lookuptf(doc_keys,qtind):
    val = 0.1/len(doc_keys) #tf value to return if term not found
    for i in range(len(doc_keys)):
        if qtind == doc_keys[i][0]: #if vocab word found
            val = doc_keys[i][2] #return the tf value
            break
    return val

def lookupttpC(model,reqdvals,collfreqsval,qt,Ndocs):
    sigma = reqdvals[0]
    neighbortokens = reqdvals[1]
    PttpC = 0
    for n in neighbortokens:
        try:
            PttpC += round(log(model.similarity(qt,n)/sigma * collfreqsval) , 10)
        except:
            PttpC += round(log(float(collfreqsval)/float(Ndocs)) , 10)
    return PttpC

def lookupttpd(model,doc_keys,docsigma,ordered_vocab,qtind):
    docid = docsigma[0]
    indices = [int(item[0]) for item in docsigma[1]]
    sigmas = [float(item[1]) for item in docsigma[1]]
    Pttpd = 0
    for i in range(len(indices)):
        index = indices[i]
        tf = lookuptf(doc_keys,qtind)
        try:
            Pttpd += round(log((model.similarity(ordered_vocab[qtind],ordered_vocab[index]))/sigmas[i] * tf) , 10)
        except:
            Pttpd += round(log(1/1000),10)
    return Pttpd

def do_this():
    check()
    folder_prefix = sys.argv[1] #Give it a model folder as prefix
    run_prefix = sys.argv[2] #Same job desc that was used to run tfidf and sigma
    lm_run_prefix = sys.argv[3]
    param_file = sys.argv[4] #Parameters: Lambda, Alpha, Beta, Gamma
    docidlistfile = sys.argv[5]
    query_file = sys.argv[6]
    query_length = int(sys.argv[7])
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
    #Name param file like - paramsL0.1A0.4B0.3G0.1.txt
    param_file_prefix = os.path.basename(param_file).replace('.txt','')
    output_LM_file = '%s/%s_%s_%s_%s_LM.txt' % (output_folder, folder_prefix, run_prefix, lm_run_prefix, param_file_prefix)
    logfilename = output_LM_file.replace('txt','log.txt')
    doclistprefix = os.path.basename(docidlistfile).replace('.txt','')
    concept_file = '%s'  % tfidfs_file.replace('tfidf','_%s_concepts_%s_%s_%s' % (lm_run_prefix,param_file_prefix,doclistprefix,st))
    
    #create log file
    orig_stdout = sys.stdout
    logfile = file(logfilename, 'w')
    sys.stdout = logfile 
    
    print 'sys.argv: ', sys.argv
    print 'run_prefix: ', run_prefix
    print 'lm_run_prefix: ', lm_run_prefix
    print 'model_folder: ', model_folder
    print 'modelfile: ', modelfile
    print 'vocabfile: ', vocabfile
    print 'collection_sigmas_file: ', collection_sigmas_file
    print 'document_sigmas_file: ', document_sigmas_file
    print 'collection_freqs_file: ', collection_freqs_file
    print 'document_freqs_file: ', document_freqs_file
    print 'tfidfs_file: ', tfidfs_file
    print 'topn_tfidfs_file: ', topn_tfidfs_file
    print 'param_file: ', param_file
    print 'output_folder: ', output_folder
    print 'output_LM_file: ', output_LM_file
    print 'logfilename: ', logfilename
    print 'docidlistfile: ', docidlistfile
    print 'concept_file: ', concept_file
    print 'query_file: ', query_file
    print 'query_length: ', query_length

    doctermsfreqsfile = open(document_freqs_file)
    docsigmafile = open(document_sigmas_file)    
    collsigmas = eval(open(collection_sigmas_file).read())
    collfreqs = eval(open(collection_freqs_file).read())
    
    vocab = open(vocabfile).readlines()
    vocab = [x.strip() for x in vocab]
    N = len(vocab)
   
    mapped_vocab = {}
    ordered_vocab = []
     
    for ind in range(N):
         tupl = vocab[ind].lstrip('(').rstrip(')').split(',')
         #print tupl
         mapped_vocab[tupl[0]] = int(tupl[1])
         ordered_vocab.append(tupl[0])
        
    mapped_vocab_file = '%s/lm_%s_mapped_vocab.txt' % (model_folder,run_prefix)
 
    write_to_file(str(mapped_vocab), mapped_vocab_file)
    
    #print 'ordered vocab: ', ordered_vocab
     
    #Load word2vec model
    model = Word2Vec.load(modelfile) 
    
    #Test neighborhood similarities for a single term
    print 'child', model.most_similar(positive=['child'], topn=3)
    print "vector for child: ", model['child']
    print 'random vector', model.seeded_vector('child')
    print 'similarity', model.similarity('child', 'adult')
    
    tic = time.time()
    
    #unk_vec = make_unk_vec(mapped_vocab,model,N,model_folder)
    
    toc = time.time()
    te = toc - tic 
    print "Time elapsed for processing vector for unknown: ", te 
    tic = toc
    
    params = eval(open(param_file).read())
    print 'params:', params
    lmbda = params['lambda']
    alpha = params['alpha']
    beta = params['beta']
    gamma = params['gamma']
    print 'lambda:', lmbda, ' alpha: ', alpha, ' beta: ', beta, ' gamma:', gamma
    
    topnfile = open(topn_tfidfs_file)
    
    topnlines = {}
    bad_doc_ids = []
    lines = open(topn_tfidfs_file).readlines()
    for line in lines:
        rec = eval(line)
        d = int(rec[0])
        tfterms = rec[1]
        if(len(tfterms) < 4): #Only 1 tfidf term, e.g.(2542398,[[84552, 7.3982, 7.3982, 38, 'ondansetron']])
            bad_doc_ids.append(d)
        else:
            topnlines[d] = tfterms
        
    print "check topnlines: ", topnlines.keys()[0:5], '\n' ,topnlines.values()[0:5]
    
    bad_doc_ids.sort()
    
    print "check bad docids: ", len(bad_doc_ids), bad_doc_ids[0:10]
    
    docids = [int(docid.strip()) for docid in open(docidlistfile).readlines()]

    print "check docids: ", docids[0:10]
    
    queries = []
    querieslines = open(query_file).readlines()
    for q in querieslines:
        queries.append(eval(q))
    
    Ndocs = len(topnlines.keys())
    print 'check queries: ', queries[0:10], 'Ndocs: ', Ndocs
        
    doctermsfreqs = {} #load full set of doc terms freqs into dict
    doctermsfreqslines = doctermsfreqsfile.readlines()
    for line in doctermsfreqslines:
        rec = eval(line)
        d = int(rec[0])
        docterms = rec[2]
        #discard documents of less than full no of tfids - leads to bad concepts
        if ((len(docterms) >= 30) and (d not in bad_doc_ids)):
           doctermsfreqs[d] = rec

    print 'check doctermsfreqs: ', len(doctermsfreqs.keys())
    for k in doctermsfreqs.keys()[0:5]:
        print k,doctermsfreqs[k]

    docsigmas = {} #load final set of doc sigmas into dict - bad_doc_ids + terms < 10
    dkeys = sorted(doctermsfreqs.keys())
    docsigmaslines = docsigmafile.readlines()
    for line in docsigmaslines:
        rec = eval(line)
        d = int(rec[0])
        sigmas = rec[1]
        if(d in dkeys): #only add good docs
            docsigmas[d] = sigmas
            
    print 'check docsigmas: '
    for k in docsigmas.keys()[0:5]:
        print k,docsigmas[k]

    query = queries[0][1]
    docid = docids[0]
    
    print 'check one query: ', query, 'docid: ', docid

    #First do for 1 document, then create loop around it
    
    #Loop through all documents, obtain tuple (docid, score) which will be reverse ordered
    rndlogLmbda = round(log(lmbda),10)
    rndlogCconst = round(log((1-lmbda-alpha-beta)),10)
    rndlogAlpha = round(log(alpha),10)
    rndlogBeta = round(log(beta),10)

    #new doctermsfreqs
    newdoctermsfreqsfile = open(document_freqs_file)
    
    newdoctermsfreqs = {} #load full set of doc terms freqs into dict
    newdoctermsfreqslines = newdoctermsfreqsfile.readlines()
    for line in newdoctermsfreqslines:
        rec = eval(line)
        d = int(rec[0])
        newdocterms = rec[2]
        newdoctermsfreqs[d] = newdocterms
    
    tic_start = time.time()
    documents_concepts = []
    concepts_str = ''
    for j in range(len(queries)):   #range(10):
        query = queries[j][1][0:query_length]
        query_docid = queries[j][0]
        document_scores = []
        c = 5000
        #calc WE-based GLM first for 1 document, then over all docs
        for d in doctermsfreqs.keys(): #docs:
            #print "IN HERE"
            doc = doctermsfreqs[d]
            #print '\n\nc=', c , query, "\n\ndoc: ", doc
            thisdocid = int(doc[0])
            #print 'thisdocid: ', thisdocid, 'doclength: ', doc[1]
            docsigma = docsigmas[thisdocid]
            #print 'docsigma: ' , docsigma
            score = 0
            for qt in query:
                 qtind = mapped_vocab[qt]
                 doc_keys = doc[2][0:130] #take upto 1st 100 words
                 #print qt, qtind, doc_keys
                 tfpart = rndlogLmbda + round(log(lookuptf(doc_keys,qtind)),10)
                 collfreqsval = lookupcs(collfreqs,qt,Ndocs)
                 cspart =  rndlogCconst + round(log(collfreqsval),10)
                 try:
                     ttpdpart =  rndlogAlpha + lookupttpd(model,doc_keys,docsigma,ordered_vocab,qtind)
                 except:
                     ttpdpart = rndlogAlpha - 8
                 reqdvals = collsigmas[ordered_vocab[qtind]]
                 qt = ordered_vocab[qtind]
                 ttpCpart = rndlogBeta + lookupttpC(model,reqdvals,collfreqsval,qt,Ndocs)
                 expr = (tfpart + cspart + ttpdpart + ttpCpart)
                 #print 'tfpart, cspart, ttpdpart, ttpCpart, expr', tfpart, cspart, ttpdpart, ttpCpart, expr
                 score = score + expr
            score = score * -1
            #print '\n\nc= ', c , ', (docid: %s, score: %s)' % (thisdocid,score)
            document_scores.append((thisdocid,score))
            c = c - 1
            if (c < 0):
                break
       
        document_scores.sort(key=operator.itemgetter(1))
        matching_docs = document_scores[0:5]
        print "\n\n\nTop matching documents for document: %s" % query_docid , matching_docs 
    
        toc = time.time()
        te = toc - tic 
        print "Time elapsed for processing LM and top document matches: %s sec" % te 
        
        tic = toc
        
        best_matches = word2vec_concepts(query_docid,query,matching_docs,model,ordered_vocab,newdoctermsfreqs)
        word2vec_disc_concepts = [item[1] for item in best_matches.values()]
        tfidf_disc_concepts = tfidf_concepts(matching_docs,topnlines)
        concept_tuple = (query_docid,query,word2vec_disc_concepts,tfidf_disc_concepts,matching_docs,best_matches)
        discovered_concepts = [word2vec_disc_concepts, tfidf_disc_concepts]
        print "Top discovered concepts for document %s, query - %s :\n" % (query_docid,query), discovered_concepts
        
        toc = time.time()
        te = toc - tic 
        print "Time elapsed for concept discovery for this document: %s sec" % te 
        te = toc - tic_start
        documents_concepts.append(concept_tuple)
        concepts_str += '%s\n' % str(concept_tuple)
        
    write_to_file('%s\n' % concepts_str, concept_file)
        
    print "\nTotal time elapsed for performing concept discovery on all documents: %s sec" % te
    doc_concepts = concept_file.replace('concepts','document_concepts_list')
    write_to_file(str(documents_concepts), doc_concepts)
    
    sys.stdout = orig_stdout
    logfile.close()
    
    return

def phrase2vec_concepts(query_docid,query,scores_list,model,ordered_vocab,newdoctermsfreqs):
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
            doctermsrec = newdoctermsfreqs[md]#[2]
            doctermsinds = [int(item[0]) for item in doctermsrec] #all the term indices in this matching doc
            docterms = [ordered_vocab[t_ind] for t_ind in doctermsinds]
            #add MAX similarity value of that query term with all terms in document to simscore list
            simslist = [(float(model.similarity(q,term)),term,md) for term in docterms if term not in stoplist]
            simslist.sort(key=operator.itemgetter(0), reverse=True)
            #print 'simslist', simslist
            highest = simslist[0]
            #print 'highest:' , highest
            hterm = highest[1] #just the term 
            if hterm not in topterms: #if block to avoid duplicates
                topterms.append(hterm)
                topsimscores.append(highest)
            else:
                try:
                    highest = simslist[1]
                    hterm = highest[1]
                    topterms.append(hterm)
                    topsimscores.append(highest)
                except:
                    topterms.append(hterm)
                    topsimscores.append(highest)
        topsimscores.sort(key=operator.itemgetter(0), reverse=True)
        qmatch_highest = topsimscores[0] #[topsimscores[0],topsimscores[1]]
        best_matches[q] = qmatch_highest
    print query, best_matches
    return best_matches

def word2vec_concepts(query_docid,query,scores_list,model,ordered_vocab,newdoctermsfreqs):
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
            doctermsrec = newdoctermsfreqs[md]#[2]
            doctermsinds = [int(item[0]) for item in doctermsrec] #all the term indices in this matching doc
            docterms = [ordered_vocab[t_ind] for t_ind in doctermsinds]
            #add MAX similarity value of that query term with all terms in document to simscore list
            simslist = [(float(model.similarity(q,term)),term,md) for term in docterms if term not in stoplist]
            simslist.sort(key=operator.itemgetter(0), reverse=True)
            #print 'simslist', simslist
            highest = simslist[0]
            #print 'highest:' , highest
            hterm = highest[1] #just the term 
            if hterm not in topterms: #if block to avoid duplicates
                topterms.append(hterm)
                topsimscores.append(highest)
            else:
                try:
                    highest = simslist[1]
                    hterm = highest[1]
                    topterms.append(hterm)
                    topsimscores.append(highest)
                except:
                    topterms.append(hterm)
                    topsimscores.append(highest)
        topsimscores.sort(key=operator.itemgetter(0), reverse=True)
        qmatch_highest = topsimscores[0] #[topsimscores[0],topsimscores[1]]
        best_matches[q] = qmatch_highest
    print query, best_matches
    return best_matches

def tfidf_concepts(matching_docs,topnlines):
    matching_doc_ids = [item[0] for item in matching_docs]
    #print "matching_doc_ids: ", matching_doc_ids
    discovered_concepts = []
    for md in matching_doc_ids:
        key = int(md)
        concept_list =[item[4] for item in topnlines[key]]
        print 'doc: ', md, 'concept list: ', concept_list
        if len(concept_list) >= 2:
            for concept in concept_list[0:2]:
                discovered_concepts.append(concept)
        else:
            for concept in concept_list:
                discovered_concepts.append(concept)
    return discovered_concepts

do_this()

#eng.quit()

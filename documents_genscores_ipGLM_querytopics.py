#!/usr/local/bin/python

"""
@author: Manirupa Das
Script to perform concept discovery on a set of documents in the corpus

Each document to be concept-tagged is treated as a query into the word-embedding based GLM, 
query = top 4 (variable k) tfidf terms for that document.

This script implements an interpolated unified GLM employing unigram and phrasal GLM models

Using this unified-GLM, the query is used to score all the documents and obtain a ranking
of the top k docs related to the query. 2 schemes are employed to obtain the top matching concepts:
1) The top 1 nearest word-embedding to each of the query terms picked from the top K ranked set of 
   relevant docs for query doc corresponding to the phrasal query
2) The top 1 or 2 tfidf terms associated with each of the top K ranked set of relevant docs for phrasal 
   query doc

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
    if (len(sys.argv)<2):
        #print "usage: %s <prefix> (just model folder name) <previous_run_prefix> <run_description (LM)> <LM parameters file e.g. 3ql> <doc id list file (one per line) [obsolete]> <query_file> <query_length (upto 5)>" % sys.argv[0]
        print "usage: %s <model_settings_file>" % sys.argv[0]
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

def word2vec_concepts(query_docid,query,scores_list,model,ordered_vocab,newdoctermsfreqs):
    #print "scores_list: ", scores_list
    matching_doc_ids = [int(item[0]) for item in scores_list]
    #print "matching_doc_ids: ", matching_doc_ids
    best_matches = {}
    stoplist = stop + query
    topterms = []
    for q in query:
        topsimscores = []
        for md in matching_doc_ids:
            #print "processing query term: %s for document: %s " % (q,md)
            try:
                doctermsrec = newdoctermsfreqs[md][2] #only the terms-freqs list from tuple    
                #print 'DOCTERMSREC', doctermsrec
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
            except KeyError:
                print 'KeyError ', md
                pass
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

def do_GLM(lmdocid, rndlogLmbda, rndlogCconst, rndlogAlpha, rndlogBeta, \
           model, query, mapped_vocab, ordered_vocab, docsigma, doc_keys, \
           collfreqs, collsigmas, Ndocs):

    #print 'check query: ', query, 'lm docid: ', lmdocid

    score = 0
    for qt in query:
         qtind = mapped_vocab[qt]
         #print qt, qtind, doc_keys
         tfpart = rndlogLmbda + round(log(lookuptf(doc_keys,qtind)),10)
         collfreqsval = lookupcs(collfreqs,qt,Ndocs)
         cspart =  rndlogCconst + round(log(collfreqsval),10)
         try:
             ttpdpart = rndlogAlpha + lookupttpd(model,doc_keys,docsigma,ordered_vocab,qtind)
         except:
             ttpdpart = rndlogAlpha - 8
         reqdvals = collsigmas[ordered_vocab[qtind]]
         qt = ordered_vocab[qtind]
         ttpCpart = rndlogBeta + lookupttpC(model,reqdvals,collfreqsval,qt,Ndocs)
         expr = (tfpart + cspart + ttpdpart + ttpCpart)
         #print 'tfpart, cspart, ttpdpart, ttpCpart, expr', tfpart, cspart, ttpdpart, ttpCpart, expr
         score =  score + expr 
    score = score * -1
    
    return score

def do_this():
    check()
    model_settings = eval(open(sys.argv[1]).read())
    model_settings_prefix = os.path.basename(sys.argv[1]).replace('.txt','')
    unigram_settings = model_settings['unigram']
    phrasal_settings = model_settings['phrasal']
    unigram_query_file = model_settings['unigram']['query_file']
    phrasal_query_file = model_settings['phrasal']['query_file']
    docidlistfile = model_settings['docids_common_file']
    query_length = model_settings['query_length']
    gamma = model_settings['gamma']
    
    ##################################################################

    #Output folder and logs for unified model      

    ##################################################################
    #use phrasal one for final output
    output_folder = 'models/%s' % phrasal_settings['model_folder_prefix'] 
    output_LM_file = '%s/interpolated_%s_%s_G%s_%s_LM.txt' % \
                    (output_folder, phrasal_settings['orig_run_prefix'], \
                     phrasal_settings['LM_run_desc'], gamma, os.path.basename(sys.argv[1]).replace('.txt',''))
    logfilename = output_LM_file.replace('txt','log.txt')
    concept_file = '%s'  % output_LM_file.replace('LM','concepts' )
     
    #create log file
    orig_stdout = sys.stdout
    logfile = file(logfilename, 'w')
    sys.stdout = logfile 
          
    print 'sys.argv: ', sys.argv
    print 'model_settings: ', model_settings
    print 'unigram_settings: ', unigram_settings
    print 'phrasal_settings: ', phrasal_settings
    print 'output_folder: ', output_folder
    print 'output_LM_file: ', output_LM_file
    print 'logfilename: ', logfilename
    print 'concept_file: ', concept_file
    print 'unigram_query_file: ', unigram_query_file
    print 'phrasal_query_file: ', phrasal_query_file
    print 'docidlistfile: ', docidlistfile
    print 'query_length: ', query_length
    print 'gamma: ', gamma

    
    ##################################################################

    #Initialize Args and Files for Unigram Model
    
    ##################################################################

    uni_folder_prefix = unigram_settings['model_folder_prefix'] #Give it a model folder as prefix
    uni_run_prefix = unigram_settings['orig_run_prefix'] #Same job desc that was used to run tfidf and sigma
    uni_lm_run_prefix = unigram_settings['LM_run_desc']
    uni_lmbda = unigram_settings['lambda']
    uni_alpha = unigram_settings['alpha']
    uni_beta = unigram_settings['beta']
    query_file = unigram_settings['query_file']
    
    print '\nUnigram -  lambda:', uni_lmbda, ' alpha: ', uni_alpha, ' beta: ', uni_beta
    print '\ngamma:', gamma

    #Make folder and file names for unigram model
    uni_model_folder = 'models/%s' % uni_folder_prefix
    #Model folder should already exist from word2vec run, so no need to create it
    uni_modelfile = '%s/%s.bin.model.txt' % (uni_model_folder,uni_folder_prefix)
    uni_vocabfile = '%s/indexed_vocab.txt' % uni_model_folder
    uni_collection_sigmas_file =  '%s/%s_%s_collection_sigmas.txt' % (uni_model_folder,uni_folder_prefix,uni_run_prefix)
    uni_document_sigmas_file = '%s/%s_%s_document_sigmas.txt' % (uni_model_folder,uni_folder_prefix,uni_run_prefix)
    uni_collection_freqs_file =  '%s/%s_%s_coll_terms_freqs.txt' % (uni_model_folder,uni_folder_prefix,uni_run_prefix)
    uni_document_freqs_file = '%s/%s_%s_doc_term_counts_freqs.txt' % (uni_model_folder,uni_folder_prefix,uni_run_prefix)
    uni_tfidfs_file = '%s/%s_%s_tfidf.txt' % (uni_model_folder,uni_folder_prefix,uni_run_prefix)
    uni_topn_tfidfs_file = '%s/%s_%s_topn_tfidf.txt' % (uni_model_folder,uni_folder_prefix,uni_run_prefix)
    
    print 'uni_run_prefix: ', uni_run_prefix
    print 'uni_lm_run_prefix: ', uni_lm_run_prefix
    print 'uni_model_folder: ', uni_model_folder
    print 'uni_modelfile: ', uni_modelfile
    print 'uni_vocabfile: ', uni_vocabfile
    print 'uni_collection_sigmas_file: ', uni_collection_sigmas_file
    print 'uni_document_sigmas_file: ', uni_document_sigmas_file
    print 'uni_collection_freqs_file: ', uni_collection_freqs_file
    print 'uni_document_freqs_file: ', uni_document_freqs_file
    print 'uni_tfidfs_file: ', uni_tfidfs_file
    print 'uni_topn_tfidfs_file: ', uni_topn_tfidfs_file
    
    uni_doctermsfreqsfile = open(uni_document_freqs_file)
    uni_docsigmafile = open(uni_document_sigmas_file)    
    uni_collsigmas = eval(open(uni_collection_sigmas_file).read())
    uni_collfreqs = eval(open(uni_collection_freqs_file).read())
    
    uni_vocab = open(uni_vocabfile).readlines()
    uni_vocab = [x.strip() for x in uni_vocab]
    N = len(uni_vocab)
   
    uni_mapped_vocab = {}
    uni_ordered_vocab = []
     
    for ind in range(N):
         tupl = uni_vocab[ind].lstrip('(').rstrip(')').split(',')
         #print tupl
         uni_mapped_vocab[tupl[0]] = int(tupl[1])
         uni_ordered_vocab.append(tupl[0])
        
    uni_mapped_vocab_file = '%s/lm_%s_mapped_vocab.txt' % (uni_model_folder,uni_run_prefix)
 
    write_to_file(str(uni_mapped_vocab), uni_mapped_vocab_file)
    
    print 'unigram ordered vocab: ', uni_ordered_vocab[0:100]
     
    #Load Unigram word2vec model
    umodel = Word2Vec.load(uni_modelfile) 
    
    #Test neighborhood similarities for a single term
    print 'child', umodel.most_similar(positive=['child'], topn=3)
    print "vector for child: ", umodel['child']
    print 'random vector', umodel.seeded_vector('child')
    print 'similarity', umodel.similarity('child', 'adult')

    #########################################################################
        
    # Get ready to process unigram model queries from unigram topn-tf-idf file

    #########################################################################
    
    uni_topnlines = {}
    bad_doc_ids = []
    lines = open(uni_topn_tfidfs_file).readlines()
    for line in lines:
        rec = eval(line)
        d = int(rec[0])
        tfterms = rec[1]
        if(len(tfterms) < 4): #Only 1 tfidf term, e.g.(2542398,[[84552, 7.3982, 7.3982, 38, 'ondansetron']])
            bad_doc_ids.append(d)
        else:
            uni_topnlines[d] = tfterms
        
    print "check unigram topnlines: ", uni_topnlines.keys()[0:5], '\n' ,uni_topnlines.values()[0:5]
    
    bad_doc_ids.sort()
    
    print "check bad docids: ", len(bad_doc_ids), bad_doc_ids[0:10]
    
    '''
    unigram_queries = []
    unigram_querieslines = open(unigram_query_file).readlines()
    for q in unigram_querieslines:
        unigram_queries.append(eval(q))
    '''
    
    unigram_queries = []
    query_output_file = query_file.replace('.txt','%s_toList.txt' % model_settings_prefix)
    querieslines = open(query_file).readlines()[1:]
    for i in range(len(querieslines)):
        query_word_list = [x for x in querieslines[i].split("|") if x in uni_mapped_vocab.keys()]
        query = (i+1,query_word_list)
        write_to_file('%s\n' % str(query),query_output_file)
        unigram_queries.append(query)

    uNdocs = len(uni_topnlines.keys())
    print 'check unigram queries: ', unigram_queries[0:10], 'Ndocs: ', uNdocs
        
    uni_doctermsfreqs = {} #load full set of doc terms freqs into dict
    uni_doctermsfreqslines = uni_doctermsfreqsfile.readlines()
    for line in uni_doctermsfreqslines:
        rec = eval(line)
        d = int(rec[0])
        docterms = rec[2]
        #discard documents of less than full no of tfids - leads to bad concepts
        if ((len(docterms) >= 20) and (d not in bad_doc_ids)):
           uni_doctermsfreqs[d] = rec

    print 'check uni doctermsfreqs: ', len(uni_doctermsfreqs.keys())
    for k in uni_doctermsfreqs.keys()[0:5]:
        print k,uni_doctermsfreqs[k]

    uni_docsigmas = {} #load final set of doc sigmas into dict - bad_doc_ids + terms < 10
    uni_dkeys = sorted(uni_doctermsfreqs.keys())
    uni_docsigmaslines = uni_docsigmafile.readlines()
    for line in uni_docsigmaslines:
        rec = eval(line)
        d = int(rec[0])
        sigmas = rec[1]
        if(d in uni_dkeys): #only add good docs
            uni_docsigmas[d] = sigmas
            
    print 'check uni docsigmas: '
    for k in uni_docsigmas.keys()[0:5]:
        print k,uni_docsigmas[k]

    ##################################################################

    #Initialize Args and Files for Phrasal Model

    ##################################################################

    phr_folder_prefix = phrasal_settings['model_folder_prefix'] #Give it a model folder as prefix
    phr_run_prefix = phrasal_settings['orig_run_prefix'] #Same job desc that was used to run tfidf and sigma
    phr_lm_run_prefix = phrasal_settings['LM_run_desc']
    phr_lmbda = phrasal_settings['lambda']
    phr_alpha = phrasal_settings['alpha']
    phr_beta = phrasal_settings['beta']
    query_file = phrasal_settings['query_file']
    
    print '\nPhrasal -  lambda:', phr_lmbda, ' alpha: ', phr_alpha, ' beta: ', phr_beta
    print '\ngamma:', gamma

    #Make folder and file names for unigram model
    phr_model_folder = 'models/%s' % phr_folder_prefix
    #Model folder should already exist from word2vec run, so no need to create it
    phr_modelfile = '%s/%s.bin.model.txt' % (phr_model_folder,phr_folder_prefix)
    phr_vocabfile = '%s/indexed_vocab.txt' % phr_model_folder
    phr_collection_sigmas_file =  '%s/%s_%s_collection_sigmas.txt' % (phr_model_folder,phr_folder_prefix,phr_run_prefix)
    phr_document_sigmas_file = '%s/%s_%s_document_sigmas.txt' % (phr_model_folder,phr_folder_prefix,phr_run_prefix)
    phr_collection_freqs_file =  '%s/%s_%s_coll_terms_freqs.txt' % (phr_model_folder,phr_folder_prefix,phr_run_prefix)
    phr_document_freqs_file = '%s/%s_%s_doc_term_counts_freqs.txt' % (phr_model_folder,phr_folder_prefix,phr_run_prefix)
    phr_tfidfs_file = '%s/%s_%s_tfidf.txt' % (phr_model_folder,phr_folder_prefix,phr_run_prefix)
    phr_topn_tfidfs_file = '%s/%s_%s_topn_tfidf.txt' % (phr_model_folder,phr_folder_prefix,phr_run_prefix)
    
    print 'phr_run_prefix: ', phr_run_prefix
    print 'phr_lm_run_prefix: ', phr_lm_run_prefix
    print 'phr_model_folder: ', phr_model_folder
    print 'phr_modelfile: ', phr_modelfile
    print 'phr_vocabfile: ', phr_vocabfile
    print 'phr_collection_sigmas_file: ', phr_collection_sigmas_file
    print 'phr_document_sigmas_file: ', phr_document_sigmas_file
    print 'phr_collection_freqs_file: ', phr_collection_freqs_file
    print 'phr_document_freqs_file: ', phr_document_freqs_file
    print 'phr_tfidfs_file: ', phr_tfidfs_file
    print 'phr_topn_tfidfs_file: ', phr_topn_tfidfs_file
    
    phr_doctermsfreqsfile = open(phr_document_freqs_file)
    phr_docsigmafile = open(phr_document_sigmas_file)    
    phr_collsigmas = eval(open(phr_collection_sigmas_file).read())
    phr_collfreqs = eval(open(phr_collection_freqs_file).read())
    
    phr_vocab = open(phr_vocabfile).readlines()
    phr_vocab = [x.strip() for x in phr_vocab]
    N = len(phr_vocab)
   
    phr_mapped_vocab = {}
    phr_ordered_vocab = []
     
    for ind in range(N):
         tupl = phr_vocab[ind].lstrip('(').rstrip(')').split(',')
         #print tupl
         phr_mapped_vocab[tupl[0]] = int(tupl[1])
         phr_ordered_vocab.append(tupl[0])
        
    phr_mapped_vocab_file = '%s/lm_%s_mapped_vocab.txt' % (phr_model_folder,phr_run_prefix)
 
    write_to_file(str(phr_mapped_vocab), phr_mapped_vocab_file)
    
    print 'phrasal ordered vocab: ', phr_ordered_vocab[0:100]
     
    #Load Phrasal word2vec model
    pmodel = Word2Vec.load(phr_modelfile) 
    
    #Test neighborhood similarities for a single term
    print 'child', pmodel.most_similar(positive=['child'], topn=3)
    print "vector for child: ", pmodel['child']
    print 'random vector', pmodel.seeded_vector('child')
    print 'similarity', pmodel.similarity('child', 'adult')
        
    #########################################################################

    # Get ready to process phrasal model queries from topn-tf-idf file

    #########################################################################
    
    phr_topnlines = {}
    bad_doc_ids = []
    lines = open(phr_topn_tfidfs_file).readlines()
    for line in lines:
        rec = eval(line)
        d = int(rec[0])
        tfterms = rec[1]
        if(len(tfterms) < 4): #Only 1 tfidf term, e.g.(2542398,[[84552, 7.3982, 7.3982, 38, 'ondansetron']])
            bad_doc_ids.append(d)
        else:
            phr_topnlines[d] = tfterms
        
    print "check phrasal topnlines: ", phr_topnlines.keys()[0:5], '\n' , phr_topnlines.values()[0:5]
    
    bad_doc_ids.sort()
    
    print "check bad docids: ", len(bad_doc_ids), bad_doc_ids[0:10]
    
    phrasal_queries = []
    query_output_file = query_file.replace('.txt','%s_toList.txt' % model_settings_prefix)
    querieslines = open(query_file).readlines()[1:]
    for i in range(len(querieslines)):
        query_word_list = [x for x in querieslines[i].split("|") if x in phr_mapped_vocab.keys()]
        query = (i+1,query_word_list)
        write_to_file('%s\n' % str(query),query_output_file)
        phrasal_queries.append(query)
    
    pNdocs = len(uni_topnlines.keys())
    print 'check phrasal queries: ', phrasal_queries[0:10], 'Ndocs: ', pNdocs

    phr_doctermsfreqs = {} #load full set of doc terms freqs into dict
    phr_doctermsfreqslines = phr_doctermsfreqsfile.readlines()
    for line in phr_doctermsfreqslines:
        rec = eval(line)
        d = int(rec[0])
        docterms = rec[2]
        #discard documents of less than full no of tfids - leads to bad concepts
        if ((len(docterms) >= 30) and (d not in bad_doc_ids)):
           phr_doctermsfreqs[d] = rec

    print 'check phrase doctermsfreqs: ', len(phr_doctermsfreqs.keys())
    for k in phr_doctermsfreqs.keys()[0:5]:
        print k,phr_doctermsfreqs[k]

    phr_docsigmas = {} #load final set of doc sigmas into dict - bad_doc_ids + terms < 10
    phr_dkeys = sorted(phr_doctermsfreqs.keys())
    phr_docsigmaslines = phr_docsigmafile.readlines()
    for line in phr_docsigmaslines:
        rec = eval(line)
        d = int(rec[0])
        sigmas = rec[1]
        if(d in phr_dkeys): #only add good docs
            phr_docsigmas[d] = sigmas
            
    print 'check phrase docsigmas: '
    for k in phr_docsigmas.keys()[0:5]:
        print k,phr_docsigmas[k]

    #########################################################################
    
    #Get ready the documents on which to run the interpolated GLM

    #########################################################################

    documents = [int(docid.strip()) for docid in open(docidlistfile).readlines()]

    print "check docids: ", documents[0:10]

    #Run the queries over the interpolated model and score the docs
    tic_start = time.time()
    documents_concepts = []
    concepts_str = ''

    #Num queries is same for both uni and phrasal so this works
    for j in range(len(unigram_queries)):   
        
        uquery = unigram_queries[j][1][0:query_length]
        uquery_docid = unigram_queries[j][0]
        rndlogLmbda = round(log(uni_lmbda),10)
        rndlogCconst = round(log((1-uni_lmbda-uni_alpha-uni_beta)),10)
        rndlogAlpha = round(log(uni_alpha),10)
        rndlogBeta = round(log(uni_beta),10)
        
        print 'unigram query_docid: ', uquery_docid, 'unigram query: ', uquery
        
        pquery = phrasal_queries[j][1][0:query_length]
        pquery_docid = phrasal_queries[j][0]
        prndlogLmbda = round(log(phr_lmbda),10)
        prndlogCconst = round(log((1-phr_lmbda-phr_alpha-phr_beta)),10)
        prndlogAlpha = round(log(phr_alpha),10)
        prndlogBeta = round(log(phr_beta),10)
        
        print 'pquery_docid: ', pquery_docid, 'pquery: ', pquery
        
        tic = time.time()
        
        c = 20000
        #DO this for same doc in both models, check for existing key
        #Loop through all documents, obtain tuple (docid, score) which will be reverse ordered
        document_scores = []
        for d in documents: #The documents common between both models
            try:
                unigram_docsigma = uni_docsigmas[d]
                unigram_doc_keys = uni_doctermsfreqs[d][2][0:100]
                phrase_docsigma = phr_docsigmas[d]
                phrase_doc_keys = phr_doctermsfreqs[d][2][0:130]
                #print 'unigram docsigma: ' , unigram_docsigma
                #print 'phrase docsigma: ' , phrase_docsigma
                #Get score for unigram GLM first
                '''
                do_GLM(lmdocid, rndlogLmbda, rndlogCconst, rndlogAlpha, rndlogBeta, \
                       model, query, mapped_vocab, ordered_vocab, docsigma, doc_keys, \
                       collfreqs, collsigmas, Ndocs)
                '''
                unigram_score =  do_GLM(d, rndlogLmbda, rndlogCconst, rndlogAlpha, rndlogBeta, \
                                        umodel, uquery, uni_mapped_vocab, uni_ordered_vocab, \
                                        unigram_docsigma, unigram_doc_keys, \
                                        uni_collfreqs, uni_collsigmas, uNdocs )
                phrasal_score =  do_GLM(d, prndlogLmbda, prndlogCconst, prndlogAlpha, prndlogBeta, \
                                        pmodel, pquery, phr_mapped_vocab, phr_ordered_vocab, \
                                        phrase_docsigma, phrase_doc_keys, \
                                        phr_collfreqs, phr_collsigmas, pNdocs )
                interpolated_score = gamma * unigram_score + (1-gamma) * phrasal_score
                
                document_scores.append((d,interpolated_score))
                c = c - 1
                if (c < 0):
                    break
            except KeyError:
                print 'KeyError ', d
                pass

       
        document_scores.sort(key=operator.itemgetter(1))
        matching_docs = document_scores[0:5] #Use top 5 matching documents
        print "\n\n\nTop matching documents for document: %s" % uquery_docid , pquery_docid, matching_docs 
    
        toc = time.time()
        te = toc - tic 
        print "Time elapsed for processing LM and top document matches: %s sec" % te 
        
        tic = toc
        
        best_matches = word2vec_concepts(pquery_docid,pquery,matching_docs,pmodel,phr_ordered_vocab,phr_doctermsfreqs)
        best_matches_uni = word2vec_concepts(uquery_docid,uquery,matching_docs,umodel,uni_ordered_vocab,uni_doctermsfreqs)
        word2vec_disc_concepts = [item[1] for item in best_matches.values()]
        word2vec_disc_concepts_uni = [item[1] for item in best_matches_uni.values()]
        tfidf_disc_concepts = tfidf_concepts(matching_docs,phr_topnlines)
        tfidf_disc_concepts_uni = tfidf_concepts(matching_docs,uni_topnlines)
        concept_tuple = (pquery_docid,pquery,word2vec_disc_concepts,tfidf_disc_concepts,word2vec_disc_concepts_uni,tfidf_disc_concepts_uni,matching_docs,best_matches,best_matches_uni)
        discovered_concepts = [word2vec_disc_concepts, tfidf_disc_concepts, word2vec_disc_concepts_uni, tfidf_disc_concepts_uni]
        print "Top discovered concepts for document %s, query - %s :\n %s" % (pquery_docid,pquery,discovered_concepts)
        
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

do_this()


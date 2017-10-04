#!/usr/local/bin/python

"""
@author: Manirupa Das
This script takes in input for settings for various methods for QE
and corresponding output files and generates the query terms 
necessary for input to ES.

"""
import time
import operator
import sys, re, os
from textblob import *
import datetime

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H-%M-%S')

def introspect(desc, list):
    print desc
    for i in range(len(list)):
        print 'Record %s: %s\n' % (i+1, list[i])
    print 'Length ', len(list)

def check():
    if (len(sys.argv)<5):
        print "usage: %s <pipe_sep_input_IDs_file> <methods_setting_file> <folder_prefix_full_path> <num_concepts>" % sys.argv[0]
        exit()
    return

def write_to_file(str_to_print,filename):
    f = open(filename, 'ab')
    f.write(str_to_print)
    f.close()

def do_this():
    check()
    idsfile = open(sys.argv[1])
    settings_list = eval(open(sys.argv[2]).read())
    folder_prefix = sys.argv[3]
    num_concepts = int(sys.argv[4])
    output_file = 'goodinput/SEqueries/methods_QEterms_%s.txt' % os.path.basename(sys.argv[2]).replace('.txt','')
    
    print 'settings_list: ', settings_list
    
    methods_dict = {}
    header_str = 'QueryID'
    for method in settings_list.values():
        method_name = method['Name']
        concepts_lines = open('%s/%s' % (folder_prefix,method['File'])).readlines()
        methods_dict[method_name] = {}
        header_str = '%s\t%s' % (header_str,method_name)
        print header_str #, lines[0:10]
        for line in concepts_lines:
            rec = str(line.strip())
            try:
                docid = int(eval(rec)[0])               
                terms = eval(rec)[int(method['Field'])][0:num_concepts]
                termstr = '|'.join([str(t.replace('-',' ')) for t in terms])
                #print docid, method_name, termstr, methods_dict[method_name], '\n\n'
                methods_dict[method_name][int(docid)] = termstr
            except:
                print "Problem record: ", rec, line
    header_str = '%s\n' % header_str  
    write_to_file(header_str,output_file) 
    
    print 'methods_dict keys: ', methods_dict.keys()
    
    qe_terms = {}
    
    for line in idsfile: 
        temp = line.split()
        qid = int(temp[0])
        qe_pmcids = [int(id) for id in temp[1].split('|')]
        qe_terms[qid] = {}
        for method in methods_dict.keys():
            qe_terms[qid][method] = {}
            qe_terms[qid][method]['pmcids'] = qe_pmcids
            tempterms = []
            for pmcid in qe_pmcids:
                try:
                    tempterms.append(methods_dict[method][pmcid])
                except:
                    print 'pmcid %s not found in methods_dict\n' % pmcid
                    continue
            qe_terms[qid][method]['terms'] = '|'.join(tempterms)
            #print 'qe_terms[%s][%s] = \ntempterms: %s\n' % (qid, method, qe_terms[qid][method]['terms'])
        #create tab-separated entry for different methods
        #print qid, [x['terms'] for x in qe_terms[qid].values()]
        qe_str = '%s\t%s\n' % (qid,'\t'.join([x['terms'] for x in qe_terms[qid].values()]))
        print 'Record: ', qe_str
        write_to_file(qe_str,output_file) 
        
    return

do_this()
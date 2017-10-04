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
    if (len(sys.argv)<3):
        print "usage: %s <methods_setting_file> <folder_prefix_full_path>" % sys.argv[0]
        exit()
    return

def write_to_file(str_to_print,filename):
    f = open(filename, 'ab')
    f.write(str_to_print)
    f.close()

def do_this():
    check()
    settings_list = eval(open(sys.argv[1]).read())
    folder_prefix = sys.argv[2]
    output_file = 'goodinput/SEqueries/methods_QEterms_%s.txt' % os.path.basename(sys.argv[1]).replace('.txt','')
    
    print 'settings_list: ', settings_list
    
    methods_dict = {}
    header_str = 'QueryID'
    for method in settings_list.values():
        method_name = method['Name']
        lines = open('%s/%s' % (folder_prefix,method['File'])).readlines()
        methods_dict[method_name] = {}
        header_str = '%s\t%s' % (header_str,method_name)
        for line in lines:
            rec = line
            try:
                docid = eval(rec)[0]               
                terms = eval(rec)[int(method['Field'])]
                #termstr = '|'.join([str(t) for t in terms])
                termstr = '|'.join([str(t.replace('-',' ')) for t in terms]) 
                #print docid, method_name, termstr, methods_dict[method_name], '\n\n'
                methods_dict[method_name][int(docid)] = termstr
            except:
                print "Problem record: ", rec, line
    header_str = '%s\n' % header_str  
    write_to_file(header_str,output_file) 
    
    print 'methods_dict keys: ', methods_dict.keys()
    
    for q in range(1,31):
        qtermlist = []
        for k in methods_dict.keys():
            qtermlist.append(methods_dict[k][q])
        qe_str = '%s\t%s\n' % (q,'\t'.join([qterms for qterms in qtermlist]))
        print 'Record: ', qe_str
        write_to_file(qe_str,output_file) 
        
    return

do_this()
#!/usr/local/bin/python

import time
import operator
import sys, re, os
from textblob import *


def check():
    if (len(sys.argv)<4):
        print "usage: %s <input_PMCID_file> <source_data_file_eg.PMCID+abstract.txt> <outfile>" % sys.argv[0]
        exit()
    return

def write_to_file(str_to_print,filename):
    f = open(filename, 'ab')
    f.write(str_to_print)
    f.close()
    
def do_this():
    check()
    idfile = sys.argv[1]
    infile = sys.argv[2]
    outfile = sys.argv[3]
    
    ids = (open(idfile).read()).split('\n')[:-1]
    
    print ids[0:10], len(ids)

    lines = open(infile).readlines()
    
    qrels_records = {}
    
    for i in range(len(lines)):
        temp = lines[i].split('\t')
        thisid = temp[0].strip()
        try:
            text = temp[1].strip()
        except:
            text = "null document"
        if (thisid in ids):
            print "YES"
            str_to_print = '%s\t%s\n' % (thisid,text)
            write_to_file(str_to_print,outfile)
                            
do_this()
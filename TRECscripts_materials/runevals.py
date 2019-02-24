#!/usr/local/bin/python

import os
import sys
import time
import datetime

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H-%M-%S')


def write_to_file(str_to_print,filename):
    f = open(filename, 'ab')
    f.write(str_to_print)
    f.close()

def check():
    if (len(sys.argv)<3):
        print "usage: %s <folder_full_path> (containing RankedArticles output files e.g. /Users/das.65/Documents/OSU/Research/ConceptDiscovery/2Seq2SetOutput/FeedbackLoop_seq2set_v2_Feb21_KNNTransformersElmoDANLSTMBilSTMx2wAttTransformer_3terms_SumText <run_desc (no spaces)>" % sys.argv[0]
        exit()
    return

check()

if(len(sys.argv) > 1):
    path = sys.argv[1]
    run_desc = sys.argv[2]

prefix = '/Users/das.65/Documents/OSU/Research/ConceptDiscovery/2Seq2SetResults/evals'
eval_file_all = '%s/evals_all_%s_%s_%s.txt' % (prefix,run_desc,os.path.basename(path),st)
eval_file_byq = '%s/evals_byq_%s_%s_%s.txt' % (prefix,run_desc,os.path.basename(path),st)

for file in os.listdir(path):
    current = os.path.join(path, file)
    if os.path.isfile(current):
        #data = open(current, "rb")
        #print len(data.read())
        str_to_print = 'Evaluating all queries for :\n%s \n' % os.path.basename(current)
        write_to_file(str_to_print,eval_file_all)
        os.system('perl sample_eval.pl qrels-sampleval-2016.txt %s >> %s' % (current,eval_file_all))
        str_to_print = 'Evaluating by query for :\n%s \n' % os.path.basename(current)
        write_to_file(str_to_print,eval_file_byq)
        os.system('perl sample_eval.pl -q qrels-sampleval-2016.txt %s >> %s' % (current,eval_file_byq))

print "Evaluated Ranked files results are located at: %s, %s " % (eval_file_all,eval_file_byq)
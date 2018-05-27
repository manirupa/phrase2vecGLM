#!/usr/local/bin/python
"""
This beautiful automation script helps generate blocks of code for the Search.js file
as well as for the SE run calls to the specified Search.js to be run with the queries
corresponding to the LM or phrase2vec method - USE this script
"""

import string
import time
import datetime
import operator
import sys, re, os
from math import *

ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H-%M-%S')


# header = 'Topic_ID    MeSH_terms    SUM_FULL_TEXT    SUM_UMLS    QueryID    3qlphr_tfidif_G0.1_model_ip_G0.1_L0.2_A0.1_B0.5    3qluni_tfidf_G0.1_model_ip_G0.1_L0.2_A0.1_B0.5    3qluni_G0.1_model_ip_G0.1_L0.2_A0.1_B0.5    3qlphr_tfidf_G0.2_model_ip_G0.2_L0.2_A0.1_B0.5    3qlphr_G0.2_model_ip_G0.2_L0.2_A0.1_B0.5    3qluni_tfidf_G0.2_model_ip_G0.2_L0.2_A0.1_B0.5    3qluni_G0.2_model_ip_G0.2_L0.2_A0.1_B0.5    3qlphr_tfidif_G0.3_model_ip_G0.3_L0.2_A0.1_B0.5    3qlphr_G0.3_model_ip_G0.3_L0.2_A0.1_B0.5    3ql_tfidf_G0.3_model_ipG0.3uA0.3pB0.3    3ql_G0.4_model_ipG0.4uA0.3pB0.3    3ql_tfidf_G0.2_model_ipG0.2uA0.3pB0.3    3ql_G0.3_model_ipG0.3uA0.3pB0.3    3ql_tfidf_G0.1_model_ipG0.1uA0.3pB0.3    3ql_G0.2_model_ipG0.2uA0.3pB0.3    3ql_G0.1_model_ipG0.1uA0.3pB0.3    3ql_tfidf_G0.4_model_ipG0.4uA0.3pB0.3    3ql_G0.5_model_ipG0.5uA0.3pB0.3    3ql_tfidf_G0.9_model_ipG0.9uA0.3pB0.3    3qlphr_G0.1_model_ip_G0.1_L0.2_A0.1_B0.5    3ql_tfidf_G0.5_model_ipG0.5uA0.3pB0.3    3ql_G0.6_model_ipG0.6uA0.3pB0.3    3ql_tfidf_G0.6_model_ipG0.6uA0.3pB0.3    3ql_G0.7_model_ipG0.7uA0.3pB0.3    3ql_tfidf_G0.7_model_ipG0.7uA0.3pB0.3    3ql_G0.8_model_ipG0.8uA0.3pB0.3    3ql_tfidf_G0.8_model_ipG0.8uA0.3pB0.3    3ql_G0.9_model_ipG0.9uA0.3pB0.3    3qluni_tfidf_G0.7_model_ip_G0.7_L0.2_A0.1_B0.5    3qluni_G0.7_model_ip_G0.7_L0.2_A0.1_B0.5    3qlphr_tfidf_G0.7_model_ip_G0.7_L0.2_A0.1_B0.5    3qlphr_G0.7_model_ip_G0.7_L0.2_A0.1_B0.5    3qluni_tfidf_G0.6_model_ip_G0.6_L0.2_A0.1_B0.5    3qluni_G0.6_model_ip_G0.6_L0.2_A0.1_B0.5    3qlphr_tfidf_G0.6_model_ip_G0.6_L0.2_A0.1_B0.5    3qlphr_G0.6_model_ip_G0.6_L0.2_A0.1_B0.5    3qluni_G0.5_model_ip_G0.5_L0.2_A0.1_B0.5    3qluni_tfidf_G0.5_model_ip_G0.5_L0.2_A0.1_B0.5    3qlphr_G0.5_model_ip_G0.5_L0.2_A0.1_B0.5    3qlphr_tfidf_G0.5_model_ip_G0.5_L0.2_A0.1_B0.5    3qluni_G0.4_model_ip_G0.4_L0.2_A0.1_B0.5    3qluni_tfidf_G0.4_model_ip_G0.4_L0.2_A0.1_B0.5    3qlphr_G0.4_model_ip_G0.4_L0.2_A0.1_B0.5    3qlphr_tfidf_G0.4_model_ip_G0.4_L0.2_A0.1_B0.5    3qluni_G0.3_model_ip_G0.3_L0.2_A0.1_B0.5    3qluni_tfidf_G0.3_model_ip_G0.3_L0.2_A0.1_B0.5'
# header = 'Topic_ID    MeSH_terms    SUM_FULL_TEXT    SUM_UMLS    QueryID    3qlphr_G0.9_model_ip_G0.9_L0.2_A0.1_B0.5_ql3    3qluni_G0.6_model_ipG0.6A0.3B0.4_ql3    3qluni_G0.8_model_ip_G0.8_L0.2_A0.1_B0.5_ql3    3qluni_tfidf_G0.6_model_ipG0.6A0.3B0.4_ql3    3qlphr_tfidif_G0.4_model_ipG0.4A0.3B0.4_ql3    3qlphr_G0.4_model_ipG0.4A0.3B0.4_ql3    3qluni_tfidf_G0.4_model_ipG0.4A0.3B0.4_ql3    3qluni_G0.4_model_ipG0.4A0.3B0.4_ql3    3qlphr_tfidf_G0.4_model_ipG0.4A0.3B0.4_ql4    3qlphr_G0.4_model_ipG0.4A0.3B0.4_ql4    3qluni_tfidf_G0.4_model_ipG0.4A0.3B0.4_ql4    3qluni_G0.4_model_ipG0.4A0.3B0.4_ql4    3qlphr_tfidif_G0.4_model_ipG0.4A0.4B0.3_ql3_concepts    3qlphr_G0.4_model_ipG0.4A0.4B0.3_ql3_concepts    3qluni_G0.4_model_ipG0.4A0.4B0.3_ql4    3qluni_tfidf_G0.4_model_ipG0.4A0.4B0.3_ql4    3qlphr_G0.4_model_ipG0.4A0.4B0.3_ql4    3qlphr_tfidf_G0.4_model_ipG0.4A0.4B0.3_ql4    3qluni_G0.4_model_ipG0.4A0.4B0.3_ql3_concepts    3qluni_tfidf_G0.4_model_ipG0.4A0.4B0.3_ql3_concepts    3qluni_tfidf_G0.6_model_ipG0.6A0.4B0.3_ql4    3qlphr_tfidf_G0.9_model_ip_G0.9_L0.2_A0.1_B0.5_ql3    3qlphr_G0.6_model_ipG0.6A0.3B0.4_ql3    3qluni_tfidf_G0.8_model_ip_G0.8_L0.2_A0.1_B0.5_ql3    3qluni_G0.6_model_ipG0.6A0.4B0.3_ql4    3qlphr_tfidf_G0.6_model_ipG0.6A0.3B0.4_ql4    3qlphr_tfidf_G0.6_model_ipG0.6A0.4B0.3_ql4    3qluni_tfidf_G0.9_model_ip_G0.9_L0.2_A0.1_B0.5_ql3    3qlphr_G0.6_model_ipG0.6A0.4B0.3_ql4    3qlphr_G0.6_model_ipG0.6A0.3B0.4_ql4    3qlphr_tfidf_G0.8_model_ip_G0.8_L0.2_A0.1_B0.5_ql3    3qluni_tfidf_G0.6_model_ipG0.6A0.3B0.4_ql4    3qlphr_tfidf_G0.6_model_ipG0.6A0.3B0.4_ql3    3qlphr_G0.8_model_ip_G0.8_L0.2_A0.1_B0.5_ql3    3qluni_G0.9_model_ip_G0.9_L0.2_A0.1_B0.5_ql3    3qluni_G0.6_model_ipG0.6A0.3B0.4_ql4'
# header = 'Topic_ID    MeSH_terms    SUM_FULL_TEXT    SUM_UMLS    QueryID    3qlphr_G0.6_model_ipG0.6A0.4B0.3_ql4    3qluni_G0.6_model_ipG0.6A0.4B0.3_ql4    3qluni_tfidf_G0.6_model_ipG0.6A0.4B0.3_ql4    3qlphr_tfidf_G0.6_model_ipG0.6A0.4B0.3_ql4    3qlphr_tfidif_G0.4_model_ipG0.4A0.4B0.3_ql3    3qlphr_G0.4_model_ipG0.4A0.4B0.3_ql3    3qluni_tfidf_G0.4_model_ipG0.4A0.4B0.3_ql3    3qluni_G0.4_model_ipG0.4A0.4B0.3_ql3    3qlphr_tfidf_G0.6_model_ipG0.6A0.3B0.4_ql3    3qlphr_G0.6_model_ipG0.6A0.3B0.4_ql3    3qluni_tfidf_G0.4_model_ipG0.4A0.3B0.4_ql4    3qluni_G0.6_model_ipG0.6A0.3B0.4_ql3    3qlphr_tfidif_G0.6_model_ipG0.6A0.3B0.4_ql4_concepts    3qlphr_G0.6_model_ipG0.6A0.3B0.4_ql4_concepts    3qluni_G0.6_model_ipG0.6A0.4B0.3_ql3    3qluni_tfidf_G0.6_model_ipG0.6A0.4B0.3_ql3    3qlphr_G0.6_model_ipG0.6A0.4B0.3_ql3    3qlphr_tfidf_G0.6_model_ipG0.6A0.4B0.3_ql3    3qluni_G0.6_model_ipG0.6A0.3B0.4_ql4_concepts    3qluni_tfidf_G0.6_model_ipG0.6A0.3B0.4_ql4_concepts'
# header = 'Topic_ID    MeSH_terms    SUM_FULL_TEXT    QueryID    ip_3ql_tfidf_vs50_cw4_L0.2_A0.3_B0.4_G0.6    ip_4ql_vs50_cw4_L0.2_A0.3_B0.4_G0.6    ip_4ql_tfidf_vs50_cw4_L0.2_uA0.3_pB0.4_G0.4    ip_3ql_vs50_cw4_L0.2_A0.3_B0.4_G0.6    ip_3ql_tfidf_vs50_cw4_L0.2_uA0.3_pB0.4_G0.4    ip_4ql_vs50_cw4_L0.2_uA0.3_pB0.4_G0.4    ip_3ql_tfidf_vs50_cw4_L0.25uA0.45pB0.2iG0.5    ip_3ql_vs50_cw4_L0.2_uA0.3_pB0.4_G0.4    ip_4ql_tfidf_vs50_cw4_L0.2_A0.3_B0.4_G0.6    ip_3ql_vs50_cw4_L0.1uA0.4pB0.2iG0.5    ip_3ql_tfidf_vs50_cw4_L0.25uA0.4pB0.4iG0.6    ip_3ql_vs50_cw4_L0.25uA0.45pB0.2iG0.5    ip_3ql_tfidf_vs50_cw4_L0.1uA0.4pB0.2iG0.5    ip_3ql_vs50_cw4_L0.1uA0.4pB0.4iG0.5    ip_3ql_tfidf_vs50_cw4_L0.1uA0.4pB0.4iG0.5    ip_3ql_vs50_cw4_L0.2uA0.4pB0.2iG0.5    ip_3ql_tfidf_vs50_cw4_L0.2uA0.4pB0.2iG0.5    ip_3ql_vs50_cw4_L0.2uA0.4pB0.4iG0.5    ip_3ql_tfidf_vs50_cw4_L0.2uA0.4pB0.4iG0.5    ip_3ql_vs50_cw4_L0.25uA0.4pB0.4iG0.6    SUM_UMLS'
# header = 'QueryID    5ql_phr_tfidf_G0.6_model_ipG0.6A0.4B0.3_u50p200_5ql_DESC_UMLS    5ql_phr_G0.6_model_ipG0.6A0.4B0.3_u50p200_5ql_DESC_UMLS    5ql_uni_tfidf_G0.6_model_ipG0.6A0.4B0.3_u50p200_5ql_DESC_UMLS    5ql_uni_G0.6_model_ipG0.6A0.4B0.3_u50p200_5ql_DESC_UMLS    5ql_phr_tfidf_G0.6_model_ipG0.6A0.4B0.3_u50p200_5ql_NOTES_UMLS    5ql_phr_G0.6_model_ipG0.6A0.4B0.3_u50p200_5ql_NOTES_UMLS    5ql_uni_tfidf_G0.6_model_ipG0.6A0.4B0.3_u50p200_5ql_NOTES_UMLS    5ql_uni_G0.6_model_ipG0.6A0.4B0.3_u50p200_5ql_NOTES_UMLS    5ql_phr_tfidf_G0.6_model_ipG0.6A0.4B0.3_u50p200_5ql_SUM_UMLS    5ql_phr_G0.6_model_ipG0.6A0.4B0.3_u50p200_5ql_SUM_UMLS    5ql_uni_G0.6_model_ipG0.6A0.4B0.3_u50p200_5ql_SUM_UMLS    5ql_uni_tfidf_G0.6_model_ipG0.6A0.4B0.3_u50p200_5ql_SUM_UMLS    SUM_UMLS    SUM_FULL_TEXT    NOTE_UMLS    DESC_UMLS'
# header= 'Topic_ID    MeSH_terms    SUM_FULL_TEXT    QueryID    phrase437_3ql_tfidf_vs50_cw4_L0.2_A0.4_B0.2_G0.1    phrase437_4ql_vs50_cw4_L0.2_A0.4_B0.2_G0.1    phrase437_5ql_vs50_cw4_L0.2_A0.4_B0.2_G0.1    phrase437_3ql_vs50_cw4_L0.2_A0.4_B0.2_G0.1    phrase437_4ql_tfidf_vs50_cw4_L0.2_A0.4_B0.2_G0.1    phrase437_5ql_tfidf_vs50_cw4_L0.2_A0.4_B0.2_G0.1    SUM_UMLS    uni_3ql_vs50_cw4_L0.2_A0.3_B0.2_G0.1_phrase437_3ql_vs50_cw4_L0.2_A0.4_B0.2_G0.1'
# header = 'Topic_ID    MeSH_terms    SUM_FULL_TEXT    SUM_UMLS    QueryID    interpolated_tfidf_G0.5L0.2uA0.3B0.2pA0.4B0.2_ql5    interpolated_tfidf_G0.5L0.2uA0.3B0.2pA0.4B0.2_ql4    interpolated_G0.5L0.2uA0.3B0.2pA0.4B0.2_ql5    interpolated_tfidf_G0.5L0.2uA0.3B0.2pA0.4B0.2_ql3    interpolated_G0.5L0.2uA0.3B0.2pA0.4B0.2_ql4    interpolated_G0.5L0.2uA0.3B0.2pA0.4B0.2_ql3'
# header = 'QueryID    querytopics_phr_DESC_UMLS_paramsL0.2_A0.3_B0.2    querytopics_phr_SUM_UMLS_paramsL0.2_A0.3_B0.2    querytopics_phr_DESC_UMLS_paramsL0.2_A0.2_B0.4    querytopics_phr_NOTES_UMLS_paramsL0.2_A0.3_B0.2    querytopics_phr_SUM_UMLS_paramsL0.2_A0.2_B0.4    querytopics_phr_NOTES_UMLS_paramsL0.2_A0.2_B0.4    SUM_FULL_TEXT    DESC_UMLS    SUM_UMLS    NOTE_UMLS    Topic_ID    ExpertTerms'
# header = 'Topic_ID    MeSH_terms    SUM_FULL_TEXT    QueryID    phrase437_3ql_tfidf_vs50_cw4_L0.5_A0.0_B0.0_G0.5    phrase437_3ql_tfidf_vs50_cw4_L0.0_A0.5_B0.5_G0.0    phrase437_3ql_vs50_cw4_L0.5_A0.0_B0.0_G0.5    phrase437_3ql_vs50_cw4_L0.0_A0.5_B0.5_G0.0    phrase437_3ql_phrase2vec    SUM_UMLS'

#ADD A NEW HEADER FROM QUERY FILE HERE, MOVE THIS ABOVE
header = 'Topic_ID    MeSH_terms    SUM_FULL_TEXT    QueryID    querytopics_vs50_cw4_phrase2vec_SUM_UMLS_Direct    querytopics_vs50_cw4_phrase2vec_SummaryTextDirect    querytopics_vs50_cw4_L0.5_A0.0_B0.0_G0.5_SUM_UMLS_Direct    querytopics_vs50_cw4_L0.5_A0.0_B0.0_G0.5_SummaryText_Direct'

keys = header.split()

print '%s\n' % str([(i,keys[i]) for i in range(len(keys))])

# script_name = 'Search_ip_A0.3-0.4B0.3-0.4_ql3-4_20K.js'
# script_name = 'Search_ip_vs200_querytopics.js'
# script_name = 'Search_uni+phr_combined.js'
# script_name = 'Search_phr_UMLS.js'
# script_name = 'Search_vs50_phrases437_L0.5A0.0B0.0G0.5_2ndlevel.js'

#ADD A NEW SCRIPT NAME HERE, MOVE THIS ABOVE
script_name = 'Search_vs50_phrases437_L0.5A0.0B0.0G0.5_phrase2Vec_Direct.js'

block = '''
            //REPLACE            FIELD
            else if (method == "REPLACE"){
                if(fields[FIELD].length > 1){
                    dicTopics[fields[0]] = dicTopics[fields[0]].concat(fields[FIELD].split(/\|/));
              }
            }'''

genblock = ''
nodeSrchStr = ''
for i in range(len(keys)):
    print '            //%s, %s' % (i, keys[i])
    genblock += '%s\n' % block.replace('REPLACE', keys[i]).replace('FIELD', str(i))
    nodeSrchStr += 'node %s %s > logs/ip_%s.log.txt &\n' % (script_name,keys[i],keys[i])
    
print genblock

print nodeSrchStr
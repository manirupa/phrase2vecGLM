#!/usr/local/bin/python

import numpy
import scipy
import matplotlib
import nltk
import mechanize
import sklearn
import gensim
# from pulp import value, LpVariable, LpProblem, LpMinimize, LpStatus
# 
# x = LpVariable("x", 0, 3)
# y = LpVariable("y", 0, 1)
# prob = LpProblem("myProblem", LpMinimize)
# prob = LpProblem("myProblem", LpMinimize)
# prob += -4*x + y
# status = prob.solve()
# #status = prob.solve(GLPK(msg = 0))
# print LpStatus[status]
# print value(x)

#import wikipedia
from wikipedia import *
print wikipedia.summary("Wikipedia")

ny = wikipedia.page("New York")
ny.title
ny.url
s1 = ny.content
ml = wikipedia.page("Machine Learning")
ml.title
ml.url
s2 = ml.content

sentences = [s1.split(), s2.split()]

print sentences
from gensim.models import Word2Vec
min_count = 2
size = 50
window = 4
 
model = Word2Vec(sentences, min_count=min_count, size=size, window=window)
vocab = list(model.vocab.keys())
vocab[:10]



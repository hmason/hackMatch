#!/usr/bin/env python
# encoding: utf-8
"""
hackmatch.py

Created by Hilary Mason on 2010-05-02.
Copyright (c) 2010 Hilary Mason. All rights reserved.
"""

import sys, os
import csv
import string
from collections import defaultdict
from nltk.tokenize import *
from nltk.corpus import stopwords
from hcluster import jaccard

# startups: Name,E-mail,Company,In NYC,Funding,Site,Blog,Twitter,Num Employees,Environment,Project,Skills,Misc
# students: Student Name,e-mail,University,Major,Degree,Graduation Date,Site,Blog,Twitter,Facebook,Project,Skills,Misc

class HackMatch(object):
    DEBUG = False
    STUDENT_FILE = 'unmatched_students.csv'
    STARTUP_FILE = 'unmatched_top_startups.csv'
    BOW_FIELDS = ['Environment', 'Project', 'Skills', 'Misc']
    COMPLETENESS_THRESHOLD = 4 # num of words necessary to match
    
    def __init__(self, distance=jaccard, num_matches=3):
        self.stopwords = self.get_stopwords()
        self.distance = distance
        
        student_data = self.parseCSV(self.STUDENT_FILE)
        startup_data = self.parseCSV(self.STARTUP_FILE)
        
        doc_words = self.defineFeatures([student_data, startup_data], self.BOW_FIELDS)

        # matches = self.doRanking(student_data, startup_data, doc_words, self.BOW_FIELDS, base_name_field='Student Name', match_name_field='Company')
        matches = self.doRanking(startup_data, student_data, doc_words, self.BOW_FIELDS)

        self.printMatches(matches, num_matches)
        
    def printMatches(self, matches, num_matches):
        for n, m in matches.items():
            print n
            for item, score in sorted(m.items(), key=lambda(i,c):(-c, i))[:num_matches]:
                print "\t%s :: %s" % (item, score)
                # print "'%s' '%s' %s" % (n.translate(string.maketrans("",""), string.punctuation), item.translate(string.maketrans("",""), string.punctuation), score)
            print '\n'
            
        
    def doRanking(self, base_data, match_data, doc_words, fields=[], base_name_field='Company', match_name_field='Student Name'):
        """
        do ranking
        """
        base = {}
        for item in base_data:
            base[item[base_name_field]] = self.extractFeatures(item, doc_words, fields)
            
        matches = defaultdict(dict)
        for match_item in match_data:
            match_features = self.extractFeatures(match_item, doc_words, fields)

            for base_item, base_item_features in base.items(): # actually do the comparison
                if not base_item_features or not match_features:
                    matches[match_item[match_name_field]][base_item] = 0.0
                else:
                    matches[match_item[match_name_field]][base_item] = self.distance(base_item_features, match_features)
                if self.DEBUG:
                    print "%s :: %s = %s " % (match_item[match_name_field], base_item, self.distance(base_item_features, match_features))

        return matches

    def extractFeatures(self, item, doc_words, fields=[]):
        s_tokens = []
        for f in fields:
            tokens = None
            try:
                tokens = word_tokenize(item[f])
            except (KeyError, TypeError):
                pass
                
            if tokens:
                s_tokens.extend(tokens)
        
        s_features = []        
        for token in doc_words:
            if token in s_tokens:
                s_features.append(1)
            else:
                s_features.append(0)
        
        if sum(s_features) <= self.COMPLETENESS_THRESHOLD:
            return None
            
        return s_features

    def defineFeatures(self, data, fields=[]):
        """
        define the global bag of words features
        """
        ngram_freq = {}
        
        for d in data:
            for r in d:
                for f in fields:
                    tokens = None
                    try:
                        tokens = word_tokenize(r[f])
                    except (KeyError, TypeError):
                        pass
                    
                    if tokens:
                        for t in [t.lower() for t in tokens if t.lower() not in self.stopwords]:
                            t = t.strip('.')
                            ngram_freq[t] = ngram_freq.get(t, 0) + 1

                        # for i in range(0,len(ngram_freq)):
                            
        ngram_freq = dict([(w,c) for w,c in ngram_freq.items() if c > 1])
        if self.DEBUG:
            print "Global vocabulary: %s" % len(ngram_freq)        
        return ngram_freq
    
    def get_stopwords(self):
        sw = stopwords.words('english')
        sw.extend([',', '\xe2', '.', ')', '(', ':', "'s", "'nt", '\x99', '\x86', '\xae', '\x92'])
        return sw
            
    def parseCSV(self, filename):
        """
        parseCSV: parses the CSV file to a dict
        """
        csv_reader = csv.DictReader(open(filename))
        return [r for r in csv_reader]
        
        
if __name__ == '__main__':
    h = HackMatch(num_matches=15)
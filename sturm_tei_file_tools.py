from sturm_tei_parser import sturm_tei_file
import os
from os.path import join, basename
import spacy
import json
import random
from bs4 import BeautifulSoup

_ner_tag_list=['date','pers','place']

def merge_statistics(firststatistics,secondstatistics):
        for key in secondstatistics.keys():
            if key in firststatistics.keys():
                firststatistics[key][0]+=secondstatistics[key][0]
                firststatistics[key][1]+=secondstatistics[key][1]
            else:
                firststatistics[key]=secondstatistics[key]
        return firststatistics

def build_ner_statistics(directory):
    statistics={}
    for filename in os.listdir(directory):
        print(filename)
        brief=sturm_tei_file(directory+'/'+filename)
        statistics=merge_statistics(statistics,brief.get_statistics())
    for key in statistics.keys():
            print(key,statistics[key])

def split_into_sentences(tagged_text_line_list):
    cur_sentence=[]
    sentence_list=[]
    for text_part in tagged_text_line_list:
        for word in text_part:
            if word[2]==2:
                if len(cur_sentence)>0:
                    sentence_list.append(cur_sentence)
                cur_sentence=[word]
            else:
                cur_sentence.append(word)
    if len(cur_sentence)>0:
        sentence_list.append(cur_sentence)
    return sentence_list

def build_ner_training_data(directory,outfile,with_rs=False):

    #  before first use download the spacy model by: python -m spacy download de_core_news_sm
    nlp =spacy.load('de_core_news_sm')
    training_data=[]
    for filename in os.listdir(directory):
           brief=sturm_tei_file(directory+'/'+filename,nlp)
           training_data+=split_into_sentences(brief.build_tagged_text_line_list())
    for i in range(len(training_data)):
          for j in range(len(training_data[i])):
              for tag in _ner_tag_list:
                  if tag in training_data[i][j][1]:
                      if with_rs and training_data[i][j][1].startswith('re'):
                          training_data[i][j][1]='rs'+tag
                      else:
                          training_data[i][j][1]=tag
    with open(outfile,'w+') as g:
        json.dump(training_data,g)

def build_ner_data_per_file(directory,outdirectory,fname=None):
    #  before first use download the spacy model by: python -m spacy download de_core_news_sm
    nlp =spacy.load('de_core_news_sm')

    if fname is not None:
        filelist=[join(directory,fname)]
    else:
        filelist=os.listdir(directory)
    for filename in filelist:
        if 1==1:
            brief=sturm_tei_file(join(directory,filename),nlp)
            raw_ner_data=split_into_sentences(brief.build_tagged_text_line_list())
            for i in range(len(raw_ner_data)):
                for j in range(len(raw_ner_data[i])):
                    for tag in _ner_tag_list:
                        if tag in raw_ner_data[i][j][1]:
                            raw_ner_data[i][j][1]=tag
            with open(join(outdirectory,filename+'.json'),'w+') as g:
                json.dump(raw_ner_data,g)

def count_tags_in_json(filelist):
    tag_collect={}
    for filename in filelist:
        with open(filename) as f:
            training_data=json.load(f)
        #print(len(training_data))
        for i in range(len(training_data)):
            for j in range(len(training_data[i])):
                if training_data[i][j][1] in tag_collect.keys():
                    tag_collect[training_data[i][j][1]]+=1
                else:
                    tag_collect[training_data[i][j][1]]=1
    print({k: v for k, v in sorted(tag_collect.items(), key=lambda item: item[1])})

if __name__ == '__main__':
    #build_ner_statistics('../data_sturm/briefe')
    #build_ner_training_data('../data_sturm/briefe','../data_sturm/train_data.json')
    count_tags_in_json(['../data_sturm/train_data.json'])
    #split_train_data_in_val_and_train_set('../data_040520/train_data.json','../data_040520/data_uja_ner_train2.json','../data_040520/data_uja_ner_val2.json',0.2)
    #build_ner_data_per_file('../data_sturm/briefe','../data_sturm/data_to_train')

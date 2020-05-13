from tei_parser import uja_tei_file
import os
import spacy
import json
import random

_ner_tag_list=['date','pers','city','ground','water','org']

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
        if int(filename[:4])<223:
           print(filename)
           brief=uja_tei_file(directory+'/'+filename)
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

def build_ner_training_data(directory,outfile):

    #  before first use download the spacy model by: python -m spacy download de_core_news_sm
    nlp =spacy.load('de_core_news_sm')
    training_data=[]
    for filename in os.listdir(directory):
        if int(filename[:4])<223:
           brief=uja_tei_file(directory+'/'+filename,nlp)
           training_data+=split_into_sentences(brief.build_tagged_text_line_list())
    for i in range(len(training_data)):
          for j in range(len(training_data[i])):
              for tag in _ner_tag_list:
                  if tag in training_data[i][j][1]:
                      training_data[i][j][1]=tag
    with open(outfile,'w+') as g:
        json.dump(training_data,g)

def test_load_json(filename):
    with open(filename) as f:
        training_data=json.load(f)
    print(len(training_data))
    tag_collect={}
    for i in range(len(training_data)):
          for j in range(len(training_data[i])):
              if training_data[i][j][1] in tag_collect.keys():
                  tag_collect[training_data[i][j][1]]+=1
              else:
                  tag_collect[training_data[i][j][1]]=1
    print(tag_collect)

def split_train_data_in_val_and_train_set(filename,trainfilename,valfilename,valrate=0.1):
    with open(filename) as f:
        training_data=json.load(f)
    val_list=[]
    train_list=[]
    random.shuffle(training_data)
    for i in range(len(training_data)):
        if i<valrate*len(training_data):
            val_list.append(training_data[i])
        else:
            train_list.append(training_data[i])
    with open(valfilename,'w+') as g:
        json.dump(val_list,g)
    with open(trainfilename,'w+') as h:
        json.dump(train_list,h)




if __name__ == '__main__':
    #build_ner_statistics('../data_040520/briefe')
    #build_ner_training_data('../data_040520/briefe','../data_040520/train_data.json')
    #test_load_json('../data_040520/train_data.json')
    #split_train_data_in_val_and_train_set('../data_040520/train_data.json','../data_040520/data_uja_ner_train.json','../data_040520/data_uja_ner_val.json')
    print('Alles:')
    test_load_json('../data_040520/train_data.json')
    print('Val:')
    test_load_json('../data_040520/data_uja_ner_val.json')
    print('Train:')
    test_load_json('../data_040520/data_uja_ner_train.json')


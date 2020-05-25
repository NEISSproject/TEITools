from tei_parser import uja_tei_file,reconstruct_text
import os
from os.path import join, basename
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

def build_data_for_prediction(directory,outdirectory,fname=None):
    #  before first use download the spacy model by: python -m spacy download de_core_news_sm
    nlp =spacy.load('de_core_news_sm')

    if fname is not None:
        filelist=[join(directory,fname)]
    else:
        filelist=os.listdir(directory)
    for filename in filelist:
        brief=uja_tei_file(join(directory,filename),nlp)
        raw_ner_data=split_into_sentences(brief.build_tagged_text_line_list())
        for i in range(len(raw_ner_data)):
            for j in range(len(raw_ner_data[i])):
                for tag in _ner_tag_list:
                    if tag in raw_ner_data[i][j][1]:
                        raw_ner_data[i][j][1]=tag
        with open(join(outdirectory,filename+'.json'),'w+') as g:
            json.dump(raw_ner_data,g)


def count_tags_in_json(filename):
    with open(filename) as f:
        training_data=json.load(f)
    #print(len(training_data))
    tag_collect={}
    for i in range(len(training_data)):
          for j in range(len(training_data[i])):
              if training_data[i][j][1] in tag_collect.keys():
                  tag_collect[training_data[i][j][1]]+=1
              else:
                  tag_collect[training_data[i][j][1]]=1
    print({k: v for k, v in sorted(tag_collect.items(), key=lambda item: item[1])})

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

def reconstruct_text_to_predicted_data(directory,outdirectory):
    for filename in os.listdir(directory):
        with open(join(directory,filename)) as f:
            predicted_data=json.load(f)
        with open(join(outdirectory,filename+'.txt'),'w+') as g:
            g.write(reconstruct_text(predicted_data,False, True))

def show_statistics_of_json_files(filelist):
    for file in filelist:
        print(file+':')
        count_tags_in_json(file)

def _map_to_type(c):
    if c.isalpha():
        if c.isupper():
            return 'A'
        else:
            return 'a'
    elif c.isnumeric():
        return 'd'
    else:
        return c

def build_tfaip_type_vocab_for_train_data(train_data_file,outfilename):
    d={}
    with open(train_data_file) as f:
        train_data=json.load(f)
        #print(train_data[0])
        #print(train_data[1])
        for train_line in train_data:
            for word in train_line:
                type="".join([_map_to_type(c) for c in word[0]])
                if type not in d:
                    d[type]=1
                else:
                    d[type]= 1 + d[type]


    sorted_types = sorted(d.items(), key=lambda kv: -kv[1])
    with open(outfilename, 'w+') as f:
        for c, val in sorted_types:
            f.write('{}\t{}\n'.format(c, val))

def build_tfaip_ner_train_data(train_data_file,outfilename,build_vocab=False):
    chars = {}
    words = {}
    with open(outfilename, "w+") as g:
        with open(train_data_file) as f:
            train_data=json.load(f)
            #print(train_data[0])
            #print(train_data[1])
            for train_line in train_data:
                for word in train_line:
                    if word[0] not in words:
                        words[word[0]]=1
                    else:
                        words[word[0]]=1+words[word[0]]
                    for w in word[0]:
                        if w not in chars:
                            chars[w] = 1
                        else:
                            chars[w] = 1 + chars[w]
                    g.write('{}\t{}\t{}\t{}\n'.format(word[0], word[1], 0,"".join([_map_to_type(c) for c in word[0]])))
                # print("\n")
                g.write('\n')
    if build_vocab:
        sorted_chars = sorted(chars.items(), key=lambda kv: -kv[1])
        with open("../data_040520/chars.vocab.tsv", 'w+') as f:
            for c, val in sorted_chars:
                f.write('{}\t{}\n'.format(c, val))

        sorted_words = sorted(words.items(), key=lambda kv: -kv[1])
        with open("../data_040520/words.vocab.tsv", 'w+') as f:
            for w, val in sorted_words:
                f.write('{}\t{}\n'.format(w, val))

def find_errors_in_predicted_data(predpath,origpath):
    count_all=0
    count_error=0
    tagged_origs=0
    tagged_preds=0
    tagged_origs_error=0
    tagged_preds_error=0
    for filename in os.listdir(origpath):
        if int(filename[:4])<223:
            with open(origpath+'/'+filename) as f:
                with open(predpath+'/pred_'+filename) as g:
                    orig_data=json.load(f)
                    pred_data=json.load(g)
                    for i in range(len(orig_data)):
                        for j in range(len(orig_data[i])):
                            count_all+=1
                            if orig_data[i][j][1]!='O':
                                tagged_origs+=1
                            if pred_data[i][j][1]!='O':
                                tagged_preds+=1
                            if orig_data[i][j][1]!=pred_data[i][j][1]:
                                count_error+=1
                                print('Fehler in ' + origpath+'/'+filename)
                                print('Satz ' + str(i+1) + ' Wort ' + str(j+1) + ' ')
                                print(orig_data[i][j][0] + ' ' + orig_data[i][j][1] + ' ' + pred_data[i][j][1])
                                if orig_data[i][j][1]!='O':
                                    tagged_origs_error+=1
                                if pred_data[i][j][1]!='O':
                                    tagged_preds_error+=1
    print('Accuracy: ' + str(float((1-count_error/count_all)*100)) + '%')
    print('Precision: ' + str(float((1-tagged_preds_error/tagged_preds)*100)) + '%')
    print('Recall: ' + str(float((1-tagged_origs_error/tagged_origs)*100)) + '%')







if __name__ == '__main__':
    #build_ner_statistics('../data_040520/briefe')
    #build_ner_training_data('../data_040520/briefe','../data_040520/train_data.json')
    #count_tags_in_json('../data_040520/train_data.json')
    #split_train_data_in_val_and_train_set('../data_040520/train_data.json','../data_040520/data_uja_ner_train2.json','../data_040520/data_uja_ner_val2.json',0.2)
    #build_data_for_prediction('../data_040520/briefe','../data_040520/data_to_predict')
    #reconstruct_text_to_predicted_data('../data_040520/predicted_data2/','../data_040520/text_from_predicted_data2/')
    #build_tfaip_type_vocab_for_train_data('../data_040520/train_data.json','../data_040520/types.vocab.tsv')
    #build_tfaip_ner_train_data('../data_040520/data_uja_ner_val2.json','../data_040520/tf_aip_uja_ner_val.txt',False)
    find_errors_in_predicted_data('../data_040520/predicted_data2','../data_040520/data_to_predict')
    #count_tags_in_json('../data_040520/train_data.json')
    #show_statistics_of_json_files(['../data_040520/train_data.json','../data_040520/data_uja_ner_train2.json','../data_040520/data_uja_ner_val2.json','../data_040520/data_uja_ner_train.json','../data_040520/data_uja_ner_val.json'])


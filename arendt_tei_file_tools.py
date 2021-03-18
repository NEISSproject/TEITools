from arendt_tei_parser import arendt_tei_file
import os
from os.path import join, basename
import spacy
import json
import random
from bs4 import BeautifulSoup

_ner_tag_mapper = {'nameperson': 'person'
    , 'nameplace': 'place'
    , 'nameethnicity': 'ethnicity'
    , 'nameevent': 'event'
    , 'namebiblicalFigure': 'person'
    , 'nameficticiousPerson': 'person'
    , 'namedeity': 'person'
    , 'nameorganization': 'organization'
    , 'namemythologicalFigure': 'person'
    , 'namelanguage': 'language'
    , 'namecountry': 'place'}


# ['person','place','ethnicity','event','organization','language']

def merge_statistics(firststatistics, secondstatistics):
    for key in secondstatistics.keys():
        if key in firststatistics.keys():
            firststatistics[key][0] += secondstatistics[key][0]
            firststatistics[key][1] += secondstatistics[key][1]
        else:
            firststatistics[key] = secondstatistics[key]
    return firststatistics


def build_ner_statistics(directory):
    statistics = {}
    for filename in os.listdir(directory):
        print(filename)
        if filename.endswith('.xml'):
            brief = arendt_tei_file(directory + '/' + filename)
            statistics = merge_statistics(statistics, brief.get_statistics())
    for key in statistics.keys():
        print(key, statistics[key][0])


def split_into_sentences(tagged_text_line_list):
    cur_sentence = []
    sentence_list = []
    for text_part in tagged_text_line_list:
        for word in text_part:
            if word[2] == 2:
                if len(cur_sentence) > 0:
                    sentence_list.append(cur_sentence)
                cur_sentence = [word]
            else:
                cur_sentence.append(word)
    if len(cur_sentence) > 0:
        sentence_list.append(cur_sentence)
    return sentence_list


def build_ner_training_data(directory, outfile, with_position_tags=False):
    #  before first use download the spacy model by: python -m spacy download de_core_news_sm
    nlp = spacy.load('de_core_news_sm')
    training_data = []
    for filename in os.listdir(directory):
        if filename.endswith('.xml'):
            brief = arendt_tei_file(directory + '/' + filename, nlp,with_position_tags=with_position_tags)
            training_data += split_into_sentences(brief.build_tagged_text_line_list())
    for i in range(len(training_data)):
        for j in range(len(training_data[i])):
            cur_tag = training_data[i][j][1]
            if cur_tag.startswith('B-') or cur_tag.startswith('I-'):
                cur_start=cur_tag[:2]
                cur_tag=cur_tag[2:]
            else:
                cur_start=''
            training_data[i][j][1] = 'O'
            for tag in _ner_tag_mapper.keys():
                if tag == cur_tag:
                    training_data[i][j][1] = cur_start + _ner_tag_mapper[tag]
    with open(outfile, 'w+') as g:
        json.dump(training_data, g)


def build_ner_data_per_file(directory, outdirectory, fname=None, with_position_tags=False):
    #  before first use download the spacy model by: python -m spacy download de_core_news_sm
    nlp = spacy.load('de_core_news_sm')

    if fname is not None:
        filelist = [join(directory, fname)]
    else:
        filelist = os.listdir(directory)
    for filename in filelist:
        if filename.endswith('.xml'):
            brief = arendt_tei_file(join(directory, filename), nlp,with_position_tags=with_position_tags)
            raw_ner_data = split_into_sentences(brief.build_tagged_text_line_list())
            for i in range(len(raw_ner_data)):
                for j in range(len(raw_ner_data[i])):
                    cur_tag = raw_ner_data[i][j][1]
                    if cur_tag.startswith('B-') or cur_tag.startswith('I-'):
                        cur_start=cur_tag[:2]
                        cur_tag=cur_tag[2:]
                    else:
                        cur_start=''
                    raw_ner_data[i][j][1] = 'O'
                    for tag in _ner_tag_mapper.keys():
                        if tag == cur_tag:
                            raw_ner_data[i][j][1] = cur_start + _ner_tag_mapper[tag]
            with open(join(outdirectory, filename + '.json'), 'w+') as g:
                json.dump(raw_ner_data, g)


def count_tags_in_json(filelist):
    tag_collect = {}
    for filename in filelist:
        with open(filename) as f:
            training_data = json.load(f)
        # print(len(training_data))
        for i in range(len(training_data)):
            for j in range(len(training_data[i])):
                if training_data[i][j][1] in tag_collect.keys():
                    tag_collect[training_data[i][j][1]] += 1
                else:
                    tag_collect[training_data[i][j][1]] = 1
    print({k: v for k, v in sorted(tag_collect.items(), key=lambda item: item[1])})


def count_tags_in_list_file(listfile):
    fnames = []
    print(listfile)
    with open(listfile, 'r') as f:
        fnames.extend(f.read().splitlines())
    # print(fnames)
    count_tags_in_json(fnames)

def check_correctness(file):
    count=0
    textlist=[]
    with open(file) as f:
        textlist.extend(json.load(f))
    for element in textlist:
        for i in range(len(element)):
            if (i==0 or element[i-1][1].replace('B-','I-')!=element[i][1]) and element[i][1].startswith('I-'):
                count+=1
                print(element)
    print(count)

def check_correctness_in_list_file(listfile):
    fnames = []
    with open(listfile, 'r') as f:
        fnames.extend(f.read().splitlines())
    #print(fnames)
    for file in fnames:
        check_correctness(file)

def split_train_data_in_val_dev_and_train_set(filename,trainfilename,valfilename,devfilename,valrate=0.1,devrate=0.1):
    with open(filename) as f:
        training_data=json.load(f)
    val_list=[]
    dev_list=[]
    train_list=[]
    random.shuffle(training_data)
    for i in range(len(training_data)):
        if i<valrate*len(training_data):
            val_list.append(training_data[i])
        elif i<(valrate+devrate)*len(training_data):
            dev_list.append(training_data[i])
        else:
            train_list.append(training_data[i])
    with open(valfilename,'w+') as g:
        json.dump(val_list,g)
    with open(devfilename,'w+') as g2:
        json.dump(dev_list,g2)
    with open(trainfilename,'w+') as h:
        json.dump(train_list,h)


if __name__ == '__main__':
    #build_ner_statistics('../../uwe_johnson_data/data_hannah_arendt/')
    #build_ner_training_data('../../uwe_johnson_data/data_hannah_arendt/','../../uwe_johnson_data/data_hannah_arendt/train_data.json',with_position_tags=True)
    #count_tags_in_json(['../../uwe_johnson_data/data_hannah_arendt/train_data.json'])
    # split_train_data_in_val_and_train_set('../data_040520/train_data.json','../data_040520/data_uja_ner_train2.json','../data_040520/data_uja_ner_val2.json',0.2)
    #build_ner_data_per_file('../../uwe_johnson_data/data_hannah_arendt/','../../uwe_johnson_data/data_hannah_arendt/data_to_train',with_position_tags=True)

    #count_tags_in_list_file("lists/sturm_full.lst")
    count_tags_in_list_file("lists/train_sturm.lst")
    count_tags_in_list_file("lists/test_sturm.lst")
    count_tags_in_list_file("lists/dev_sturm.lst")
    #count_tags_in_list_file("lists/train2_arendt.lst")
    #check_correctness_in_list_file("lists/test_arendt.lst")
    #split_train_data_in_val_dev_and_train_set('data/arendt.json','data/train_arendt.json','data/val_arendt.json','data/dev_arendt.json')
    #count_tags_in_json(['data/arendt.json'])
    #count_tags_in_json(['data/train_arendt.json'])
    #count_tags_in_json(['data/val_arendt.json'])
    #count_tags_in_json(['data/dev_arendt.json'])


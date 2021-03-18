import json
import random

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
    #print({k: v for k, v in sorted(tag_collect.items(), key=lambda item: item[1])})
    for k in sorted(tag_collect.keys()):
        if not k.startswith('I-'):
            print(k, tag_collect[k])

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


def count_tags_in_list_file(listfile):
    fnames = []
    with open(listfile, 'r') as f:
        fnames.extend(f.read().splitlines())
    # print(fnames)
    count_tags_in_json(fnames)

if __name__ == '__main__':
    split_train_data_in_val_and_train_set('data/LER/ler.conll_cg_wp_train.json','data/LER/ler.conll_cg_wp_train2.json','data/LER/ler.conll_cg_wp_dev.json')
    print('Train')
    count_tags_in_list_file("lists/train_ler_cg_wp.lst")
    print('Val')
    count_tags_in_list_file("lists/val_ler_cg_wp.lst")
    print('Train2')
    count_tags_in_list_file("lists/train2_ler_cg_wp.lst")
    print('Dev')
    count_tags_in_list_file("lists/dev_ler_cg_wp.lst")

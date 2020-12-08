import json

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

def count_sentence_length_in_json(filelist):
    sen_len_collect = {}
    for filename in filelist:
        with open(filename) as f:
            training_data = json.load(f)
        # print(len(training_data))
        for i in range(len(training_data)):
                if len(training_data[i]) in sen_len_collect.keys():
                    sen_len_collect[len(training_data[i])] += 1
                else:
                    sen_len_collect[len(training_data[i])] = 1
    print({k: v for k, v in sorted(sen_len_collect.items(), key=lambda item: item[0])})


def count_tags_in_list_file(listfile):
    fnames = []
    with open(listfile, 'r') as f:
        fnames.extend(f.read().splitlines())
    # print(fnames)
    count_tags_in_json(fnames)

def shorten_sentences_in_json(filename,max_word_number=500):
    new_training_data=[]
    with open(filename) as f:
        training_data = json.load(f)
    for i in range(len(training_data)):
        if len(training_data[i])<=max_word_number:
            new_training_data.append(training_data[i])
    with open(filename, 'w+') as g:
        json.dump(new_training_data, g)



if __name__ == '__main__':
    #count_tags_in_json(['../../tf_neiss_test/data/LER/ler.conll_fg_wp_train.json','../../tf_neiss_test/data/LER/ler.conll_fg_wp_val.json'])
    count_sentence_length_in_json(['../../tf_neiss_test/data/LER/ler.conll_fg_wp_train.json','../../tf_neiss_test/data/LER/ler.conll_fg_wp_val.json'])
    #shorten_sentences_in_json('../../tf_neiss_test/data/LER/ler.conll_cg_wp_train.json')

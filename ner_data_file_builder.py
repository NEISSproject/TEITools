import json
import random

def build_train_file_from_lst_file(lst_file,outfilename):
    fnames = []
    with open(lst_file, 'r') as f:
        fnames.extend(f.read().splitlines())
    print(fnames)
    textlist=[]
    for filename in fnames:
        with open('../../tf_neiss_test/'+filename) as f:
            textlist.extend(json.load(f))
    for i in range(len(textlist)):
        textlist[i]=[el[0:2] for el in textlist[i]]
    random.shuffle(textlist)
    with open(outfilename, 'w+') as g:
        json.dump(textlist, g)

def build_whole_file_conll_json(filelist,writefilename):
    textlist=[]
    conlllist=[]
    for filename in filelist:
        with open(filename) as f:
            textlist.extend(json.load(f))
    for i in range(len(textlist)):
        for j in range(len(textlist[i])):
            textlist[i][j]=textlist[i][j][0:2]
            conlllist.append(textlist[i][j][0]+' '+textlist[i][j][1]+'\n')
        conlllist.append('\n')
    with open(writefilename+'.json', 'w+') as g:
        json.dump(textlist, g)
    with open(writefilename+'.conll', 'w+') as h:
        h.writelines(conlllist)

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
    check_correctness(fnames)







if __name__ == '__main__':
    #build_train_file_from_lst_file('../../tf_neiss_test/lists/train_arendt.lst','train_arendt.json')
    build_whole_file_conll_json(['train_arendt.json','val_arendt.json'],'arendt')
    #check_correctness('arendt.json')
    #check_correctness_in_list_file()

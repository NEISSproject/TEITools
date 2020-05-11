from tei_parser import uja_tei_file
import os

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

if __name__ == '__main__':
    build_ner_statistics('../data_040520/briefe')


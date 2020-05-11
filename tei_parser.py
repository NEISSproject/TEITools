from bs4 import BeautifulSoup
import re

class uja_tei_file():

    def __init__(self, filename):
        self._allowed_tags={'rs':['person','city','ground','water','org'],'persName':[],'persname':[],'placeName':['city','ground','water'],'placename':['city','ground','water'],'orgName':[],'orgname':[],'date':[]}
        self._text,self._tagged_text,self._statistics=self._get_text_and_statistics(filename)

    def _add_content_to_statistics(self,content,statistics,content_text_list):
        tagkey=content.name
        tagtext=""
        for i in range(len(content_text_list)):
            if i>0:
                tagtext=tagtext+' '
            tagtext=tagtext+content_text_list[i]
        if content.attrs is not None and 'subtype' in content.attrs.keys():
            tagkey=tagkey+content['subtype']
        if tagkey not in statistics.keys():
            statistics[tagkey]=[1,[tagtext]]
        else:
            statistics[tagkey][0]+=1
            statistics[tagkey][1].append(tagtext)
        return statistics,tagkey

    def _merge_statistics(self,firststatistics,secondstatistics):
        for key in secondstatistics.keys():
            if key in firststatistics.keys():
                firststatistics[key][0]+=secondstatistics[key][0]
                firststatistics[key][1]+=secondstatistics[key][1]
            else:
                firststatistics[key]=secondstatistics[key]
        return firststatistics


    def _get_text_from_contentlist(self,contentlist):
        text_list=[]
        tagged_text_list=[]
        statistics={}
        for pagecontent in contentlist:
            if pagecontent.name not in ['lb','pb'] and pagecontent!='\n' and str(pagecontent.__class__.__name__)!='Comment':
                if pagecontent.name=='app' and pagecontent.lem is not None:
                    text_list_to_add,tagged_text_list_to_add,statistics_to_add=self._get_text_from_contentlist(pagecontent.lem.contents)
                    text_list=text_list+text_list_to_add
                    tagged_text_list=tagged_text_list+tagged_text_list_to_add
                    statistics=self._merge_statistics(statistics,statistics_to_add)
                elif pagecontent.name is not None and not (pagecontent.name in self._allowed_tags.keys() and (len(self._allowed_tags[pagecontent.name])==0
                                                                                                              or ('subtype' in pagecontent.attrs.keys() and pagecontent.attrs['subtype'] in self._allowed_tags[pagecontent.name]))):
                    text_list_to_add,tagged_text_list_to_add,statistics_to_add=self._get_text_from_contentlist(pagecontent.contents)
                    text_list=text_list+text_list_to_add
                    tagged_text_list=tagged_text_list+tagged_text_list_to_add
                    statistics=self._merge_statistics(statistics,statistics_to_add)
                    if pagecontent.name == 'address':
                        text_list=text_list+[' <linebreak>\n']
                        tagged_text_list=tagged_text_list+[' <linebreak>\n']
                elif pagecontent.name is None:
                    text_list.append(pagecontent)
                    tagged_text_list.append(pagecontent)
                else:
                    text_list_to_add,tagged_text_list_to_add,statistics_to_add=self._get_text_from_contentlist(pagecontent.contents)
                    text_list=text_list+text_list_to_add
                    statistics,tagname=self._add_content_to_statistics(pagecontent,statistics,text_list_to_add)
                    tagged_text_list=tagged_text_list+['<'+tagname+'>']+tagged_text_list_to_add+['</'+tagname+'>']
                    statistics=self._merge_statistics(statistics,statistics_to_add)
                        #text_list.append(pagecontent.text+' ')
            elif pagecontent.name not in ['lb','pb']:
                text_list.append(' ')
                tagged_text_list.append(' ')
        text_list.append(' ')
        tagged_text_list.append(' ')
        return text_list, tagged_text_list, statistics

    def _get_text_and_statistics(self, filename):
        with open(filename, 'r') as tei:
            soup = BeautifulSoup(tei, 'lxml')
        textcontent=soup.find('text')
        text_list=[]
        tagged_text_list=[]
        statistics={}
        pages = textcontent.find_all(['opener','p','closer'])
        for page in pages:
            if page.name=='closer':
                text_list=text_list+[' <linebreak>\n']
                tagged_text_list=tagged_text_list+[' <linebreak>\n']
            new_text_list,new_tagged_text_list,new_statistics=self._get_text_from_contentlist(page.contents)
            text_list=text_list+new_text_list
            tagged_text_list=tagged_text_list+new_tagged_text_list
            statistics=self._merge_statistics(statistics,new_statistics)
            if page.name=='opener':
                text_list=text_list+[' <linebreak>\n']
                tagged_text_list=tagged_text_list+[' <linebreak>\n']
        text=""
        for element in text_list:
            text=text+str(element)
        text=" ".join(re.split(r"\s+", text))
        text=text.replace('<linebreak>','\n')
        tagged_text=""
        for element in tagged_text_list:
            tagged_text=tagged_text+str(element)
        tagged_text=" ".join(re.split(r"\s+", tagged_text))
        tagged_text=tagged_text.replace('<linebreak>','\n')
        return text, tagged_text, statistics

    def get_text(self):
        return self._text
    def get_tagged_text(self):
        return self._tagged_text
    def get_statistics(self):
        return self._statistics
    def print_statistics(self):
        for key in self._statistics.keys():
            print(key,self._statistics[key])

if __name__ == '__main__':
    #brief=uja_tei_file('../data_040520/briefe/0003_060000.xml')
    brief=uja_tei_file('../data_040520/briefe/0094_060083.xml')
    print(brief.get_tagged_text())
    brief.print_statistics()



from bs4 import BeautifulSoup
import re
import spacy
import json

class uja_tei_file():

    def __init__(self, filename,nlp=None):
        self._allowed_tags={'rs':['person','city','ground','water','org'],'persName':[],'persname':[],'placeName':['city','ground','water'],'placename':['city','ground','water'],'orgName':[],'orgname':[],'date':[]}
        self._pagelist=[]
        self._soup=None
        self._text,self._tagged_text,self._statistics=self._get_text_and_statistics(filename)
        self._tagged_text_line_list=[]

        if nlp is not None:
            self._nlp=nlp
        else:
            self._nlp=spacy.load('de_core_news_sm')


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
                    tagged_text_list=tagged_text_list+[' <'+tagname+'> ']+tagged_text_list_to_add+[' </'+tagname+'> ']
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
            self._soup = BeautifulSoup(tei, 'lxml')

        textcontent=self._soup.find('text')
        text_list=[]
        tagged_text_list=[]
        statistics={}
        pages = textcontent.find_all(['opener','p','closer'])
        for page in pages:
            self._pagelist.append({'name':page.name,'page':page})
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
        return text,tagged_text, statistics

    def build_tagged_text_line_list(self):
        cur_tag='O' #O is the sign for without tag
        tagged_text_lines=self.get_tagged_text().split('\n')
        #Build Mapping Word to Tag
        for tagged_text_line in tagged_text_lines:
            cur_line_list=[]
            tagged_text_list=tagged_text_line.split(' ')
            for text_part in tagged_text_list:
                if text_part.startswith('<') and text_part.endswith('>'):
                    if text_part[1]=='/':
                        cur_tag='O' #O is the sign for without tag
                    else:
                        cur_tag=text_part[1:-1]
                elif text_part is not None and text_part!='':
                    #Sentence extraction doesn't work for capitalized words, that is why we use the following
                    if text_part.upper()==text_part:
                        cur_line_list.append([text_part.lower(),cur_tag,1])
                    else:
                        cur_line_list.append([text_part,cur_tag,0])
            self._tagged_text_line_list.append(cur_line_list)
        #Seperate sentences with the help of spacy
        for i in range(len(self._tagged_text_line_list)):
            #print(self._tagged_text_line_list[i])
            cur_line_text=""
            for j in range(len(self._tagged_text_line_list[i])):
                if j>0:
                    cur_line_text+=' '
                cur_line_text+=self._tagged_text_line_list[i][j][0]
            #print('cur line text: ',cur_line_text)
            tokens=self._nlp(cur_line_text)
            k=0
            new_line_list=[]
            cur_word=""
            for sent in tokens.sents:
                space_before=False
                for wordindex in range(len(sent)):
                    cur_tag_element=self._tagged_text_line_list[i][k]
                    cur_word+=str(sent[wordindex])
                    word_to_insert=str(sent[wordindex])
                    if cur_tag_element[2]==1:
                       word_to_insert=word_to_insert.upper()
                    if wordindex==0:
                        new_line_list.append([word_to_insert,cur_tag_element[1],2])
                    elif space_before:
                        new_line_list.append([word_to_insert,cur_tag_element[1],0])
                    else:
                        new_line_list.append([word_to_insert,cur_tag_element[1],1])
                    if cur_word==cur_tag_element[0]:
                        space_before=True
                        cur_word=""
                        k+=1
                    else:
                        space_before=False
            self._tagged_text_line_list[i]=new_line_list
        #for line_list in self._tagged_text_line_list:
        #    print(line_list)
        return self._tagged_text_line_list

    def get_text(self):
        return self._text
    def get_tagged_text(self):
        return self._tagged_text
    def get_tagged_text_line_list(self):
        return self._tagged_text_line_list
    def get_statistics(self):
        return self._statistics
    def print_statistics(self):
        for key in self._statistics.keys():
            print(key,self._statistics[key])

    def _write_content(self,content,predicted_data,contentindex,wordindex,already_tagged):
        cur_content_index=0
        for subcontent in content.contents:
            if subcontent.name not in ['lb','pb'] and subcontent!='\n' and str(subcontent.__class__.__name__)!='Comment':
                if subcontent.name=='app' and subcontent.lem is not None:
                    contentindex,wordindex=self._write_content(subcontent.lem,predicted_data,contentindex,wordindex,already_tagged)
                elif subcontent.name is not None and not (subcontent.name in self._allowed_tags.keys() and (len(self._allowed_tags[subcontent.name])==0
                                                                                                              or ('subtype' in subcontent.attrs.keys() and subcontent.attrs['subtype'] in self._allowed_tags[subcontent.name]))):
                    contentindex,wordindex=self._write_content(subcontent,predicted_data,contentindex,wordindex,True)
                elif subcontent.name is None:
                    if subcontent is not None and subcontent!="":
                        for i in range(len(subcontent)):
                            #if contentindex>=len(predicted_data)-1:
                            #    print('Hallo')
                            if contentindex<len(predicted_data) and len(self._cur_word)>len(predicted_data[contentindex][wordindex][0]):
                                print("Error: Predicted data doesn't match TEI-File!")
                                raise ValueError
                            if subcontent[i]==self._cur_pred_word[self._cur_pred_index]:
                                self._cur_pred_index+=1
                                self._cur_word=self._cur_word+subcontent[i]
                            elif i>0 and self._cur_pred_index>0:
                                print("Error: Predicted data doesn't match TEI-File!")
                                raise ValueError
                            if self._cur_word==self._cur_pred_word:
                                if len(predicted_data[contentindex])-1>wordindex:
                                    wordindex+=1
                                else:
                                    wordindex=0
                                    contentindex+=1
                                self._cur_word=""
                                if len(predicted_data)>contentindex:
                                    self._cur_pred_word=predicted_data[contentindex][wordindex][0]
                                self._cur_pred_index=0
                        #print(subcontent)
                else:
                    contentindex,wordindex=self._write_content(subcontent,predicted_data,contentindex,wordindex,already_tagged)
            cur_content_index+=1
        return contentindex,wordindex


    def write_predicted_ner_tags(self,predicted_data):
        #print(len(predicted_data))
        #for i in range(len(predicted_data)):
        #    print(len(predicted_data[i]))
        contentindex=0
        wordindex=0
        self._cur_word=""
        self._cur_pred_word=predicted_data[0][0][0]
        self._cur_pred_index=0
        for page in self._pagelist:
            #print(page)
            contentindex,wordindex=self._write_content(page['page'],predicted_data,contentindex,wordindex,False)
            #print(contentindex,wordindex)





def reconstruct_text(text_list,sentences_per_line=False,with_tags=False):
    text=''
    for text_line in text_list:
        first_line_word=True
        for text_part in text_line:
            if first_line_word:
                first_line_word=False
            elif text_part[2]==0:
                text+=' '
            elif sentences_per_line and text_part[2]==2:
                text+='\n'
            elif text_part[2]==2:
                text+=' '
            text+=text_part[0]
            if with_tags and text_part[1]!='O':
                text+='#'+text_part[1]
        text+='\n'
    return text

def test_rewrite_pred_into_tei():
    nlp =spacy.load('de_core_news_sm')
    #pred_0084_060075.xml.json
    brief=uja_tei_file('../data_040520/briefe/0178_060169.xml',nlp)
    with open('../data_040520/predicted_data3/pred_0178_060169.xml.json') as f:
        predicted_data=json.load(f)
    print(reconstruct_text(predicted_data,True))
    brief.write_predicted_ner_tags(predicted_data)
    print(brief._soup.find('text'))

def test_write():
    nlp =spacy.load('de_core_news_sm')
    #pred_0084_060075.xml.json
    brief=uja_tei_file('../data_040520/briefe/0178_060169.xml',nlp)
    for element in brief._soup.find('text').findChildren():
        print(element.name,element.string)


def test_write2():

    soup = BeautifulSoup('<html><div>abcdef</div><body>Hallo Welt! <p>Hello, World!</p>  nochmal </body></html>','lxml')
    print(soup.html.p)
    for content in soup.html.findChildren():
        print(content.name,content.string,content.contents)
        if content.name=='p':
            content.string='Hello '
        elif content.name=='body':
            begin=soup.new_string('Hallo ')
            content.contents[1].replace_with(begin)
            #content.contents[1]='Hallo'
            org=soup.new_tag('orgname',type='real',checked=False)
            org.string='Welt'
            content.insert(2,org)
            rest=soup.new_string('! ')
            content.insert(3,rest)
        #print(content)
    org=soup.new_tag('orgname',type='real',checked=False)
    org.string='World'
    soup.html.p.insert(len(soup.html.p),org)
    rest=soup.new_string('!')
    soup.html.p.insert(len(soup.html.p),rest)
    print(soup)
    for content in soup.html.findChildren():
        print(content.name,content.string,content.contents)


if __name__ == '__main__':
    #brief=uja_tei_file('../data_040520/briefe/0003_060000.xml')
    #brief=uja_tei_file('../data_040520/briefe/0094_060083.xml')
    #print(brief.get_text())
    #print(reconstruct_text(brief.build_tagged_text_line_list(),True,False))
    #brief.print_statistics()
    #test_rewrite_pred_into_tei()
    test_write2()






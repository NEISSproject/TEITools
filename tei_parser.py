from bs4 import BeautifulSoup
import re
import spacy
import json

class uja_tei_text_parser():
    def __init__(self, filename):
        self._space_codes=['&#x2008;']
        self._allowed_tags={'rs':['subtype="person"','subtype="city"','subtype="ground"','subtype="water"','subtype="org"'],'persName':[],'persname':[],'placeName':['subtype="city"','subtype="ground"','subtype="water"'],'placename':['subtype="city"','subtype="ground"','subtype="water"'],'orgName':[],'orgname':[],'date':[]}
        with open(filename, 'r') as f:
            tei=f.read()
        begintextindex=tei.find('<text ')
        begintextindex2=tei.find('<text>')
        if begintextindex<0:
            begintextindex=begintextindex2
        endtextindex=begintextindex+tei[begintextindex:].find('>')
        self._begin=tei[0:endtextindex+1]
        self._end='</text>'+tei[tei.find('</text>')+7:]
        self._text=tei[endtextindex+1:tei.find('</text>')]
        #print(self._text)
        self._build_text_tree()

    def _get_tag_name(self,cur_tag_content):
        spaceindex=cur_tag_content.find(' ')
        if spaceindex>0:
            return cur_tag_content[:spaceindex]
        return cur_tag_content

    def _getinnersametagindex(self,cur_text,tag_name):
        innersametagindex=cur_text.find('<'+tag_name+' ')
        innersametagindex2=cur_text.find('<'+tag_name+'>')
        if innersametagindex<0 or (innersametagindex2>=0 and innersametagindex2<innersametagindex):
            innersametagindex=innersametagindex2
        #Check that it is not part of a comment
        commentbeginindex=cur_text.find('<!--')
        if commentbeginindex>0 and commentbeginindex<innersametagindex:
            commentendindex=commentbeginindex+4+cur_text[commentbeginindex+4:].find('-->')
            if commentendindex>innersametagindex:
                newinnersametagindex=self._getinnersametagindex(cur_text[commentendindex+2:],tag_name)
                if newinnersametagindex>0:
                    innersametagindex=commentendindex+2+newinnersametagindex
                else:
                    innersametagindex=newinnersametagindex
        if innersametagindex>=0:
            innersametagstopindex=innersametagindex+cur_text[innersametagindex:].find('>')
            if cur_text[innersametagstopindex-1]=='/':
                newinnersametagindex=self._getinnersametagindex(cur_text[innersametagstopindex:],tag_name)
                if newinnersametagindex>0:
                    innersametagindex=innersametagstopindex+newinnersametagindex
                else:
                    innersametagindex=newinnersametagindex
        return innersametagindex

    def _find_endstartindex(self,cur_text,tag_name):
        endstartindex=cur_text.find('</'+tag_name+'>')
        if endstartindex<0:
            return -1
        innersametagindex=self._getinnersametagindex(cur_text,tag_name)
        #Relevant if the same tag is nested
        if innersametagindex>=0 and innersametagindex<endstartindex:
            newstartindex= innersametagindex +2 + self._find_endstartindex(cur_text[innersametagindex+2:],tag_name)
            return newstartindex+2+self._find_endstartindex(cur_text[newstartindex+2:],tag_name)
        return endstartindex

    def _extract_next_tag(self,cur_text):
        beginstartindex=cur_text.find('<')
        if beginstartindex>=0:
            beginstopindex=cur_text.find('>')
            if beginstopindex<beginstartindex:
                print("Error: CheckSyntax")
                raise ValueError
            tag_name=self._get_tag_name(cur_text[beginstartindex+1:beginstopindex])
            #if tag_name in ['p','opener','closer','pb','lem']:
            #    print('Stop')
            if tag_name=='!--':
                beginstopindex=cur_text.find('-->')+2
            endstartindex=beginstopindex+self._find_endstartindex(cur_text[beginstopindex:],tag_name)#cur_text.find('</'+tag_name+'>')
            if cur_text[beginstopindex-1]=='/' or tag_name=='!--':
                return tag_name, beginstartindex,beginstopindex,-1,-1
            if endstartindex<beginstopindex:
                print("Error: CheckSyntax")
                raise ValueError
            endstopindex=endstartindex+len(tag_name)+2
            return tag_name, beginstartindex,beginstopindex,endstartindex,endstopindex

        else:
            return None,0,0,0,0

    def _build_subtexttaglist(self,cur_text):
        tag_name, beginstartindex,beginstopindex,endstartindex,endstopindex=self._extract_next_tag(cur_text)
        if tag_name is not None:
            returnlist=[]
            if beginstartindex>0:
                returnlist.append(cur_text[:beginstartindex])
            tag_dict={'name':tag_name,'tagbegin':cur_text[beginstartindex:beginstopindex+1]}
            if endstartindex>0:
                tag_dict['tagend']=cur_text[endstartindex:endstopindex+1]
                if beginstopindex+1<endstartindex:
                    tag_dict['tagcontent']=self._build_subtexttaglist(cur_text[beginstopindex+1:endstartindex])
                returnlist.append(tag_dict)
                if endstopindex+1<len(cur_text):
                    returnlist.append(self._build_subtexttaglist(cur_text[endstopindex+1:]))
            elif beginstopindex+1<len(cur_text):
                returnlist.append(tag_dict)
                returnlist.append(self._build_subtexttaglist(cur_text[beginstopindex+1:]))
            else:
                returnlist.append(tag_dict)
            return returnlist
        else:
            return cur_text


    def _build_text_tree(self):
        self._text_tree=self._build_subtexttaglist(self._text)
        #print(self._text_tree)

    def _get_tree_text(self,cur_element):
        if isinstance(cur_element,dict):
            text=cur_element['tagbegin']
            if 'tagcontent' in cur_element.keys():
                text+=self._get_tree_text(cur_element['tagcontent'])
            if 'tagend' in cur_element.keys():
                text+=cur_element['tagend']
            return text
        elif isinstance(cur_element,list):
            text=""
            for element in cur_element:
                text=text+self._get_tree_text(element)
            return text
        elif isinstance(cur_element,str):
            return cur_element

    def refresh_text_by_tree(self):
        self._text=self._get_tree_text(self._text_tree)
        #print(self.get_tei_file_string())

    def get_tei_file_string(self):
        return self._begin+self._text+self._end

    def write_back_to_file(self,outputpath):
        #print(self._text_tree)
        self.refresh_text_by_tree()
        with open(outputpath, 'w') as file:
            file.write(self.get_tei_file_string())

    def _has_subtype(self,tagname,tagbegin):
        for subtype in self._allowed_tags[tagname]:
            if tagbegin.find(subtype)>=0:
                return True
        return False

    def _merge_tags_to_insert(self,ins_tag,textstring):
        merged_tags=[]
        last_tag={'tag':'X','begin':0,'end':0}
        for tag in ins_tag:
            #print('alt',tag)
            if last_tag['tag']==tag['tag'] and \
                    (last_tag['end']==tag['begin'] or (last_tag['end']+1==tag['begin'] and textstring[last_tag['end']] in (' ','-'))):
                last_tag={'tag':last_tag['tag'],'begin':last_tag['begin'],'end':tag['end']}
            else:
                if last_tag['tag']!='X':
                    merged_tags.append(last_tag)
                last_tag=tag
        if last_tag['tag']!='X':
            merged_tags.append(last_tag)
        #print('neu',merged_tags)
        return merged_tags

    def _write_textstring(self,textstring,predicted_data,already_tagged):
        if textstring is not None and textstring!="":
            ins_tag=[]
            ignore_char_until=0
            for i in range(len(textstring)):
                if i<ignore_char_until:
                    continue
                if self._contentindex<len(predicted_data) and len(self._cur_word)>len(predicted_data[self._contentindex][self._wordindex][0]):
                    print("Error: Predicted data doesn't match TEI-File!")
                    raise ValueError
                if textstring[i]==self._cur_pred_word[self._cur_pred_index]:
                    self._cur_pred_index+=1
                    self._cur_word=self._cur_word+textstring[i]
                elif textstring[i]=='&': #Special handling for html unicode characters
                    unicode_end_index=textstring[i:].find(';')
                    ignore_char_until=i+unicode_end_index+1
                    if textstring[i:ignore_char_until] not in self._space_codes:
                        self._cur_pred_index+=1
                        self._cur_word=self._cur_word+self._cur_pred_word[len(self._cur_word)]

                elif i>0 and self._cur_pred_index>0:
                    print("Error: Predicted data doesn't match TEI-File!")
                    raise ValueError
                if self._cur_word==self._cur_pred_word:
                    if already_tagged==False and predicted_data[self._contentindex][self._wordindex][1]!='O':
                        ins_tag.append({'tag':predicted_data[self._contentindex][self._wordindex][1],'begin':i-len(self._cur_pred_word)+1,'end':i+1})
                    if len(predicted_data[self._contentindex])-1>self._wordindex:
                        self._wordindex+=1
                    else:
                        self._wordindex=0
                        self._contentindex+=1
                        #print(self._contentindex)
                    self._cur_word=""
                    if len(predicted_data)>self._contentindex:
                        self._cur_pred_word=predicted_data[self._contentindex][self._wordindex][0]
                        #print(self._cur_pred_word)
                    self._cur_pred_index=0
            #print(subcontent)
        if len(ins_tag)>0:
            #print(content.contents)
            ins_tag=self._merge_tags_to_insert(ins_tag,textstring)
            addindex=0
            for tag in ins_tag:
                #print(tag,textstring[:tag['begin']+addindex],'##',textstring[tag['begin']+addindex:tag['end']+addindex],'##',textstring[tag['end']+addindex:])
                string_to_tag=textstring[tag['begin']+addindex:tag['end']+addindex]
                if tag['tag']=='pers':
                    new_tagged_string='<persName type="real" checked="False">'+string_to_tag+'</persName>'
                elif tag['tag']=='date':
                    new_tagged_string='<date type="real" checked="False">'+string_to_tag+'</date>'
                elif tag['tag']=='org':
                    new_tagged_string='<orgName type="real" checked="False">'+string_to_tag+'</orgName>'
                elif tag['tag']=='city':
                    new_tagged_string='<placeName type="real" subtype="city" checked="False">'+string_to_tag+'</placeName>'
                elif tag['tag']=='water':
                    new_tagged_string='<placeName type="real" subtype="water" checked="False">'+string_to_tag+'</placeName>'
                elif tag['tag']=='ground':
                    new_tagged_string='<placeName type="real" subtype="ground" checked="False">'+string_to_tag+'</placeName>'
                else:
                    new_tagged_string='<unknownName type="real" checked="False">'+string_to_tag+'</unknownName>'
                textstring=textstring[:tag['begin']+addindex]+new_tagged_string+textstring[tag['end']+addindex:]
                addindex=addindex+len(new_tagged_string)-len(string_to_tag)
        return textstring

    def _write_tag_dict(self,tag_dict,predicted_data,already_tagged):
        if tag_dict['name'] in ['note','rdg']:
            return tag_dict
        elif tag_dict['name']=='app':
            if 'tagcontent' in tag_dict.keys() and isinstance(tag_dict['tagcontent'],list):
                if len(tag_dict['tagcontent'])>0:
                    if isinstance(tag_dict['tagcontent'][0],dict):
                        if tag_dict['tagcontent'][0]['name']=='lem' and 'tagcontent' in tag_dict['tagcontent'][0].keys():
                            tag_dict['tagcontent'][0]=self._write_tag_dict(tag_dict['tagcontent'][0],predicted_data,already_tagged)
            elif isinstance(tag_dict['tagcontent'],str):
                tag_dict['tagcontent']=self._write_textstring(tag_dict['tagcontent'],predicted_data,already_tagged)
        else:
            if tag_dict['name'] in self._allowed_tags.keys() and (len(self._allowed_tags[tag_dict['name']])==0 or self._has_subtype(tag_dict['name'],tag_dict['tagbegin'])):
                tagged=True
            else:
                tagged=already_tagged
            if 'tagcontent' in tag_dict.keys():
                if isinstance(tag_dict['tagcontent'],list):
                    tag_dict['tagcontent']=self._write_contentlist(tag_dict['tagcontent'],predicted_data,tagged)
                elif isinstance(tag_dict['tagcontent'],dict):
                    tag_dict['tagcontent']=self._write_tag_dict(tag_dict['tagcontent'],predicted_data,tagged)
                elif isinstance(tag_dict['tagcontent'],str):
                    tag_dict['tagcontent']=self._write_textstring(tag_dict['tagcontent'],predicted_data,tagged)
        return tag_dict

    def _write_contentlist(self,contentlist,predicted_data,already_tagged):
        for contentindex in range(len(contentlist)):
            if isinstance(contentlist[contentindex],list):
                contentlist[contentindex]=self._write_contentlist(contentlist[contentindex],predicted_data,already_tagged)
            elif isinstance(contentlist[contentindex],dict):
                contentlist[contentindex]=self._write_tag_dict(contentlist[contentindex],predicted_data,already_tagged)
            elif isinstance(contentlist[contentindex],str):
                contentlist[contentindex]=self._write_textstring(contentlist[contentindex],predicted_data,already_tagged)
        return contentlist


    def write_predicted_ner_tags(self,predicted_data):
        self._contentindex=0
        self._wordindex=0
        self._cur_word=""
        self._cur_pred_word=predicted_data[0][0][0]
        self._cur_pred_index=0
        self._write_contentlist(self._text_tree,predicted_data,False)
        if len(predicted_data)>self._contentindex:
            print('Error: Predicted Data does not match the text of the xml file')
            raise ValueError



class uja_tei_file():

    def __init__(self, filename,nlp=None):
        self._allowed_tags={'rs':['person','city','ground','water','org'],'persName':[],'persname':[],'placeName':['city','ground','water'],'placename':['city','ground','water'],'orgName':[],'orgname':[],'date':[]}
        self._pagelist=[]
        self._soup=None
        self._note_list=[]
        self._tagged_note_list=[]
        self._note_statistics={}
        self._text,self._tagged_text,self._statistics,self._notes, self._tagged_notes=self._get_text_and_statistics(filename)
        self._tagged_text_line_list=[]
        self._tagged_note_line_list=[]


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
            if pagecontent.name not in ['lb','pb','note','rdg'] and pagecontent!='\n' and str(pagecontent.__class__.__name__)!='Comment':
                if pagecontent.name=='app' and pagecontent.lem is not None:
                    text_list_to_add,tagged_text_list_to_add,statistics_to_add=self._get_text_from_contentlist(pagecontent.lem.contents)
                    text_list=text_list+text_list_to_add
                    tagged_text_list=tagged_text_list+tagged_text_list_to_add
                    statistics=self._merge_statistics(statistics,statistics_to_add)
                    if pagecontent.note is not None:
                        note_list_to_add,tagged_note_list_to_add,note_statistics_to_add=self._get_text_from_contentlist(pagecontent.note.contents)
                        #print(note_list_to_add,tagged_note_list_to_add,note_statistics_to_add)
                        self._note_list=self._note_list+note_list_to_add
                        self._tagged_note_list=self._tagged_note_list+tagged_note_list_to_add
                        self._note_statistics=self._merge_statistics(self._note_statistics,note_statistics_to_add)
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
            elif pagecontent.name=='note':
                note_list_to_add,tagged_note_list_to_add,note_statistics_to_add=self._get_text_from_contentlist(pagecontent.contents)
                #print(note_list_to_add,tagged_note_list_to_add,note_statistics_to_add)
                self._note_list=self._note_list+note_list_to_add
                self._tagged_note_list=self._tagged_note_list+tagged_note_list_to_add
                self._note_statistics=self._merge_statistics(self._note_statistics,note_statistics_to_add)
            elif pagecontent.name not in ['lb','pb']:
                text_list.append(' ')
                tagged_text_list.append(' ')
        text_list.append(' ')
        tagged_text_list.append(' ')
        return text_list, tagged_text_list, statistics

    def _get_text_and_statistics(self, filename):
        if self._soup is None:
            with open(filename, 'r') as tei:
                self._soup = BeautifulSoup(tei,'xml')#'html.parser' )#'lxml')
        textcontent=self._soup.find('text')
        text_list=[]
        tagged_text_list=[]
        statistics={}
        self._note_list=[]
        self._tagged_note_list=[]
        self._note_statistics={}
        #pages = textcontent.find_all(['opener','p','closer','postscript'])
        for page in textcontent.find('body').contents:
            if page.name is not None:
                if page.name=='app' and page.lem is not None:
                    self._pagelist.append({'name':page.lem.name,'page':page.lem})
                else:
                    self._pagelist.append({'name':page.name,'page':page})
                if page.name=='closer' or page.name=='postscript':
                    text_list=text_list+[' <linebreak>\n']
                    tagged_text_list=tagged_text_list+[' <linebreak>\n']
                if page.name=='app' and page.lem is not None:
                    new_text_list,new_tagged_text_list,new_statistics=self._get_text_from_contentlist(page.lem.contents)
                    if page.note is not None:
                        note_list_to_add,tagged_note_list_to_add,note_statistics_to_add=self._get_text_from_contentlist(page.note.contents)
                        #print(note_list_to_add,tagged_note_list_to_add,note_statistics_to_add)
                        self._note_list=self._note_list+note_list_to_add
                        self._tagged_note_list=self._tagged_note_list+tagged_note_list_to_add
                        self._note_statistics=self._merge_statistics(self._note_statistics,note_statistics_to_add)
                else:
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
        notes=""
        for element in self._note_list:
            notes=notes+str(element)
        notes=" ".join(re.split(r"\s+", notes))
        notes=notes.replace('<linebreak>','\n')
        tagged_notes=""
        for element in self._tagged_note_list:
            tagged_notes=tagged_notes+str(element)
        tagged_notes=" ".join(re.split(r"\s+", tagged_notes))
        tagged_notes=tagged_notes.replace('<linebreak>','\n')
        return text,tagged_text, statistics, notes, tagged_notes

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

    def build_tagged_note_line_list(self):
        cur_tag='O' #O is the sign for without tag
        tagged_note_lines=self.get_tagged_notes().split('\n')
        #Build Mapping Word to Tag
        for tagged_note_line in tagged_note_lines:
            cur_line_list=[]
            tagged_note_list=tagged_note_line.split(' ')
            for note_part in tagged_note_list:
                if note_part.startswith('<') and note_part.endswith('>'):
                    if note_part[1]=='/':
                        cur_tag='O' #O is the sign for without tag
                    else:
                        cur_tag=note_part[1:-1]
                elif note_part is not None and note_part!='':
                    #Sentence extraction doesn't work for capitalized words, that is why we use the following
                    if note_part.upper()==note_part:
                        cur_line_list.append([note_part.lower(),cur_tag,1])
                    else:
                        cur_line_list.append([note_part,cur_tag,0])
            self._tagged_note_line_list.append(cur_line_list)
        #Seperate sentences with the help of spacy
        for i in range(len(self._tagged_note_line_list)):
            #print(self._tagged_text_line_list[i])
            cur_line_note=""
            for j in range(len(self._tagged_note_line_list[i])):
                if j>0:
                    cur_line_note+=' '
                cur_line_note+=self._tagged_note_line_list[i][j][0]
            #print('cur line text: ',cur_line_text)
            tokens=self._nlp(cur_line_note)
            k=0
            new_line_list=[]
            cur_word=""
            for sent in tokens.sents:
                space_before=False
                for wordindex in range(len(sent)):
                    cur_tag_element=self._tagged_note_line_list[i][k]
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
            self._tagged_note_line_list[i]=new_line_list
        #for line_list in self._tagged_text_line_list:
        #    print(line_list)
        return self._tagged_note_line_list

    def get_text(self):
        return self._text
    def get_tagged_text(self):
        return self._tagged_text
    def get_notes(self):
        return self._notes
    def get_tagged_notes(self):
        return self._tagged_notes
    def get_tagged_text_line_list(self):
        return self._tagged_text_line_list
    def get_tagged_note_line_list(self):
        return self._tagged_note_line_list
    def get_statistics(self):
        return self._statistics
    def print_statistics(self):
        for key in self._statistics.keys():
            print(key,self._statistics[key])
    def get_note_statistics(self):
        return self._note_statistics
    def print_note_statistics(self):
        for key in self._note_statistics.keys():
            print(key,self._note_statistics[key])

    def _merge_tags_to_insert(self,ins_tag,cont_list):
        merged_tags=[]
        last_tag={'tag':'X','begin':0,'end':0,'soap_content_index':-1}
        for tag in ins_tag:
            #print('alt',tag)
            if last_tag['soap_content_index']==tag['soap_content_index'] and last_tag['tag']==tag['tag'] and \
                    (last_tag['end']==tag['begin'] or (last_tag['end']+1==tag['begin'] and cont_list[tag['soap_content_index']][last_tag['end']] in (' ','-'))):
                last_tag={'tag':last_tag['tag'],'begin':last_tag['begin'],'end':tag['end'],'soap_content_index':tag['soap_content_index']}
            else:
                if last_tag['soap_content_index']!=-1:
                    merged_tags.append(last_tag)
                last_tag=tag
        if last_tag['soap_content_index']!=-1:
            merged_tags.append(last_tag)
        #print('neu',merged_tags)
        return merged_tags

    def _write_content(self,content,predicted_data,contentindex,wordindex,already_tagged):
        cur_content_index=0
        ins_tag=[]
        for subcontent in content.contents:
            if subcontent.name not in ['lb','pb','note','rdg'] and subcontent!='\n' and str(subcontent.__class__.__name__)!='Comment':
                if subcontent.name=='app' and subcontent.lem is not None:
                    contentindex,wordindex=self._write_content(subcontent.lem,predicted_data,contentindex,wordindex,already_tagged)
                elif subcontent.name is not None and not (subcontent.name in self._allowed_tags.keys() and (len(self._allowed_tags[subcontent.name])==0
                                                                                                              or ('subtype' in subcontent.attrs.keys() and subcontent.attrs['subtype'] in self._allowed_tags[subcontent.name]))):
                    contentindex,wordindex=self._write_content(subcontent,predicted_data,contentindex,wordindex,already_tagged)
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
                                if already_tagged==False and predicted_data[contentindex][wordindex][1]!='O':
                                    ins_tag.append({'tag':predicted_data[contentindex][wordindex][1],'begin':i-len(self._cur_pred_word)+1,'end':i+1,'soap_content_index':cur_content_index})
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
                    contentindex,wordindex=self._write_content(subcontent,predicted_data,contentindex,wordindex,True)
            cur_content_index+=1
        if len(ins_tag)>0:
            #print(content.contents)
            ins_tag=self._merge_tags_to_insert(ins_tag,content.contents)
            addindex=0
            subposition=0
            oldindex=-1
            for tag in ins_tag:
                if tag['tag']!='dateX':
                    tagcontent=content.contents[tag['soap_content_index']+addindex]
                    if tag['soap_content_index']>oldindex:
                        subposition=0
                    #print(tag,tagcontent[:tag['begin']-subposition],'##',tagcontent[tag['begin']-subposition:tag['end']-subposition],'##',tagcontent[tag['end']-subposition:])
                    begin=self._soup.new_string(tagcontent[:tag['begin']-subposition])
                    tagcontent.replace_with(begin)
                    #content.contents[1]='Hallo'
                    if tag['tag']=='pers':
                        new_tag=self._soup.new_tag('persName',type='real',checked=False)
                    elif tag['tag']=='date':
                        new_tag=self._soup.new_tag('date',type='real',checked=False)
                    elif tag['tag']=='org':
                        new_tag=self._soup.new_tag('orgName',type='real',checked=False)
                    elif tag['tag']=='city':
                        new_tag=self._soup.new_tag('placeName',type='real',checked=False,subtype="city")
                    elif tag['tag']=='water':
                        new_tag=self._soup.new_tag('placeName',type='real',checked=False,subtype="water")
                    elif tag['tag']=='ground':
                        new_tag=self._soup.new_tag('placeName',type='real',checked=False,subtype="ground")
                    else:
                        new_tag=self._soup.new_tag('UnknownName',type='real',checked=False)
                    new_tag.string=tagcontent[tag['begin']-subposition:tag['end']-subposition]
                    content.insert(tag['soap_content_index']+1+addindex,new_tag)
                    rest=self._soup.new_string(tagcontent[tag['end']-subposition:])
                    content.insert(tag['soap_content_index']+2+addindex,rest)
                    addindex+=2
                    oldindex=tag['soap_content_index']
                    subposition=tag['end']
            #print(content.contents)
        return contentindex,wordindex


    def write_predicted_ner_tags(self,predicted_data):
        contentindex=0
        wordindex=0
        self._cur_word=""
        self._cur_pred_word=predicted_data[0][0][0]
        self._cur_pred_index=0
        for page in self._pagelist:
            contentindex,wordindex=self._write_content(page['page'],predicted_data,contentindex,wordindex,False)





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
    #pred_0383_101386.xml
    #pred_0586_101039.xml.json
    #pred_0676_101124.xml.json
    brief=uja_tei_file('../data_040520/briefe/0676_101124.xml',nlp)
    with open('../data_040520/predicted_data3/pred_0676_101124.xml.json') as f:
        predicted_data=json.load(f)
    #print(reconstruct_text(predicted_data,True))
    brief.write_predicted_ner_tags(predicted_data)
    #print(brief._soup.find('text'))
    #print(brief._soup.html.body.tei)
    #tei=brief._soup.original_encoding
    #print(brief._soup)
    tei=brief._soup.prettify()
    tei=tei.replace('<tei:','<').replace('</tei:','<')
    print(tei)
    with open('../data_040520/0676_101124.xml', 'w') as file:
        file.write(tei)

def test_rewrite_pred_into_tei2():
    #pred_0084_060075.xml.json
    #pred_0383_101386.xml
    #pred_0586_101039.xml.json
    #pred_0676_101124.xml.json
    #brief=uja_tei_file('../data_040520/briefe/0676_101124.xml',nlp)
    with open('../data_040520/predicted_data3/pred_0204_060199.xml.json') as f:
        predicted_data=json.load(f)
    tei=uja_tei_text_parser('../data_040520/briefe/0204_060199.xml')
    tei.write_predicted_ner_tags(predicted_data)
    tei.refresh_text_by_tree()
    tei.write_back_to_file('../data_040520/0204_060199.xml')



if __name__ == '__main__':
    brief=uja_tei_file('../data_040520/briefe/0003_060000.xml')
    #brief=uja_tei_file('../data_040520/briefe/0188_060182.xml')
    #print(brief.get_notes())
    #print(brief.get_tagged_notes())
    #print(brief._note_statistics)
    #print(brief.build_tagged_text_line_list())
    #print(brief.build_tagged_note_line_list())
    #print(brief.print_statistics())

    #print(reconstruct_text(brief.build_tagged_note_line_list(),False,True))
    #brief.print_note_statistics()
    #test_rewrite_pred_into_tei2()
    #test_write2()











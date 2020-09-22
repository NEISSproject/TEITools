from bs4 import BeautifulSoup

class uja_tei_extractor():

    def __init__(self, filename):
        self._allowed_tags={'rs':['person','city','ground','water','org'],'persName':[],'persname':[],'placeName':['city','ground','water'],'placename':['city','ground','water'],'orgName':[],'orgname':[],'date':[]}
        with open(filename, 'r') as tei:
            self._soup = BeautifulSoup(tei,'xml')#'html.parser' )#'lxml')

    def get_person_list_from_text(self,with_rs_tags=False, only_from_text=False,showPrint=False):
        if only_from_text:
            relevant_data=self._soup.find('text')
        else:
            relevant_data=self._soup
        pers_list=relevant_data.find_all('persName')
        if with_rs_tags:
            rs_pers_list=relevant_data.find_all(name='rs',subtype='person')
        pers_list.extend(rs_pers_list)
        if showPrint:
            for person in pers_list:
                print(person)
        return pers_list

    def get_listPerson(self,showPrint=False):
        relevant_data=self._soup.find('listPerson')
        pers_list=relevant_data.find_all('persName')
        if showPrint:
            for person in pers_list:
                print(person)
        return pers_list

    def get_dnb_pers_refs(self,showPrint=False):
        pers_list=self.get_listPerson()
        refList=[]
        for person in pers_list:
            if showPrint:
                print(person.attrs['ref'])
            refList.append(person.attrs['ref'])
        return refList



if __name__ == '__main__':
    brief=uja_tei_extractor('../data_040520/briefe/0119_060109.xml')
    brief.get_person_list_from_text(with_rs_tags=True,only_from_text=True,showPrint=True)
    #brief.get_listPerson(showPrint=True)
    #brief.get_dnb_pers_refs(showPrint=True)

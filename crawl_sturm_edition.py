import requests
from bs4 import BeautifulSoup
import json

urlbrieffma = 'https://sturm-edition.de/quellen/briefe/fma.html'
urlbriefjvh='https://sturm-edition.de/quellen/briefe/jvh.html'

# gibt html code der gewünschten url zurück
def get_url_content(url):
    return requests.get(url).text

def crawl_sturm(url):
    content = get_url_content(url)
    #print(content)
    # übergebe html an beautifulsoup parser
    soup = BeautifulSoup(content, "html.parser")
    for main in soup.findAll('main',{'class': 'row content hyphenate'}):
        #print(main.contents)
        for section in main.findAll('section'):
            for element in section.contents:
                #print(element.name)
                if element.name is not None:
                    if element.name=='h4' and element.attrs['class']=='year':
                        print(element)
                        cur_year=int(element.contents[0])
                        print(cur_year)
                    if element.name=='ol':
                        for article in element.contents:
                            if article.name is not None:
                                if article.name=='li':
                                    li=article.contents[0]
                                    if li.name is not None and li.name=='a':
                                        cur_html_url=li.attrs['href']
                                        cur_xml_url='https://sturm-edition.de/api/files/' + cur_html_url[4:-4] + 'xml'
                                        tei=get_url_content(cur_xml_url)
                                        with open('../data_sturm/briefe/'+cur_html_url[4:-4] + 'xml', 'w') as file:
                                            file.write(tei)


if __name__ == "__main__":
    #print(get_url_content(urlbrieffma))
    crawl_sturm(urlbriefjvh)

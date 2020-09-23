import requests

urlessayslist = ['https://hannah-arendt-edition.net/textgrid/data/3p/III-002-aufklaerungJudenfrage.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-009-PortraitPeriodMenorah.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-012-FranzKafkaRevaluation.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-008-JewAsPariah.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-016-zionismReconsideredTS.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-004-organizedGuilt.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-014-ZionismReconsidered.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-011-FranzKafkaGewuerdigtWandlung.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-006-ImperialismRoadToSuicide.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-003-organisierteSchuldWandlung.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-005-ueberImperialismusWandlung.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-007-WhatIsExistenzPhilosophy.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-015-ZueignungJaspersTS.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-001-verborgeneTradition.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-001-FranzKafka.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-001-judenGestern.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-001-organisierteSchuld.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-001-ueberImperialismus.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-001-existenzPhilosophie.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-001-zueignungJaspers.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-017-FranzKafkaGewuerdigtRadio.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-002-aufklaerungJudenfrage.xml?lang=de'
    ,'https://hannah-arendt-edition.net/textgrid/data/3p/III-002-zionismusHeutigerSicht.xml?lang=de']

# gibt html code der gewünschten url zurück
def get_url_content(url):
    return requests.get(url).text

def crawl_arendt(urllist):
    print(len(urllist))
    for url in urllist:
        tei = get_url_content(url)
        with open('../data_hannah_arendt/'+url[51:-8], 'w') as file:
            file.write(tei)
        print(url)




if __name__ == "__main__":
    #print(get_url_content(urlessays))
    crawl_arendt(urlessayslist)

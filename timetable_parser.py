import urllib.request
from lxml import html
from bs4 import BeautifulSoup
from itertools import zip_longest


pageAddress = "https://www.lilienthal-gymnasium-berlin.de/interna/vplan/Druck_Kla.htm"

# die Webseitentypen mit bekannten URLs
pages = {
    'untis-html': ["https://www.lilienthal-gymnasium-berlin.de/interna/vplan/Druck_Kla.htm"]
}

untis_html_keys = ('lesson', 'teacher', 'subject', 'replacing_teacher', 'room',
                   'info_text', 'type_of_replacement')

# Klasse für die Webseitenobjekte


class Page(object):
    def __init__(self, url: str = pageAddress, overview=True):
        self.url = url
        # url abfragen, Code holen!
        webPage = urllib.request.urlopen(url)
        self.page = html.parse(webPage)
        # bytes = page.read()
        # self.code: str = bytes.decode('utf-8')
        webPage.close()

        self.replacements: dict = {}

        # den Websitetypen bestimmen
        for type in pages:
            if url in pages[type]:
                self.type = type
                break
            else:
                continue
        try:
            self.type
        except:
            self.type: str = None

        if self.type is not None:
            # self.beautify_code()
            self.extract_data(overview)

    # die Funktionen für die Websitetypen ausführen
    def extract_data(self, is_overview):
        if self.type is None:
            return
        elif self.type == 'untis-html':
            self.parse_untis_html()
        else:
            pass

    def parse_untis_html(self):
        # checken ob der Plan leer ist
        # if self.code.count('<table') == 1: return # alte Abfrage mit string Code

        # 2. Tabelle auswählen
        # self.code = self.code.find('<table', start=self.code.find('</table>') + 8)
        tables = self.page.findall('//center//table')
        if len(tables) == 1:
            return

        # Daten aus den Zellen extrahieren
        data_cells = {cell.text_content(): cell.get('href')
                      for cell in tables[1].iterfind('.//td/a')}
        print(data_cells)

        for class_repl in data_cells:
            link = data_cells[class_repl]
            if link.count('/') == 0:
                link = self.url.rsplit('/', 1)[0] + '/' + link
            webPage = urllib.request.urlopen(link)
            page = html.parse(webPage)
            webPage.close()

            events = page.xpath('((.//center//table)[2]/tr)[position()>1]')

            for event in events:
                cells: list = [item.text_content().strip('\n ').replace(u'\xa0', ' ')
                                if item.text_content() != u'\xa0' else None
                                for item in event.xpath('(.//td)[position()>1]')]
                replacement = dict(zip_longest(untis_html_keys, cells))

                if not class_repl in self.replacements:
                    self.replacements[class_repl] = [replacement]
                else:
                    self.replacements[class_repl].append(replacement)

    # beautifys the Code, so we don't need to double check caps, etc.

    def beautify_code(self):
        try:
            # doesnt work because we dont have self.code anymore
            self.code = BeautifulSoup(page.code, 'html.parser').prettify()
        except:
            pass


page = Page(pages['untis-html'][0])

print(page.replacements)

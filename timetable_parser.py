import urllib.request, imgkit
from lxml import html
from itertools import zip_longest


# die Webseitentypen mit bekannten URLs
pages = {
    'untis-html': ["https://www.lilienthal-gymnasium-berlin.de/interna/vplan/Druck_Kla.htm"]
}

untis_html_keys = ('lesson', 'teacher', 'subject', 'replacing_teacher', 'room',
                   'info_text', 'type_of_replacement')

page_prettifier_css = {'untis-html': '''<style type="text/css">
    @font-face {
        font-family: "ArialRounded";
        src: url("./fonts/arialrounded.woff") format("woff"),
            url("./fonts/arialrounded.woff2") format("woff2");
    }

    body, font {
        font-family: 'ArialRounded';
    }

    table:not([rules]){
        display:block;
        height:0px;
        visibility: hidden}

    table[rules] {
        background: rgba(0,0,0,0.1);
        border-collapse: separate !important;
        border-spacing: 0;
        border: 3px solid black;
        border-radius: 5px;
    }

    td {
        padding-top: 4px;
        padding-bottom: 4px;
    }

    a {
        color: #000000;
    }'''
}




# Klasse für die Webseitenobjekte
class Page(object):
    def __init__(self, url: str = pages['untis-html'][0], overview=True):
        self.url = url
        # url abfragen, Code holen!
        webPage = urllib.request.urlopen(url)
        self.page = html.parse(webPage)
        # bytes = page.read()
        # self.code: str = bytes.decode('utf-8')
        webPage.close()

        self.replacements: dict = {}
        self.times: dict = {}
        self.previews: dict = {}


        # den Websitetypen bestimmen
        self.type: str = None
        for type in pages:
            if url in pages[type]:
                self.type = type
                break
            else:
                continue

        if self.type is not None:
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
        # 2. Tabelle auswählen
        tables = self.page.findall('//center//table')
        if len(tables) == 1:
            return

        # Daten aus den Zellen extrahieren
        data_cells = {cell.text_content(): cell.get('href')
                      for cell in tables[1].iterfind('.//td/a')}

        # die Vertretungen für die einzelnen Klassen ermitteln
        for class_repl in data_cells:
            # den Link zum Plan konstruieren
            link = data_cells[class_repl]
            if link.count('/') == 0:
                link = self.url.rsplit('/', 1)[0] + '/' + link
            webPage = urllib.request.urlopen(link)
            page = html.parse(webPage)
            webPage.close()

            # Abfragen, ob der Plan neuer ist als der in unserer Datenbank
            data_time = page.xpath('(((.//center//table)[1])/tr[2])/td[last()]')[0].text_content()
            if self.times.get(class_repl) == data_time: continue # überspringen
            else:
                self.times[class_repl] = data_time

            events = page.xpath('(.//center//table)[2]/tr[position()>1]')

            self.replacements[class_repl] = []
            self.previews[class_repl] = self.get_plan_preview(page)

            # Alle Vertretungen aus der Tabelle extrahieren
            for event in events:
                cells: list = [item.text_content().strip('\n ').replace(u'\xa0', ' ')
                                if item.text_content() != u'\xa0' else None
                                for item in event.xpath('(.//td)[position()>1]')]
                replacement = dict(zip_longest(untis_html_keys, cells))

                self.replacements[class_repl].append(replacement)

        # nicht mehr vorkommene Elemente löschen
        if len(data_cells) != len(self.replacements):
            for class_repl in self.replacements:
                if not class_repl in data_cells:
                    self.replacements.pop(class_repl)
                    self.previews.pop(class_repl)
                else: continue


    def get_plan_preview(self, page) -> str:
        # unbenutzte Tabellen entfernen
        unused_tables = page.xpath('(.//center//table)[position()!=2]')
        for table in unused_tables: table.getparent().remove(table)

        # Header finden um Stylesheet einzufügen
        header = page.find('.//head')
        style = html.fromstring(page_prettifier_css[self.type]).find('.//style')
        header.insert(0, style)

        html_code: str = html.tostring(page).decode('utf-8')
        print(html_code)
        config = imgkit.config(wkhtmltoimage="C:/Program Files/wkhtmltopdf/bin/wkhtmltoimage.exe")
        imgkit.from_string(html_code, output_path='out.png', config=config)
        return html_code


# returns all the replacements for the day
def get_replacements(url: str = pages['untis-html'][0]) -> dict:
    try:
        page = Page(url)
        return  page.replacements
    except:
        return None

if __name__ == '__main__':
    page = Page(pages['untis-html'][0])

    print(page.replacements)

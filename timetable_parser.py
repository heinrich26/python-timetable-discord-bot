import urllib.request, imgkit, os
from lxml import html
from itertools import zip_longest
from typing import Union, Final


# die Webseitentypen mit bekannten URLs
pages: Final = {
    'untis-html': ["https://www.lilienthal-gymnasium-berlin.de/interna/vplan/Druck_Kla.htm"]
}

untis_html_keys: Final = ('lesson', 'teacher', 'subject', 'replacing_teacher', 'room',
                   'info_text', 'type_of_replacement')

# construct the absolute path for the fonts
fontpath_a = os.path.join(os.getcwd(), 'fonts/arialrounded.woff').replace('\\', '/')
fontpath_b = os.path.join(os.getcwd(), 'fonts/arialrounded.woff2').replace('\\', '/')
page_prettifier_css = {'untis-html': ("""<style type="text/css">@font-face {
    font-family: "ArialRounded";"""
f"  src: url('{fontpath_a}') format('woff'),"
f"      url('{fontpath_b}') format('woff2');"
"""}

body {
    background-color: rgba(0,0,0,0)
    width: fit-content;
}

body, font {
    font-family: 'ArialRounded';
}

table:not([rules]){
    display: none}

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
}

center {
    width: fit-content
}</style>"""
)}




# Klasse für die Webseitenobjekte
class Page(object):
    def __init__(self, url: str = pages['untis-html'][0], overview=True):
        self.url: Final = url

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
            self.extract_data()

    # die Funktionen für die Websitetypen ausführen
    def extract_data(self, key: str=None, keys_only: bool=False) -> Union[tuple[str, list], dict]:
        self.refresh_page()
        if self.type is None:
            return
        elif self.type == 'untis-html':
            return self.parse_untis_html(key, keys_only)
        else:
            pass

    def parse_untis_html(self, key: str=None, keys_only: bool=False) -> Union[tuple[str, list], dict]:
        # 2. Tabelle auswählen
        tables = self.page.findall('//center//table')
        if len(tables) == 1:
            return

        # Daten aus den Zellen extrahieren
        data_cells = {cell.text_content(): cell.get('href')
                      for cell in tables[1].iterfind('.//td/a')}
        print(data_cells)

        # nur die Klassen mit Vertretungen zurückgeben!
        if keys_only: return data_cells.keys()

        key_dict = {item.lower():item for item in data_cells} if key else None
        # Vplan für alle Klassen konstruieren
        if key is None:
            # die Vertretungen für die einzelnen Klassen ermitteln
            for kv in data_cells.items():
                self.parse_untis_html_table(*kv)
        elif key.lower() in key_dict:
            key = key_dict[key.lower()]
            return key, self.parse_untis_html_table(key, data_cells[key])
        else: return None
        del key_dict, key

        # nicht mehr vorkommene Elemente löschen
        if len(data_cells) != len(self.replacements):
            for class_repl in self.replacements:
                if not class_repl in data_cells:
                    self.replacements.pop(class_repl)
                    self.previews.pop(class_repl)
                else: continue

    # extrahiert den Vplan für die jeweilige Klasse
    def parse_untis_html_table(self, key, link) -> list:
        # den Link zum Plan konstruieren
        if link.count('/') == 0:
            link = self.url.rsplit('/', 1)[0] + '/' + link
        webPage = urllib.request.urlopen(link)
        page = html.parse(webPage)
        webPage.close()

        # Abfragen, ob der Plan neuer ist als der in unserer Datenbank
        data_time = page.xpath('(((.//center//table)[1])/tr[2])/td[last()]')[0].text_content()
        if self.times.get(key) == data_time: return self.replacements[key] # überspringen, vorherigen Wert zurückgeben
        else:
            self.times[key] = data_time

        events = page.xpath('(.//center//table)[2]/tr[position()>1]')

        self.replacements[key] = []
        self.previews[key] = self.get_plan_preview(page, key)

        # Alle Vertretungen aus der Tabelle extrahieren
        for event in events:
            cells: list = [item.text_content().strip('\n ').replace(u'\xa0', ' ')
                            if item.text_content() != u'\xa0' else None
                            for item in event.xpath('(.//td)[position()>1]')]
            replacement = dict(zip_longest(untis_html_keys, cells))

            self.replacements[key].append(replacement)
        print(cells)
        return self.replacements[key]


    # macht ein Bild vom Vertretungsplan
    def get_plan_preview(self, page, key: str) -> str:
        # unbenutzte Tabellen entfernen
        unused_tables = page.xpath('(.//center//table)[position()!=2]')
        for table in unused_tables + page.findall('.//meta'):
            table.getparent().remove(table)

        # Header finden um Stylesheet einzufügen
        header = page.find('.//head')
        style = html.fromstring(page_prettifier_css[self.type]).find('.//style')
        header.insert(0, style)

        html_code: str = html.tostring(page).decode('utf-8')

        filename = f"img_cache/{key}.png"
        options: Final = {'quiet': None, 'enable-local-file-access': None, 'width': 512}
        config = imgkit.config(wkhtmltoimage="C:/Program Files/wkhtmltopdf/bin/wkhtmltoimage.exe")
        imgkit.from_string(html_code, filename, options=options, config=config)
        return filename

    # gibt den Vplan der gegebenen Klasse zurück
    def get_plan_for_class(self, key: str) -> tuple[str, list]:
        return self.extract_data(key)

    def get_plan_for_all(self, key: str) -> dict[str, list]:
        self.extract_data()
        return self.replacements


    # url abfragen, Code holen!
    def refresh_page(self):
        webPage = urllib.request.urlopen(self.url)
        self.page = html.parse(webPage)
        webPage.close()
        print('page refreshed')

    def get_classes(self) -> list:
        return self.extract_data(keys_only=True)



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

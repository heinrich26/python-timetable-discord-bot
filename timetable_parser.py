import urllib.request, imgkit, os, platform, io
from discord import File
from lxml import html
from itertools import zip_longest
from typing import Union, Final
from preview_factory import create_html_preview
from replacement_types import ReplacementType, PlanPreview


# die Webseitentypen mit bekannten URLs
pages: Final = {
    'untis-html': ["https://www.lilienthal-gymnasium-berlin.de/interna/vplan/Druck_Kla.htm"]
}

untis_html_keys: Final = ('lesson', 'teacher', 'subject', 'replacing_teacher',
                          'room', 'info_text', 'type_of_replacement')

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

tr:not(:first-child) > td:nth-child(2) > font {
    text-decoration: line-through;
}

td:nth-child(4) {
    display: none;
}

a {
    color: #000000;
}

center {
    width: fit-content
}</style>"""
)}


# ensures existance of the cache directory
img_cache_path = "./img_cache"
def check_cache_dir():
    if not os.path.exists(img_cache_path):
        os.mkdir(img_cache_path)


# Klasse für die Webseitenobjekte
class Page(object):
    def __init__(self, url: str = pages['untis-html'][0], overview=True, db=None):
        self.url: Final = url

        self.replacements: dict = {}
        self.times: dict = {}
        self.previews: dict = {}

        self.db = db

        check_cache_dir()


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
    def extract_data(self, key: str=None, keys_only: bool=False) -> Union[tuple[str, list[ReplacementType], PlanPreview], dict[list[ReplacementType]]]:
        self.refresh_page()
        if self.type is None:
            return
        elif self.type == 'untis-html':
            return self.parse_untis_html(key, keys_only)
        else:
            pass

    def parse_untis_html(self, key: str=None, keys_only: bool=False) -> Union[tuple[str, list[ReplacementType], PlanPreview], dict[list[ReplacementType]]]:
        # 2. Tabelle auswählen
        tables = self.page.findall('//center//table')
        if len(tables) == 1:
            return

        # Daten aus den Zellen extrahieren
        data_cells = {cell.text_content(): cell.get('href')
                      for cell in tables[1].iterfind('.//td/a')}

        # nur die Klassen mit Vertretungen zurückgeben!
        if keys_only:
            return data_cells.keys()
        else:
            key_dict = {item.lower():item for item in data_cells} if key else None
            # Vplan für alle Klassen konstruieren
            if key is None:
                # die Vertretungen für die all Klassen ermitteln
                for kv in data_cells.items():
                    self.parse_untis_html_table(*kv, False)
            elif key.lower() in key_dict:
                key = key_dict[key.lower()]
                return key, *self.parse_untis_html_table(key, data_cells[key])
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
    def parse_untis_html_table(self, key, link, single: bool=True) -> tuple[list[ReplacementType], PlanPreview]:
        # den Link zum Plan konstruieren
        if link.count('/') == 0: # deal with relative Links
            link = self.url.rsplit('/', 1)[0] + '/' + link
        webPage = urllib.request.urlopen(link)
        page = html.parse(webPage)
        webPage.close()

        # Abfragen, ob der Plan neuer ist als der in unserer Datenbank
        time_data = page.xpath('(((.//center//table)[1])/tr[2])/td[last()]')[0].text_content()
        if self.times.get(key) == time_data:
            return self.replacements[key], self.previews[key] # überspringen, vorherigen Wert zurückgeben
        else:
            self.times[key] = time_data # Datum eintragen
        events = page.xpath('(.//center//table)[2]/tr[position()>1]')

        del page # release the page

        self.replacements[key] = []

        none_cases = ('\xa0', '+', '---')

        # Alle Vertretungen aus der Tabelle extrahieren
        for event in events:
            cells: list = [item.text_content().strip('\n ').replace('\xa0', ' ')
                            if not item.text_content().strip('\n ') in none_cases else None
                            for item in event.xpath('(.//td)[position()>1]')]
            replacement: ReplacementType = dict(zip_longest(untis_html_keys, cells))

            self.replacements[key].append(replacement)

        if single:
            return self.replacements[key], self.get_plan_preview(key)
        else:
            self.previews[key] = self.get_plan_preview(key)
            return



    # macht ein Bild vom Vertretungsplan
    def get_plan_preview(self, key: str) -> PlanPreview:
        plan_img_url: str = self.db.get_plan(key, self.times[key])
        if plan_img_url is not None:
            self.previews[key] = plan_img_url # put the value to the dict
            return plan_img_url


        # Nach HTML konvertieren & newlines entfernen, die extra Spaces erzeugen
        html_code: str = create_html_preview(self.replacements[key])


        filename = f'{key}_plan.png'
        options: Final = {'quiet': None, 'width': 640, 'transparent': None,
                          'enable-local-file-access': None, 'format': 'png',
                          'encoding': "UTF-8"}

        conf = imgkit.config()
        if platform.system() == 'Linux':
            try:
                conf.get_wkhtmltoimage()
            except:
                conf.wkhtmltoimage = "./.apt/usr/local/bin/wkhtmltoimage"
        else:
            conf.wkhtmltoimage = "C:/Program Files/wkhtmltopdf/bin/wkhtmltoimage.exe"
        config: Final = {
            'options': options,
            'config': conf
        }

        buf = io.BytesIO(imgkit.from_string(html_code, False, **config))
        buf.seek(0)
        return File(buf, filename=filename)

    # gibt den Vplan der gegebenen Klasse zurück
    def get_plan_for_class(self, key: str) -> tuple[str, list[ReplacementType], PlanPreview]:
        return self.extract_data(key)

    # gibt den Vplan für alle Klassen der Seite zurück!
    def get_plan_for_all(self) -> tuple[dict[str, list[ReplacementType]], dict[PlanPreview]]:
        self.extract_data()
        return self.replacements, self.previews


    # url abfragen, Code holen!
    def refresh_page(self):
        webPage = urllib.request.urlopen(self.url)
        self.page = html.parse(webPage)
        webPage.close()

    def get_classes(self) -> list:
        return self.extract_data(keys_only=True)




if __name__ == '__main__':
    from class_name_preview import ImageDatabase
    page = Page(pages['untis-html'][0], db=ImageDatabase())

    print(page.replacements)

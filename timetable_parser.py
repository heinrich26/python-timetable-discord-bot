import urllib.request
import os
import platform
import io
from itertools import zip_longest
from typing import Union, Final
import imgkit
from discord import File
from lxml import html
from preview_factory import create_html_preview
from replacement_types import ReplacementType, PlanPreview
from attachment_database import ImageDatabase


# die Webseitentypen mit bekannten URLs
PAGES: Final = {
    'untis-html': ["https://www.lilienthal-gymnasium-berlin.de/interna/vplan/Druck_Kla.htm"]
}

UNTIS_HTML_KEYS: Final = ('lesson', 'teacher', 'subject', 'replacing_teacher',
                          'room', 'info_text', 'type_of_replacement')

# construct the absolute path for the fonts
FONT_A = os.path.join(
    os.getcwd(), 'fonts/arialrounded.woff').replace('\\', '/')
FONT_B = os.path.join(
    os.getcwd(), 'fonts/arialrounded.woff2').replace('\\', '/')

# ensures existance of the cache directory
IMG_CACHE_PATH = "./img_cache"


def check_cache_dir():
    '''Ensures that the Cache directory exists'''
    if not os.path.exists(IMG_CACHE_PATH):
        os.mkdir(IMG_CACHE_PATH)


# Klasse für die Webseitenobjekte
class Page:
    '''Klasse für Vertetungsplan Webseiten
    Extrahiert Vertretungen & produziert Previews'''

    def __init__(self, url: str = PAGES['untis-html'][0], database: ImageDatabase = None):
        self.url: Final = url

        self.replacements: dict = {}
        self.times: dict = {}
        self.previews: dict = {}

        self.database = database

        check_cache_dir()

        # den Websitetypen bestimmen
        self.page_type: str = None
        for page_item in PAGES.items():
            if url in page_item[1]:
                self.page_type = page_item[0]
                break

        if self.page_type is not None:
            self.extract_data()

    def extract_data(self, key: str = None, keys_only: bool = False) -> Union[tuple[str, list[ReplacementType], PlanPreview], dict[list[ReplacementType]], None]:
        '''Führt die Funktionen für den jeweiligen Websitetypen aus'''
        self.refresh_page()
        if self.page_type is None:
            return None
        elif self.page_type == 'untis-html':
            return self.parse_untis_html(key, keys_only)

    def parse_untis_html(self, key: str = None, keys_only: bool = False) -> Union[tuple[str, list[ReplacementType], PlanPreview], dict[list[ReplacementType]], None]:
        '''Extrahiert die Klassen & Links aus der Webseite'''
        # 2. Tabelle auswählen
        tables = self.page.findall('//center//table')
        if len(tables) == 1:
            return None

        # Daten aus den Zellen extrahieren
        data_cells = {cell.text_content(): cell.get('href')
                      for cell in tables[1].iterfind('.//td/a')}

        # nur die Klassen mit Vertretungen zurückgeben!
        if keys_only:
            return data_cells.keys()

        key_dict = {item.lower(): item for item in data_cells} if key else None
        # Vplan für alle Klassen konstruieren
        if key is None:
            # die Vertretungen für die all Klassen ermitteln
            for kv in data_cells.items():
                self.parse_untis_html_table(*kv, False)
        elif key.lower() in key_dict:
            key = key_dict[key.lower()]
            return key, *self.parse_untis_html_table(key, data_cells[key])
        else:
            return None
        del key_dict, key

        # nicht mehr vorkommene Elemente löschen
        if len(data_cells) != len(self.replacements):
            for class_repl in self.replacements:
                if not class_repl in data_cells:
                    self.replacements.pop(class_repl)
                    self.previews.pop(class_repl)
                else:
                    continue

    def parse_untis_html_table(self, key, link, single: bool = True) -> tuple[list[ReplacementType], PlanPreview]:
        '''Extrahiert den Vertretungsplan für die jeweilige Klasse'''
        # den Link zum Plan konstruieren
        if link.count('/') == 0:  # deal with relative Links
            link = self.url.rsplit('/', 1)[0] + '/' + link
        with urllib.request.urlopen(link) as web_page:
            with html.parse(web_page) as page:
                web_page.close()

                # Abfragen, ob der Plan neuer ist als der in unserer Datenbank
                time_data = page.xpath(
                    '(((.//center//table)[1])/tr[2])/td[last()]')[0].text_content()
                if self.times.get(key) == time_data:
                    # überspringen, vorherigen Wert zurückgeben
                    return self.replacements[key], self.previews[key]

                self.times[key] = time_data  # Datum eintragen
                events = page.xpath('(.//center//table)[2]/tr[position()>1]')

        self.replacements[key] = []

        none_cases = ('\xa0', '+', '---')

        # Alle Vertretungen aus der Tabelle extrahieren
        for event in events:
            cells: list = [item.text_content().strip('\n ').replace('\xa0', ' ')
                           if not item.text_content().strip('\n ') in none_cases else None
                           for item in event.xpath('(.//td)[position()>1]')]
            replacement: ReplacementType = dict(
                zip_longest(UNTIS_HTML_KEYS, cells))

            self.replacements[key].append(replacement)

        if single:
            return self.replacements[key], self.get_plan_preview(key)

        self.previews[key] = self.get_plan_preview(key)
        return None

    def get_plan_preview(self, key: str) -> PlanPreview:
        '''Produziert die Preview für den Vertretungsplan'''
        plan_img_url: str = self.database.get_plan(key, self.times[key])
        if plan_img_url is not None:
            self.previews[key] = plan_img_url  # put the value to the dict
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

    def get_plan_for_class(self, key: str) -> tuple[str, list[ReplacementType], PlanPreview]:
        '''Gibt den Vertretungsplan der gegebenen Klasse zurück'''
        return self.extract_data(key)

    def get_plan_for_all(self) -> tuple[dict[str, list[ReplacementType]], dict[PlanPreview]]:
        '''Gibt den Vertretungsplan für alle Klassen der Seite zurück!'''
        self.extract_data()
        return self.replacements, self.previews

    def refresh_page(self):
        '''Url abfragen, Code laden!'''
        with urllib.request.urlopen(self.url) as web_page:
            self.page = html.parse(web_page)

    def get_classes(self) -> list:
        '''Gibt alle Klassen mit Vertretungen zurück'''
        return self.extract_data(keys_only=True)


if __name__ == '__main__':
    example_page = Page(PAGES['untis-html'][0], database=ImageDatabase())

    print(example_page.replacements)

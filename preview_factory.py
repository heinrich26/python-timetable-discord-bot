from discord import Embed, File, Colour
from typing import TypedDict, Final
from bs4 import BeautifulSoup
import codecs, os

from replacement_types import ReplacementType

replaced: Final = ('vertretung', 'betreuung')

fontpath_a = os.path.join(os.getcwd(), 'fonts/arialrounded.ttf').replace('\\', '/')
fontpath_b = os.path.join(os.getcwd(), 'fonts/Arial_Rounded_MT_ExtraBold.ttf').replace('\\', '/')

stylesheet = ('''<style>
@font-face {
    font-family: "ArialRounded";'''
f"  src: url('{fontpath_a}');"
'''}

@font-face {
    font-family: "ArialRoundedBold";'''
f"    src: url('{fontpath_b}');"
'''}

body {
    margin: 0px;
    width: 640px;
    height: fit-content;
}

table {
    width: 620px;
    margin: 0px 10px;
    border-spacing: 0 10px;
    height: fit-content;
    font-family: ArialRounded;
    font-size: 200%;
}

td > div {
  font-family: ArialRoundedBold;
}

tr td:first-child {
  font-family: ArialRoundedBold;
  text-align: center;
  font-size: 32pt;
  width: 30%;
  padding: 6px 6px 0px 6px;
  box-sizing: border-box;
  border-color: rgba(0,0,0,.1);
  border-style: solid;
  border-width: 2px 0px 2px 2px;
  -webkit-border-top-left-radius: 7px;
  -webkit-border-bottom-left-radius: 7px;
}

tr td:last-child {
  width: 70%;
  padding: 6px 6px 6px 0px;
  box-sizing: border-box;
  border-color: rgba(0,0,0,.1);
  border-style: solid;
  border-width: 2px 2px 2px 0px;
  -webkit-border-top-right-radius: 7px;
  -webkit-border-bottom-right-radius: 7px;
}

tr.replaced {
  background: -webkit-gradient(linear, left top, right top, color-stop(3%, #202225), color-stop(3%, #3D5AFE));
  background-attachment: fixed;
}

tr.canceled {
  background: -webkit-gradient(linear, left top, right top, color-stop(3%, #202225), color-stop(3%, #F44336));
  background-attachment: fixed;
}
</style>''')

class MessageData(TypedDict):
    files: list[File]
    embeds: list[Embed]

def prettify_html(func):
    def wrapper_prettify_html(*args, **kwargs):
        return BeautifulSoup(func(*args, **kwargs), features='lxml').prettify()
    return wrapper_prettify_html

# splits a List into Sublists with len() <= n
def chunks(list: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(list), n):
        yield list[i:i + n]

def sort_items(replacements: list[ReplacementType]) -> list[ReplacementType]:
    return sorted(replacements, key=lambda key: key.get('lesson'))


def create_embed(replacement: ReplacementType) -> Embed:
    replacer: str = replacement.get('replacing_teacher')
    info: str = replacement.get('info')
    room: str = replacement.get('room')
    repl_type: str = replacement['type_of_replacement']
    desc: str = (replacement.get('subject', '') +
                 f"({'' if replacer is None else (replacer + ' ')}~~{replacement['teacher']}~~)" +
                 f"{' in ' + room if room is not None else ''}" +
                 ('\n' + info) if info is not None else '')
    return Embed(title=repl_type,
                 description=desc,
                 colour=Colour.blue() if repl_type in replaced
                        else Colour.magenta())

# Splits the Replacements and sorts them
def prepare_replacements(replacements: list[ReplacementType]) -> list[list[ReplacementType]]:
    return chunks(sort_items(replacements), 10)


def wrap_tag(code: str, tag: str='div', sclass=None, **kwargs) -> str:
    if sclass is not None: kwargs['class'] = sclass
    attrs = ' ' + ' '.join([f"{kv[0]}='{str(kv[1])}'" for kv in kwargs.items()]) if kwargs else ''
    return f"<{tag + attrs}>{str(code)}</{tag}>"

def create_replacement_tile(replacement: ReplacementType) -> str:
    teacher: str = replacement['teacher']
    replacer: str = replacement.get('replacing_teacher')
    info: str = replacement.get('info_text')
    room: str = replacement.get('room')
    repl_type: str = replacement['type_of_replacement']
    desc: str = replacement.get('subject', '') + \
                 f" ({'' if replacer is None else (replacer + ' ')}{wrap_tag(teacher, 's') if teacher != replacer else ''})" + \
                 f"{' in ' + room if room is not None else ''}" + \
                 ('<br>' + info if info is not None else '')

    contents = wrap_tag(replacement['lesson'], 'td') + wrap_tag(wrap_tag(repl_type, 'div') + desc, 'td')
    return wrap_tag(contents, 'tr', sclass='replaced' if repl_type.lower() in replaced else 'canceled')

def convert_unicode_chars(input: str) -> str:
    if input.isalnum():
        return input
    else:
        out = ''
        for char in input:
            if char in '''  \nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890<>/!\\´`'"§$%&()[]{}?=+~*'#-_.:,;|@^°''':
                out += char
            else:
                out += '&#' + str(ord(char)) + ';'
    return input

# @prettify_html
def create_html_preview(replacements: list[ReplacementType]) -> str:
    html = stylesheet + '<table>'

    for replacement in sort_items(replacements):
        html += create_replacement_tile(replacement)

    html += '</table>'

    html = '<head><meta http-equiv="content-type" content="text/html; charset=utf-8"></head>\n' + \
            wrap_tag(html, 'body') #convert_unicode_chars(wrap_tag(html, 'body'))

    return wrap_tag(html, 'html')


if __name__ == '__main__':
    replacements = [{
            'lesson': '1', 'teacher': 'Ks', 'subject': 'GEO', 'replacing_teacher': 'Gw',
            'room': 'B108', 'info_text': None, 'type_of_replacement': 'Vertretung'
        }, {
            'lesson': '1-2', 'teacher': 'Mv', 'subject': 'SP', 'replacing_teacher': 'V\u00F6',
            'room': 'G\u00D6E', 'info_text': None, 'type_of_replacement': 'Vertretung'
        }, {
            'lesson': '3-4', 'teacher': 'So', 'subject': 'BIO', 'replacing_teacher': None,
            'room': 'A106', 'info_text': None, 'type_of_replacement': 'Entfall'
        }, {
            'lesson': '7', 'teacher': 'Tm', 'subject': 'DE', 'replacing_teacher': None,
            'room': 'OBR', 'info_text': 'OPfer kinder tralllalalalallalala', 'type_of_replacement': 'EVA'
        }]

    with codecs.open('tiles.html', 'w', 'utf-8') as f:
        f.write(create_html_preview(replacements, 'Q1'))

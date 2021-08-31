import codecs
import os
from typing import Final
from discord import Embed, Colour
from replacement_types import ReplacementType

REPLACED: Final = ('vertretung', 'betreuung')

FONT_A = os.path.join(os.getcwd(), 'fonts/arialrounded.ttf').replace('\\', '/')
FONT_B = os.path.join(os.getcwd(), 'fonts/Arial_Rounded_MT_ExtraBold.ttf').replace('\\', '/')

STYLESHEET = ('''<style>
@font-face {
    font-family: "ArialRounded";'''
f"  src: url('{FONT_A}');"
'''}

@font-face {
    font-family: "ArialRoundedBold";'''
f"    src: url('{FONT_B}');"
'''}

body {
    margin: 0px;
    width: 640px;
    height: fit-content;
}

table {
    width: 640px;
    margin: 0px;
    border-spacing: 0px;
    height: fit-content;
    font-family: ArialRounded;
    font-size: 200%;
}

tr:not(:first-child) {margin-top: 10px}

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

tr.REPLACED {
  background: -webkit-gradient(linear, left top, right top, color-stop(2%, #202225), color-stop(2%, #3D5AFE));
  background-attachment: fixed;
}

tr.canceled {
  background: -webkit-gradient(linear, left top, right top, color-stop(2%, #202225), color-stop(2%, #F44336));
  background-attachment: fixed;
}
</style>''')



# splits a List into Sublists with len() <= n
def chunks(items: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(items), n):
        yield items[i:i + n]

def sort_items(replacements: list[ReplacementType]) -> list[ReplacementType]:
    '''Sorts the Replacements by Lesson'''
    return sorted(replacements, key=lambda key: key.get('lesson'))


def create_embed(replacement: ReplacementType) -> Embed:
    '''Creates an Embed Tile for a Replacement'''
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
                 colour=Colour.blue() if repl_type in REPLACED
                 else Colour.magenta())


# Splits the Replacements and sorts them
def prepare_replacements(replacements: list[ReplacementType]) -> list[list[ReplacementType]]:
    '''Applies the Embed limits of discord'''
    return chunks(sort_items(replacements), 10)


def wrap_tag(code: str, tag: str = 'div', sclass=None, **kwargs) -> str:
    '''Surrounds the given String with the given Tag'''
    if sclass is not None:
        kwargs['class'] = sclass
    attrs = ' ' + \
            ' '.join([f"{kv[0]}='{str(kv[1])}'" for kv in kwargs.items()]) \
            if kwargs else ''
    return f"<{tag + attrs}>{str(code)}</{tag}>"



def create_replacement_tile(replacement: ReplacementType) -> str:
    '''Creates on HTML Row for a replacement'''
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
    return wrap_tag(contents, 'tr', sclass='REPLACED' if repl_type.lower() in REPLACED else 'canceled')


def convert_unicode_chars(inp: str) -> str:
    '''Removes all Html-unsupported chars from the String'''
    if inp.isalnum():
        return inp

    out = ''
    for char in inp:
        if char in '''  \nabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890<>/!\\´`'"§$%&()[]{}?=+~*'#-_.:,;|@^°''':
            out += char
        else:
            out += '&#' + str(ord(char)) + ';'
    return inp



def create_html_preview(replacements: list[ReplacementType]) -> str:
    '''Writes the HTML for the given replacements'''
    html = STYLESHEET + '<table>'

    for replacement in sort_items(replacements):
        html += create_replacement_tile(replacement)

    html += '</table>'

    html = '<head><meta http-equiv="content-type" content="text/html; charset=utf-8"></head>\n' + \
        wrap_tag(html, 'body')  # convert_unicode_chars(wrap_tag(html, 'body'))

    return wrap_tag(html, 'html')




if __name__ == '__main__':
    example_replacements = [{
        'lesson': '1', 'teacher': 'Ks', 'subject': 'GEO',
        'replacing_teacher': 'Gw', 'room': 'B108', 'info_text': None,
        'type_of_replacement': 'Vertretung'
    }, {
        'lesson': '1-2', 'teacher': 'Mv', 'subject': 'SP', 'info_text': None,
        'replacing_teacher': 'V\u00F6', 'room': 'G\u00D6E',
        'type_of_replacement': 'Vertretung'
    }, {
        'lesson': '3-4', 'teacher': 'So', 'subject': 'BIO', 'replacing_teacher': None,
        'room': 'A106', 'info_text': None, 'type_of_replacement': 'Entfall'
    }, {
        'lesson': '7', 'teacher': 'Tm', 'subject': 'DE', 'replacing_teacher': None,
        'room': 'OBR', 'info_text': 'OPfer kinder tralllalalalallalala',
        'type_of_replacement': 'EVA'
    }]

    with codecs.open('tiles.html', 'w', 'utf-8') as f:
        f.write(create_html_preview(example_replacements, 'Q1'))

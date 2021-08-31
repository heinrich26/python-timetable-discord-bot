import os, sqlite3, discord, io
from PIL import Image, ImageDraw, ImageFont
from typing import Union


img_res = 320


class ImageDatabase(object):
    def __init__(self, name:str='attachments.db'):
        create_tables = not os.path.exists(name)
        self.db = sqlite3.connect(name)
        self.cursor = self.db.cursor()

        if create_tables:
            self.cursor.execute('CREATE TABLE icons (key text, link text)')
            self.cursor.execute('CREATE TABLE plans (key text, link text, date text)')


    def get_icon(self, key: str) -> Union[str, discord.Embed]:
        self.cursor.execute('SELECT link FROM icons WHERE key = ?', [f'{key}_icon'])
        link = self.cursor.fetchone()
        self.cursor = self.db.cursor()

        # create the Image
        if link is None:
            img = Image.new("RGBA", (img_res, img_res), (0, 0, 0, 0))
            font = ImageFont.truetype("fonts/arialrounded.ttf", int(105 * (4 / (len(key) - key.count('.')))))

            draw = ImageDraw.Draw(img)
            draw.text((img_res / 2, img_res / 2), key, anchor='mm', font=font, fill=(142, 146, 151))

            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            file = discord.File(buf, filename=f'{key}_icon.png')

            return file
        else:
            return link[0]

    def get_plan(self, key: str, date: str) -> str:
        key = [f'{key}_plan']
        self.cursor.execute('SELECT * FROM plans WHERE key = ?', key)
        result = self.cursor.fetchone()
        self.cursor = self.db.cursor()

        if result is None:
            return None
        elif date == result[2]:
            return result[1]
        else:
            self.cursor.execute('DELETE FROM plans WHERE key = ?', key)
            self.db.commit()

            return None


    def set_attachment(self, key: str, link: str, date: str=None):
        self.cursor.execute(*('INSERT INTO icons VALUES (?, ?)',
                            (f'{key}_icon', link)) if date is None else
                            ('INSERT INTO plans VALUES (?, ?, ?)',
                            (f'{key}_plan', link, date)))
        self.db.commit()



    def __del__(self):
        self.db.commit()
        self.db.close()

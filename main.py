import os, math
from discord import Embed, Client, Message

from attachment_database import ImageDatabase
from timetable_parser import pages, Page
from replacement_types import ReplacementType, PlanPreview

empty_field = {'name': '\u200b', 'value': '\u200b', 'inline': False}

default_footer = {'text': 'Alle Angaben ohne Gewähr! Aber mit Gewehr. '}

invite_link = 'https://discord.com/api/oauth2/authorize?client_id=489087343589064704&permissions=268594240&scope=bot'

def mk_field(name: str='\u200b', value: str='\200b', inline: bool=True) -> dict:
    return {'name': name if name else '\u200b', 'value': value if value else '\u200b', 'inline': inline}

def row_for_class(class_a: dict, class_b: dict=None, header: bool=False, has_info: bool=False) -> list:
    if header:
        row = [
            mk_field('**Stunde**', class_a['lesson']),
            mk_field('**Lehrer**', f"~~{class_a['teacher'] if class_a.get('teacher') is not None else ''}~~{(' ' + class_a['replacing_teacher']) if class_a.get('replacing_teacher') is not None else ''}"),
            mk_field('**Fach**', class_a['subject']),
            mk_field('**Raum**', class_a['room']),
            # hier kommt das Info Feld hin, wenn es eins gibt!
            mk_field('**Art**', class_a['type_of_replacement'])
        ]
        if has_info:
            row.insert(-1, mk_field('**Info**', class_a['info_text']))
    else:
        row = []
        keys = ('lesson', 'subject', 'room', 'info_text', 'type_of_replacement')
        for i in range(0, 5):
            if i == 4 and not has_info: continue
            key = keys[i]
            row.append(mk_field(class_a[key], class_b[key] if class_b else None))
        row.insert(1, mk_field(f"~~{class_a['teacher']}~~{(' ' + class_a['replacing_teacher']) if class_a.get('replacing_teacher') is not None else ''}", None if not class_b else f"~~{class_b['teacher']}~~{(' ' + class_b['replacing_teacher']) if class_b.get('replacing_teacher') is not None else ''}"))
    return row


def class_vplan(usr_class: str, data: list) -> Embed:
    data = sorted(data, key=lambda e: e['lesson'])
	# Vertretungsplan für eine Klasse
    embedded_msg = Embed(title=f'Vertretungsplan der {usr_class}', description='Hier siehst du deine heutigen Vertretungen')

    no_info = True in [True if 'info_text' in item else None for item in data]
    fields = row_for_class(data[0], header=True, has_info=not no_info)
    if len(data) != 1:
        for i in range(0, math.ceil((len(data)-1)/2)):
            fields.append(empty_field)
            fields.extend(row_for_class(data[i*2+1], data[i*2+2] if i*2+2 != len(data) else None, has_info=not no_info))
    for field in fields:
        embedded_msg.add_field(**field)
    return embedded_msg


def build_plan(message: Message, key: str, replacements: ReplacementType, preview: PlanPreview) -> tuple[str, list, Embed, tuple[bool, bool]]:
    # embed = class_vplan(key, replacements)
    embed = Embed(title=f'**Vertretungsplan der {key}**', description='Hier siehst du deine heutigen Vertretungen:')
    embed.set_footer(**default_footer)

    files: list = []
    thumbnail = img_db.get_icon(key)

    known_icon = type(thumbnail) == str
    if known_icon:
        embed.set_thumbnail(url=thumbnail)
    else:
        embed.set_thumbnail(url=f'attachment://{thumbnail.filename}')
        files.append(thumbnail)

    generated_plan = type(preview) == str
    if preview is not None:
        if generated_plan:
            embed.set_image(url=preview)
        else:
            embed.set_image(url=f'attachment://{preview.filename}')
            files.append(preview)

    return key, files, embed, (known_icon, generated_plan)


def update_database_from_msg(key: str, message: Message, bools: tuple[bool, bool]) -> None:
    if not bools[0]:
        img_db.set_attachment(key, message.embeds[0].thumbnail.url)

    if not bools[1]:
        link = message.embeds[-1].image.url
        img_db.set_attachment(key, link, liliplan.times[key])
        liliplan.previews[key] = link


def sort_classes(classes: list[str]) -> list[str]:
    def comp(key: str):
        i=0
        while key[:i+1].isnumeric():
            i+=1
        else:
            return key[:i], key[i:]

    return sorted(classes, key=comp)


def check_lastModified() -> None:
    db = './attachments.db'
    if not os.path.exists(db): return
    else:
        files = ('main.py', 'preview_factory.py', 'timetable_parser.py', 'attachment_database.py')
        db_last_mod = os.path.getmtime(db)
        for file in files:
            if db_last_mod < os.path.getmtime(file):
                os.remove(db)
                break


if __name__ == "__main__":
    # remove the database, if it's older than the Source Code
    check_lastModified()

    img_db = ImageDatabase()
    liliplan = Page(pages['untis-html'][0], db=img_db)

    client = Client()

    @client.event
    async def on_ready():
        print(f"We've logged in as {client.user}")

    @client.event
    async def on_message(msg):
        if msg.author == client.user: return


        text = msg.content
        if text.startswith('/vplan') or text.startswith('/vertretungsplan') or text.startswith('!vplan') or text.startswith('!vertretungsplan'):
            args = text.split(' ')
            if len(args) > 1: args[1] = args[1].lower()

            # Vertretungen abfragen
            if len(args) > 2: # too many Arguments
                async with msg.channel.typing():
                    await msg.channel.send('**Ungültige Argumente!**\nVersuch mal `!vplan <Klasse>` oder `!vplan help`!')
            elif len(args) == 1:
                # sending the plan for everyone!
                async with msg.channel.typing():
                    replacements, previews = liliplan.get_plan_for_all()

                    if replacements is None or replacements == {}: # awww, you dont have replacements! How sad!
                        # Assemble the Embed
                        embedded_msg = Embed(title='Vertretungsplan',
                                             description='Hier siehst du deine heutigen Vertretungen')
                        embedded_msg.add_field(name='**Keine Vertretungen heute...**',
                                               value='\u200b', inline=False)
                        embedded_msg.set_footer(**default_footer)

                        # Send
                        msg.channel.send(embed=embedded_msg)
                    else:
                        for key in replacements.keys():
                            key, files, embed, bools = build_plan(msg, key, replacements[key], previews[key])
                            sent_msg = await msg.channel.send(files=files, embed=embed)
                            update_database_from_msg(key, sent_msg, bools)
                        # Remove files from the Previews
                        # for key in liliplan.previews:
                        #     if type(liliplan.previews[key]) == File:
                        #         liliplan.previews.pop(key)
            elif args[1] in ('help', 'h'): # send an info message to the channel
                async with msg.channel.typing():
                    help_embed = Embed(title='**__Vertretungsplan Hilfe__**',
                                       description='Hier findest du alle wichtigen Commands für den Vertretungsplan!')
                    help_embed.add_field(name='**Verwendung:** `!vplan [Optionen]`',
                                         value=('`ohne Args` Zeigt den kompletten Plan\n'
                                                '`... help` Zeigt diese Info\n'
                                                '`... <Klasse>` Zeigt den Plan für eine Klasse\n'
                                                '`... klassen` Zeigt alle Klassen die heute Vertretung haben'))
                    await msg.channel.send(embed=help_embed)
            elif args[1] in ('klassen', 'classes', 'list', 'liste'): # send all classes that have replacements at this day!
                await msg.channel.trigger_typing()
                info_embed = Embed(title='**Klassen die heute Vertretung haben**:',
                description=f"`{'`, `'.join(liliplan.get_classes())}`\n\n Verwende `!vplan <Klasse>` um einen bestimmten Plan zu sehen!")
                info_embed.set_footer(**default_footer)
                await msg.channel.send(embed=info_embed)
            elif args[1] == 'invite': # send an invitation Link
                await msg.channel.send(f"Du willst den Bot auch auf deinem Server haben?\n\nLad ihn hiermit ein: {invite_link}")
            else: # Send the plan for one Class
                async with msg.channel.typing():
                    key, files, embed, bools = build_plan(msg, *liliplan.get_plan_for_class(args[1]))
                    sent_msg = await msg.channel.send(files=files, embed=embed)
                update_database_from_msg(key, sent_msg, bools)



    try:
        client.run(os.environ['BOT_TOKEN'] if 'BOT_TOKEN' in os.environ else open('token_secret', 'r').readlines()[0])
    except Exception as exception:
        print(exception)

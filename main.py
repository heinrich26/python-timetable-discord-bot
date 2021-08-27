import discord, os, math
from timetable_parser import pages, Page


empty_field = {'name': '\u200b', 'value': '\u200b', 'inline': False}

default_footer = {'text': 'Alle Angaben ohne Gewähr! Aber mit Gewehr. '}

invite_link = 'https://discord.com/api/oauth2/authorize?client_id=489087343589064704&permissions=268594240&scope=bot'

def mk_field(name='\u200b', value='\200b', inline: bool=True) -> dict:
    return {'name': name if name else '\u200b', 'value': value if value else '\u200b', 'inline': inline}

def row_for_class(class_a: dict, class_b: dict=None, header: bool=False, has_info: bool=False) -> list:
    if header:
        row = [
            mk_field('**Stunde**', class_a['lesson']),
            mk_field('**Lehrer**', f"~~{class_a['teacher']}~~{(' ' + class_a['replacing_teacher']) if 'replacing_teacher' in class_a else ''}"),
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
        row.insert(1, mk_field(f"~~{class_a['teacher']}~~{(' ' + class_a['replacing_teacher']) if 'replacing_teacher' in class_a else ''}", None if not class_b else f"~~{class_b['teacher']}~~{(' ' + class_b['replacing_teacher']) if 'replacing_teacher' in class_b else ''}"))
    return row

def class_vplan(usr_class, data: list):
    data = sorted(data, key=lambda e: e['lesson'])
	# Vertretungsplan für eine Klasse
    embedded_msg = discord.Embed(title=f'Vertretungsplan der {usr_class}', description='Hier siehst du deine heutigen Vertretungen')

    no_info = True in [True if 'info_text' in item else None for item in data]
    fields = row_for_class(data[0], header=True, has_info=not no_info)
    if len(data) != 1:
        for i in range(0, math.ceil((len(data)-1)/2)):
            fields.append(empty_field)
            fields.extend(row_for_class(data[i*2+1], data[i*2+2] if i*2+2 != len(data) else None, has_info=not no_info))
    for field in fields:
        embedded_msg.add_field(**field)
    embedded_msg.set_footer(**default_footer)
    return embedded_msg

client = discord.Client()
liliplan = None

@client.event
async def on_ready():
    print(f"We've logged in as {client.user}")
    global liliplan
    liliplan = Page(pages['untis-html'][0])

@client.event
async def on_message(msg):
    if msg.author == client.user: return


    text = msg.content
    if text.startswith('/vplan') or text.startswith('/vertretungsplan') or text.startswith('!vplan') or text.startswith('!vertretungsplan'):
        args = text.split(' ')
        if len(args) > 1: args[1] = args[1].lower()

        # Vertretungen abfragen    

        if len(args) > 2:
            await msg.channel.send('**Ungültige Argumente!**\nVersuch mal `!vplan <Klasse>` oder `!vplan help`!')
            return
        elif len(args) == 1: pass
        elif len(args) == 2 and args[1] == 'help':
            help_embed = discord.Embed(title='**__Vertretungsplan Hilfe__**', description='Hier findest du alle wichtigen Commands für den Vertretungsplan!')
            help_embed.add_field(name='**Verwendung:** `!vplan [Optionen]`', value='`ohne Args` Zeigt den kompletten Plan\n`... help` Zeigt diese Info\n`... <Klasse>` Zeigt den Plan für eine Klasse\n`... klassen` Zeigt alle Klassen die heute Vertretung haben')
            await msg.channel.send(embed=help_embed)
            return
        elif args[1] == 'klassen':
            await msg.channel.send(f"Klassen die heute Vertretung haben:\n\n{', '.join(liliplan.get_classes())}")
            return
        elif args[1] == 'invite':
            await msg.channel.send(f"Du willst den Bot auch auf deinem Server haben?\n\nLad ihn hiermit ein: {invite_link}")
            return
        else:
            key, replacements = liliplan.get_plan_for_class(args[1])
            print(key, replacements)
            embed = class_vplan(key, replacements)

            file: str = liliplan.previews.get(key)
            if file is not None:
                image = discord.File(file)
                embed.set_image(url=f'attachment://{file}')

            await msg.channel.send(file=image, embed=embed)
            return

        replacements = liliplan.get_plan_for_all()

        if replacements is None or replacements == {}:
            embedded_msg = discord.Embed(title='Vertretungsplan',
                                    description='Hier siehst du deine heutigen Vertretungen')
            embedded_msg.add_field(name='**Keine Vertretungen heute...**', value='\u200b', inline=False)
            embedded_msg.set_footer(**default_footer)
            msg.channel.send(embed=embedded_msg)
        else:
            for rep_class in sorted(replacements.keys()):
                await msg.channel.send(embed=class_vplan(rep_class, replacements[rep_class]))


try:
    client.run(os.environ['BOT_TOKEN'] if 'BOT_TOKEN' in os.environ else open('token_secret', 'r').readlines()[0])
except:
    print("error")

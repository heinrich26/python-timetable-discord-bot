import discord, os, math
from timetable_parser import get_replacements, pages
from itertools import zip_longest


empty_field = {'name': ' ', 'value': ' ', 'inline': False}

def mk_field(name=' ', value=' ', inline: bool=True) -> dict:
    return {'name': name if name else ' ', 'value': value if value else ' ', 'inline': inline}

def row_for_class(class_a: dict, class_b: dict={}, header: bool = False, has_info: bool=False) -> list:
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
            table.insert(-1, mk_field('**Info**', class_a['info_text']))
    else:
        row = []
        keys = ('lesson', 'subject', 'room', 'info_text', 'type_of_replacement')
        for i in range(0, 5):
            if i == 4 and not has_info: continue
            key = keys[i]
            row.append(mk_field(class_a[key], class_b[key] if class_b else None))
        row.insert(1, mk_field(f"~~{class_a['teacher']}~~{(' ' + class_a['replacing_teacher']) if 'replacing_teacher' in class_a else ''}", None if class_b else f"~~{class_b['teacher']}~~{(' ' + class_b['replacing_teacher']) if 'replacing_teacher' in class_b else ''}"))
    return row

client = discord.Client()

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
        replacements = get_replacements()
        lower_keys = {key.lower(): key for key in replacements} if replacements != None else ()

        if len(args) > 2:
            await msg.channel.send('**Ungültige Argumente!**\nVersuch mal `!vplan <Klasse>` oder `!vplan help`!')
            return
        elif len(args) == 1: continue
        elif len(args) == 2 and args[1] == 'help':
            help_embed = discord.Embed(title='**__Vertretungsplan Hilfe__**', description='Hier findest du alle wichtigen Commands für den Vertretungsplan!')
            help_embed.add_field(name='**Verwendung:** `!vplan [Optionen]`', value='`ohne Args` Zeigt den kompletten Plan\n`... help` Zeigt diese Info\n`... <Klasse>` Zeigt den Plan für eine Klasse\n`... klassen` Zeigt alle Klassen die heute Vertretung haben')
            await msg.channel.send(embed=help_embed)
            return
        elif args[1] in lower_keys:
            usr_class: lower_keys[args[1]]

            
            # Vertretungsplan für eine Klasse
            embedded_msg = discord.Embed(title=f'Vertretungsplan der {usr_class}',
                                            description='Hier siehst du deine heutigen Vertretungen')
            data = sorted(replacements[usr_class], key=lambda e: e['lesson'])
            no_info = True in [True if 'info_text' in item else None for item in data]
            fields = row_for_class(data[0], header=True, no_info=no_info)
            if len(data) != 1:
                for i in range(0, math.ceil((len(data)-1)/2)):
                    fields.append(empty_field)
                    fields.extend(row_for_class(data[i*2+1], data[i*2+2] if i*2+2 != len(data) else None))
            for field in fields:
                embedded_msg.add_field(**field)


        # Vertretungsplan für alle Klassen
        embedded_msg = discord.Embed(title='Vertretungsplan',
                                    description='Hier siehst du deine heutigen Vertretungen')
        

        if replacements is None or replacements == {}:
            fields = [{'name': '**Keine Vertretungen heute...**', 'value': '', 'inline': False}]
        else:
            fields = []
            for rep_class in replacements.keys():
                data = sorted(replacements[rep_class], key=lambda e: e['lesson'])
                # abfragen ob es eine Info gibt
                noinfo = True in [True if 'info_text' in item else None for item in data]

                # erstes Item, mit den Keys
                f_item = data[0] # first item, used for the header
                table = [
                    mk_field(rep_class, None, False),
                    empty_field,
                    mk_field('**Stunde**', f_item['lesson']),
                    mk_field('**Lehrer**', f"~~{f_item['teacher']}~~{(' ' + f_item['replacing_teacher']) if 'replacing_teacher' in f_item else ''}"),
                    mk_field('**Fach**', f_item['subject']),
                    mk_field('**Raum**', f_item['room']),
                    # hier kommt das Info Feld hin, wenn es eins gibt!
                    mk_field('**Art**', f_item['type_of_replacement'])
                ]
                if noinfo:
                    table.insert(-1, mk_field('**Info**', f_item['info_text']))
                del f_item

                if len(data) != 1:
                    for f_item in data[1:]:
                        row = [
                            mk_field(None, f_item['lesson']),
                            mk_field(None, f"~~{f_item['teacher']}~~{(' ' + f_item['replacing_teacher']) if 'replacing_teacher' in f_item else ''}"),
                            mk_field(None, f_item['subject']),
                            mk_field(None, f_item['room']),
                            # hier kommt das Info Feld hin, wenn es eins gibt!
                            mk_field(None, f_item['type_of_replacement'])
                        ]

                        if noinfo:
                            row.insert(-1, mk_field(None, f_item['info_text']))
                        table.extend(row)

                fields.extend(table)
        for field in fields:
            embedded_msg.add_field(**field)

        await msg.channel.send(embed=embedded_msg)

try:
    client.run(os.environ['BOT_TOKEN'] if 'BOT_TOKEN' in os.environ else open('token_secret', 'r').readlines()[0])
except:
    print("error")

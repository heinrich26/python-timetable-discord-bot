import discord, os
from timetable_parser import get_replacements, pages


empty_field = {'name': '\u200b', 'value': '\u200b', 'inline': False}

def mk_field(name='\u200b', value='\u200b', inline: bool=True) -> dict:
    return {'name': name if name else '\u200b', 'value': value if value else '\u200b', 'inline': inline}

client = discord.Client()

@client.event
async def on_ready():
    print(f"We've logged in as {client.user}")

@client.event
async def on_message(msg):
    if msg.author == client.user: return


    text = msg.content
    if text.startswith('/vplan') or text.startswith('/vertretungsplan') or text.startswith('!vplan') or text.startswith('!vertretungsplan'):
        args = text.split(' ', 1)
        if len(args) > 2:
            await msg.channel.send('**Ungültige Argumente!**\nVersuch mal `!vplan <Klasse>` oder `!vplan help`!')
            return
        if len(args) == 2 and args[1] == 'help':
            help_embed = discord.Embed(title='**Vertretungsplan Hilfe**',
                                        description='Hier findest du alle wichtigen Commands für den Vertretungsplan!')
            help_embed.add_field('**Verwendung:** `!vplan [Optionen]`',
                                    '`ohne Args` Zeigt den kompletten Plan\n`... help` Zeigt diese Info\n`... <Klasse>` Zeigt den Plan für eine Klasse\n`... klassen` Zeigt alle Klassen die heute Vertretung haben')
            await msg.channel.send(embed=help_embed)
            return

        embedded_msg = discord.Embed(title='Vertretungsplan',
                                    description='Hier siehst du deine heutigen Vertretungen')
        replacements = get_replacements()

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

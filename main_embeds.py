import os
from discord import Embed, Client, Message, Intents
from discord_slash import SlashCommand

from attachment_database import ImageDatabase
from timetable_parser import DEFAULT_URL, Page
from replacement_types import ReplacementType, PlanPreview
from preview_factory import create_vplan_message

EMPTY_FIELD = {'name': '\u200b', 'value': '\u200b', 'inline': False}

DEFAULT_FOOTER = {'text': 'Alle Angaben ohne Gewähr! Aber mit Gewehr. '}

INVITE_LINK = 'https://discord.com/api/oauth2/authorize?client_id=489087343589064704&permissions=268594240&scope=bot'


def build_plan(key: str, replacements: ReplacementType, preview: PlanPreview) -> tuple[str, list, Embed, tuple[bool, bool]]:
    '''Returns everything needed to send a Replacementplan as Message for the given Data'''
    # embed = class_vplan(key, replacements)
    embed = Embed(title=f'**Vertretungsplan der {key}**',
                  description='Hier siehst du deine heutigen Vertretungen:')
    embed.set_footer(**DEFAULT_FOOTER)

    files: list = []
    thumbnail = img_db.get_icon(key)

    known_icon = isinstance(thumbnail, str)
    if known_icon:
        embed.set_thumbnail(url=thumbnail)
    else:
        embed.set_thumbnail(url=f'attachment://{thumbnail.filename}')
        files.append(thumbnail)

    generated_plan = isinstance(preview, str)

    if preview is not None:
        if generated_plan:
            embed.set_image(url=preview)
        else:
            embed.set_image(url=f'attachment://{preview.filename}')
            files.append(preview)

    return key, files, embed, (known_icon, generated_plan)


def update_database_from_msg(key: str, message: Message, bools: tuple[bool, bool]) -> None:
    '''Adds the Attachment Links from the given Message to the Database'''
    if not bools[0]:
        img_db.set_attachment(key, message.embeds[0].thumbnail.url)

    if not bools[1]:
        link = message.embeds[-1].image.url
        img_db.set_attachment(key, link, liliplan.times[key])
        liliplan.previews[key] = link


def sort_classes(classes: list[str]) -> list[str]:
    '''Sorts Classes by their Identifiers/Names'''
    def comp(key: str):
        i = 0
        while key[:i + 1].isnumeric():
            i += 1
        return key[:i], key[i:]

    return sorted(classes, key=comp)


def check_last_modified() -> None:
    '''Deletes the Database when the Code has changed'''
    database = './attachments.db'
    if not os.path.exists(database):
        return

    files = ('main.py', 'preview_factory.py',
             'timetable_parser.py', 'attachment_database.py')
    db_last_mod = os.path.getmtime(database)
    for file in files:
        if db_last_mod < os.path.getmtime(file):
            os.remove(database)
            break


if __name__ == "__main__":
    # remove the database, if it's older than the Source Code
    check_last_modified()

    img_db = ImageDatabase()
    liliplan = Page(DEFAULT_URL, database=img_db)

    client = Client(intents=Intents.all())
    slash = SlashCommand(client, sync_commands=True)

    @client.event
    async def on_ready():
        '''Called when the Bot is ready'''
        print(f"We've logged in as {client.user}")

    @slash.slash(name='vplan', options=[
                                {
                                    'name': 'klasse',
                                    'description': 'Wähle eine Klasse',
                                    'type': 3,
                                    'required': False
                                }])
    async def send_plan(context, klasse):
        data = liliplan.get_plan_for_class(klasse)

        if data is None or data[1] is {}:
            embedded_msg = Embed(title='Vertretungsplan',
                                 description='Hier siehst du deine heutigen Vertretungen')
            embedded_msg.add_field(name='**Keine Vertretungen heute...**',
                                   value='\u200b', inline=False)
            embedded_msg.set_footer(**DEFAULT_FOOTER)

            # Send
            context.send(embed=embedded_msg)
        else:
            for msg in create_vplan_message(data[1], data[0], img_db):
                await context.send(**msg)


    @client.event
    async def on_message(msg):
        '''Called when the Bot intercepts a message'''
        if msg.author == client.user:
            return

        text = msg.content

        # ignore messages not starting with our Command Name!
        if not (text.startswith('/vplan') or
                text.startswith('/vertretungsplan') or
                text.startswith('!vplan') or
                text.startswith('!vertretungsplan')):
            return

        args = text.split(' ')
        if len(args) > 1:
            args[1] = args[1].lower()

        # Vertretungen abfragen
        if len(args) > 2:  # too many Arguments
            async with msg.channel.typing():
                await msg.channel.send('**Ungültige Argumente!**\nVersuch mal `!vplan <Klasse>` oder `!vplan help`!')
        elif len(args) == 1:
            # sending the plan for everyone!
            async with msg.channel.typing():
                replacements, previews = liliplan.get_plan_for_all()

                if replacements is None or \
                   replacements == {}:  # awww, you dont have replacements! How sad!
                    # Assemble the Embed
                    embedded_msg = Embed(title='Vertretungsplan',
                                         description='Hier siehst du deine heutigen Vertretungen')
                    embedded_msg.add_field(name='**Keine Vertretungen heute...**',
                                           value='\u200b', inline=False)
                    embedded_msg.set_footer(**DEFAULT_FOOTER)

                    # Send
                    msg.channel.send(embed=embedded_msg)
                else:
                    for item in replacements.items():
                        key, files, embed, bools = build_plan(
                            item[0], [], previews[item[0]])
                        sent_msg = await msg.channel.send(files=files, embed=embed)
                        update_database_from_msg(key, sent_msg, bools)
        elif args[1] in ('help', 'h'):  # send an info message to the channel
            async with msg.channel.typing():
                help_embed = Embed(title='**__Vertretungsplan Hilfe__**',
                                   description='Hier findest du alle wichtigen Commands für den Vertretungsplan!')
                help_embed.add_field(name='**Verwendung:** `!vplan [Optionen]`',
                                     value=('`ohne Args` Zeigt den kompletten Plan\n'
                                            '`... help` Zeigt diese Info\n'
                                            '`... <Klasse>` Zeigt den Plan für eine Klasse\n'
                                            '`... klassen` Zeigt alle Klassen die heute Vertretung haben'))
                await msg.channel.send(embed=help_embed)
        # send all classes that have replacements at this day!
        elif args[1] in ('klassen', 'classes', 'list', 'liste'):
            await msg.channel.trigger_typing()
            info_embed = Embed(title='**Klassen die heute Vertretung haben**:',
                               description=f"`{'`, `'.join(liliplan.get_classes())}`\n\n Verwende `!vplan <Klasse>` um einen bestimmten Plan zu sehen!")
            info_embed.set_footer(**DEFAULT_FOOTER)
            await msg.channel.send(embed=info_embed)
        elif args[1] == 'invite':  # send an invitation Link
            await msg.channel.send(f"Du willst den Bot auch auf deinem Server haben?\n\nLad ihn hiermit ein: {INVITE_LINK}")
        else:  # Send the plan for one Class
            await msg.channel.trigger_typing()
            data = liliplan.get_plan_for_class(args[1])
            if data is None:
                embedded_msg = Embed(title='Vertretungsplan',
                                     description='Hier siehst du deine heutigen Vertretungen')
                embedded_msg.add_field(name='**Keine Vertretungen heute...**',
                                       value='\u200b', inline=False)
                embedded_msg.set_footer(**DEFAULT_FOOTER)

                # Send
                msg.channel.send(embed=embedded_msg)
            else:
                # key, files, embed, bools = build_plan(*data)
                # sent_msg = await msg.channel.send(files=files, embed=embed)
                # update_database_from_msg(key, sent_msg, bools)
                await msg.channel.send()

    client.run(os.environ['BOT_TOKEN'] if 'BOT_TOKEN' in os.environ else open(
        'token_secret', 'r', encoding='utf-8').readlines()[0])

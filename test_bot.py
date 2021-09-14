from discord import Client, Intents, Embed
from discord_slash import SlashCommand
from discord_slash.client import commands



client = Client(intents=Intents.all())
slash = SlashCommand(client, sync_commands=True)

@client.event
async def on_ready():
    print('Ready!')

EMBEDS: list[Embed] = [Embed(title='1st embed', description='Hello as well'), Embed(title='2nd Embed', description='Hellko')]


@slash.slash(name="mycommand")
async def _ping(context): # Defines a new "context" (context) command called "mycommand."
    await context.send(embeds=EMBEDS)


client.run("ODg3MDA2Mjc1MjQ5MDA4NzMx.YT929w.nQXSWzmPXEyVrBrwtjPY4TUCP10")

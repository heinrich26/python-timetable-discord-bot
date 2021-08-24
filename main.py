import discord, os


client = discord.Client()

@client.event
async def on_ready():
    print(f"We've logged in as {client.user}")

@client.event
async def on_message(msg):
    if msg.author == client.user: return


    text = msg.content
    if text.startswith('/vplan'):
        await msg.channel.send('Dein Vertretungsplan:')

try:
    client.run(os.environ['BOT_TOKEN'] if 'BOT_TOKEN' in os.environ else open('token_secret', 'r').readlines()[0])
except:
    print("error")

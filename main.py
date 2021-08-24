import discord


token = 'NDg5MDg3MzQzNTg5MDY0NzA0.W5fYFQ.PICXIKcK8nGqf5sk0M_7QWs32ls'

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

client.run(token)

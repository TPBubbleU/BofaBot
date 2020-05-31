import BotToken
import discord, time, re, asyncio
from discord.ext import commands
import youtube_dl
import mysql.connector

bot = commands.Bot(command_prefix='$')

@bot.event
async def on_ready():
    print('Bot 2 Logged on as', bot.user)

@bot.event
async def on_message(message):
    # don't respond to ourselves
    if message.author == bot.user:
        return
    p = re.compile('bofa walkon', re.IGNORECASE)
    if p.match(message.content):
        p1 = re.compile('url=([^\s]*)')
        m1 = p1.search(message.content)
        p2 = re.compile('playtime=([^\s]*)')
        m2 = p2.search(message.content)
        if m1 and m2:
            mydb = mysql.connector.connect(host="localhost",user="root",passwd="w")
            cursor = mydb.cursor()
            cursor.execute("USE discord;")
            cursor.execute("DELETE FROM walkon WHERE username = \""+str(message.author)+"\";")
            sql_insert_query = "INSERT INTO walkon VALUES(\""+str(message.author)+"\",\""+m1.group(1)+"\","+m2.group(1)+");"
            print(sql_insert_query)
            cursor.execute(sql_insert_query)
            mydb.commit()
            cursor.close()
            mydb.close()
            await message.channel.send('I got you')
    elif 'bofa' in message.content:
        await message.channel.send('Whats bofa?')

bot.run(BotToken.Token)

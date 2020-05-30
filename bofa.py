
import discord, asyncio, youtube_dl
import time, re, mysql.connector
from datetime import datetime 
from discord.ext import commands

TOKEN = 'Njk0NzM5NTcxNzQ5MTU5MDcy.XoQA2g.SnRN049vlX4TN74UhUMtOEceu7c'
bot = commands.Bot(command_prefix='!')

youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'cookiefile': '/home/cheesy_george/cookies.txt',
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)



def get_proper_channel(channel_name):
    for channel in bot.get_all_channels():
        if channel.name == channel_name and channel.type is discord.ChannelType.voice:
            return channel

def get_proper_member(mentionstr):
    for i in bot.get_all_members():
        if mentionstr == i.mention:
            return i
    else:
        print("Something went wrong you shouldn't have got here")


def get_mysql_db():
    mydb =  mysql.connector.connect(host="localhost",user="root",passwd="w")
    cursor = mydb.cursor()
    cursor.execute("USE discord;")
    return cursor, mydb


def close_mysql_db(mydb, cursor, commit):
    if commit:
        mydb.commit()
    cursor.close()
    mydb.close()


@bot.command()
async def sipadd(ctx, sips: int, mention=None):
    print('trying to sipadd over here')
    cursor, mydb = get_mysql_db()
    
    cursor.execute("SELECT DISTINCT Username FROM sippin WHERE TIMESTAMPDIFF(HOUR,ts,CURRENT_TIMESTAMP) < 9")
    records = cursor.fetchall()
    usernames = [i[0] for i in records]

    print(mention)

    if mention is not None:
        member = get_proper_member(mention)
        user = bot.get_user(member.id)

        if not(str(user) in usernames):
            await ctx.send(str(mention) + " isn't even sippin though")
            return close_mysql_db(mydb=mydb, cursor=cursor, commit=False)

    if not records:
        await ctx.send("Nobody currently sippin though")
        return close_mysql_db(mydb=mydb, cursor=cursor, commit=False)
    
    cursor.execute("SELECT Username, CurrentTotal FROM sips")
    records = cursor.fetchall()
    CTUsers = [i[0] for i in records]

    if mention is not None:
        # doing things for a single sipper
        for i in CTUsers:
            if i == str(user):
                break
        else:
            print("adding user " + str(user) + " into sips table")
            cursor.execute("INSERT INTO sips VALUES ('" + i + "',0)")
        cursor.execute("UPDATE sips SET CurrentTotal = CurrentTotal + " + str(sips) + " WHERE Username IN ('" + str(user) + "')")
        await ctx.send(str(sips) + " sips added to " + mention)
    else:
        # doing things for all sippers
        for i in usernames:
            for j in CTUsers:
                if i == j:
                    break
            else:
                print("adding user " + i + " into sips table")
                cursor.execute("INSERT INTO sips VALUES ('" + i + "',0)")
        cursor.execute("UPDATE sips SET CurrentTotal = CurrentTotal + " + str(sips) + " WHERE Username IN ('" + "','".join(usernames) + "')")
        await ctx.send(str(sips) + " sips added to " + " and ".join(usernames))
    close_mysql_db(mydb=mydb, cursor=cursor, commit=True)
    
    
@bot.command()
async def whosesippin(ctx):
    print('trying to see whose sipping over here')
    cursor, mydb = get_mysql_db()
    cursor.execute("SELECT Username FROM sips")
    sippers = [i[0] for i in cursor.fetchall()]
    
    newmessage = await ctx.send("Who is all sipping? Are you sipping? Hit me with that 🇾 if you are.")
    await newmessage.add_reaction("🇾")
    await newmessage.add_reaction("🇳")
    CurrentSippers = []
    try:
        for i in range(10):
            reaction, user = await bot.wait_for('reaction_add', timeout=30)
            print("Got a react from " + str(user))
            
            # Lets get them added to the count table
            if not (str(user) in sippers):
                print("adding user " + str(user) + " into sips table")
                cursor.execute("INSERT INTO sips VALUES ('" + str(user) + "',0)")
            
            CurrentSippers.append(str(user))
            if reaction.emoji == "🇾":
                print("Adding user " + str(user) + " to the sippin table")
                cursor.execute("INSERT INTO sippin VALUES ('" + str(user) + "', '" + str(datetime.now()) + "')")
    except asyncio.TimeoutError:
        await ctx.send("I've got the following users as Sippin " + "','".join(CurrentSippers))
    close_mysql_db(mydb=mydb, cursor=cursor, commit=True)
    
    
@bot.command()
async def mysips(ctx, mention=None):
    print('trying to check someones sips')
    cursor, mydb = get_mysql_db()

    if mention is not None:
        member = get_proper_member(mention)
        user = bot.get_user(member.id)
    else:
        user = str(ctx.author)

    cursor.execute("SELECT CurrentTotal FROM sips WHERE Username = '" + str(user) + "'")
    record = cursor.fetchone()
    if not record:
        newmessage = await ctx.send("Are you even sippin though?")
        await newmessage.add_reaction("🇾")
        await newmessage.add_reaction("🇳")
        try:
            for i in range(10):
                reaction, user = await bot.wait_for('reaction_add', timeout=30)
                if user == bot.user:
                    continue
                print("Got a react from " + str(user))
                if str(user) == str(ctx.author):
                    if reaction.emoji == "🇾":
                        print("Adding user " + str(user) + " to the sippin table")
                        cursor.execute("INSERT INTO sippin VALUES ('" + str(user) + "', '" + str(datetime.now()) + "')")
                        cursor.execute("INSERT INTO sips VALUES ('" + str(user) + "',0)")
                        await ctx.send(str(ctx.author) + " sips are currently at 0 ")
                        return
                    break
        except asyncio.TimeoutError:
            print('We timed out on the question "Are you even sippin though?"')
        await ctx.send("I guess you aren't sippin then")
        close_mysql_db(mydb=mydb, cursor=cursor, commit=True)
        return
    await ctx.send(str(user) + " sips are currently at " + str(record[0]))
    close_mysql_db(mydb=mydb, cursor=cursor, commit=False)
    

@bot.command()
async def sipclear(ctx, mention=None):
    print('trying to sipclear over here')
    cursor, mydb = get_mysql_db()

    if mention is not None:
        member = get_proper_member(mention)
        user = bot.get_user(member.id)
    else:
        user = str(ctx.author)

    cursor.execute("UPDATE sips SET CurrentTotal = 0 WHERE Username IN ('" + str(user) + "')")
    close_mysql_db(mydb=mydb, cursor=cursor, commit=True)
    await ctx.send(str(user) + "'s sips have been cleared")

@bot.event
async def on_ready():
    print('Logged on as', bot.user)

@bot.event
async def on_voice_state_update(member, before, after):
    voice_channel = get_proper_channel('bitches')
    if before.channel is None and after.channel is voice_channel and member != bot.user:
        print('User ' + str(member) + ' has joined the channel')

        cursor, mydb = get_mysql_db()
        cursor.execute("SELECT url, playtime FROM walkon WHERE username = '" + str(member) + "'")
        record = cursor.fetchone()
        if not record:
            print("No record on file for User")
            close_mysql_db(mydb=mydb, cursor=cursor, commit=False)
            return
            
        url = record[0]
        playtime = record[1]
        close_mysql_db(mydb=mydb, cursor=cursor, commit=False)

        for i in bot.voice_clients:
            await i.disconnect()
        vc = await voice_channel.connect()

        source = await YTDLSource.from_url(url, loop=bot.loop)
        vc.play(source, after=lambda e: print('Player error: %s' % e) if e else None)
        time.sleep(playtime)
        for i in range(30):
            vc.source.volume = vc.source.volume - (0.5/30)
            time.sleep(0.1)
        vc.stop()
        await vc.disconnect()

bot.run(TOKEN)

import Config
import discord, asyncio, youtube_dl
import time, re, mysql.connector
from datetime import datetime 
from discord.ext import commands

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
    mydb =  mysql.connector.connect(host=Config.mysqlhost, user=Config.mysqluser, passwd=Config.mysqlpasswd)
    cursor = mydb.cursor()
    cursor.execute("USE discord;")
    return cursor, mydb


def close_mysql_db(mydb, cursor, commit):
    if commit:
        mydb.commit()
    cursor.close()
    mydb.close()


async def areYouEvenSippinThough(ctx, cursor, mydb):
    # We are here because a User has activated a command when they shouldn't have
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
                    cursor.execute("INSERT INTO sips VALUES ('" + str(user) + "', 0, '" + str(datetime.now()) + "')")
                    await ctx.send("Nice, " + str(ctx.author) + " is now sippin")
                    return
                break
    except asyncio.TimeoutError:
        print('We timed out on the question "Are you even sippin though?"')
    await ctx.send("I guess you aren't sippin then")
    close_mysql_db(mydb=mydb, cursor=cursor, commit=True)


@bot.command()
async def sipadd(ctx, sips: int, mention=None):
    print('Trying to sipadd over here')
    cursor, mydb = get_mysql_db()
    
    # Get sip data from the database
    cursor.execute("SELECT DISTINCT Username, CurrentTotal, TIMESTAMPDIFF(HOUR,last_sip,CURRENT_TIMESTAMP) FROM sips")
    records = cursor.fetchall()
    usernames = [i[0] for i in records]
    last5HoursUsers = [i[0] for i in records if int(i) >= 5]

    # If there is a Mention we need to make sure the user is setup in the database
    if mention is not None:
        member = get_proper_member(mention)
        user = bot.get_user(member.id)
        
        if not(str(user) in usernames):
            print("Setting up User in the database")
            cursor.execute("INSERT INTO sips VALUES ('" + str(user) + "', 0, '" + str(datetime.now()) + "')")

    # Lets early exit if there isn't a mention and no one has a last sip in the last 5 hours
    if mention is None and not last5HoursUsers:
        await ctx.send("Nobody currently sippin though")
        return close_mysql_db(mydb=mydb, cursor=cursor, commit=False)

    # Lets add some sips
    
    # Doing things for a single sipper
    if mention is not None:
        cursor.execute("UPDATE sips SET CurrentTotal = CurrentTotal + " + str(sips) + " WHERE Username IN ('" + str(user) + "')")
        await ctx.send(str(sips) + " sips added to " + mention)
    # Doing things for all sippers
    else:
        cursor.execute("UPDATE sips SET CurrentTotal = CurrentTotal + " + str(sips) + " WHERE Username IN ('" + "','".join(last5HoursUsers) + "')")
        await ctx.send(str(sips) + " sips added to " + " and ".join(last5HoursUsers))
    close_mysql_db(mydb=mydb, cursor=cursor, commit=True)
    
    
@bot.command()
async def whosesippin(ctx):
    print('Trying to see whose sipping over here')
    cursor, mydb = get_mysql_db()
    
    # Get sip data from the database
    cursor.execute("SELECT Username FROM sips")
    sippers = [i[0] for i in cursor.fetchall()]
    
    # Display Message and add reactions and wait for users to add thier own
    newmessage = await ctx.send("Who is all sipping? Are you sipping? Hit me with that 🇾 if you are.")
    await newmessage.add_reaction("🇾")
    await newmessage.add_reaction("🇳")
    CurrentSippers = []
    try:
        for i in range(10):
            reaction, user = await bot.wait_for('reaction_add', timeout=30)
            if user == bot.user:
                continue
                            
            if reaction.emoji == "🇾":
            
                # Lets get them added to the count table
                if not (str(user) in sippers):
                    print("adding user " + str(user) + " into sips table")
                    cursor.execute("INSERT INTO sips VALUES ('" + str(user) + "', 0, '" + str(datetime.now()) + "')")
                
                CurrentSippers.append(str(user))
            
                print("Adding user " + str(user) + " to the sippin table")
                cursor.execute("UPDATE sips SET last_sip = '" + str(datetime.now()) + "'")
    except asyncio.TimeoutError:
        await ctx.send("I've got the following users as Sippin " + " and ".join(CurrentSippers))
    close_mysql_db(mydb=mydb, cursor=cursor, commit=True)
    
    
@bot.command()
async def mysips(ctx, mention=None):
    print('Trying to check someones sips')
    cursor, mydb = get_mysql_db()

    # Setup the correct user variable
    if mention is not None:
        member = get_proper_member(mention)
        user = bot.get_user(member.id)
    else:
        user = str(ctx.author)

    # Get database information
    cursor.execute("SELECT CurrentTotal FROM sips WHERE Username = '" + str(user) + "'")
    record = cursor.fetchone()
    if not record:
        areYouEvenSippinThough(ctx, cursor, mydb)
        return
        
    # Display information back out
    await ctx.send(str(user) + " sips are currently at " + str(record[0]))
    close_mysql_db(mydb=mydb, cursor=cursor, commit=False)
    

@bot.command()
async def sipclear(ctx, sips:int=None, mention=None):
    print('trying to sipclear over here')
    cursor, mydb = get_mysql_db()
    
    # Setup the correct user variable
    if mention is not None:
        member = get_proper_member(mention)
        user = bot.get_user(member.id)
    else:
        user = str(ctx.author)

    # Get database information
    cursor.execute("SELECT CurrentTotal FROM sips WHERE Username = '" + str(user) + "'")
    record = cursor.fetchone()
    if not record:
        areYouEvenSippinThough(ctx, cursor, mydb)
        return
    
    # Setup the newTotal Variable that we will later put into the database
    if sips:
        # Check if user has cleared more sips that currently in database and lower it
        if sips > record[0]: 
            sips = record[0]
        newTotal = 'CurrentTotal - ' + str(sips)
    else:
        newTotal = '0'
    
    cursor.execute("UPDATE sips SET CurrentTotal = " + newTotal + " WHERE Username IN ('" + str(user) + "')")
    close_mysql_db(mydb=mydb, cursor=cursor, commit=True)
    
    # Display information back to user 
    if sips:
        await ctx.send(str(user) + "'s sips have been cleared")
    else:
        await ctx.send(str(user) + "'s sips have been lowered by " + str(sips))

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

bot.run(Config.Token)

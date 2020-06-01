import Config
import discord, time, re, asyncio
from discord.ext import commands
import youtube_dl, mysql.connector
from bofa import get_mysql_db, close_mysql_db

bot = commands.Bot(command_prefix='$')

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_options = {
	'username': Config.ytldusername,
	'password': Config.ytldpassword,
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_options)

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
        m1 = re.compile('url=([^\s]*)').search(message.content)
        m2 = re.compile('playtime=([^\s]*)').search(message.content)
        if m1 and m2:
            cursor, mydb = get_mysql_db()
            cursor.execute("DELETE FROM walkon WHERE username = \""+str(message.author)+"\";")
            sql_insert_query = "INSERT INTO walkon VALUES(\""+str(message.author)+"\",\""+m1.group(1)+"\","+m2.group(1)+");"
            print(sql_insert_query)
            cursor.execute(sql_insert_query)
            close_mysql_db(mydb=mydb, cursor=cursor, commit=False)
            await message.channel.send('I got you')
    elif 'bofa' in message.content:
        await message.channel.send('Whats bofa?')

		
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

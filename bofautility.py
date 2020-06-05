import Config, discord, mysql.connector, re

def get_proper_channel(channel_name):
    for channel in bot.get_all_channels():
        if channel.name == channel_name and channel.type is discord.ChannelType.voice:
            return channel


def get_proper_member(bot, mentionstr):
    print("Trying to find " + mentionstr)
    for guild in bot.guilds:
        print("Looking at the guild of " + str(guild))
        for member in guild.members:
            print(str(member) + " has the mention of " + str(member.mention) )
            if re.sub(re.compile('[<>@!]'), "",mentionstr) == re.sub(re.compile('[<>@!]'), "",member.mention):
                return member
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



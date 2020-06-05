import Config
import discord, asyncio, time, re, mysql.connector
from datetime import datetime 
from discord.ext import commands
import bofautility 


bot = commands.Bot(command_prefix='!')


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
                    cursor.execute("INSERT INTO sips VALUES ('" + str(user) + "', 0, now())")
                    await ctx.send("Nice, " + str(ctx.author) + " is now sippin")
                    return
                break
    except asyncio.TimeoutError:
        print('We timed out on the question "Are you even sippin though?"')
    await ctx.send("I guess you aren't sippin then")
    bofautility.close_mysql_db(mydb=mydb, cursor=cursor, commit=True)


@bot.command()
async def sipadd(ctx, sips: int, mention=None):
    print('Trying to sipadd over here')
    cursor, mydb = bofautility.get_mysql_db()
    
    # Get sip data from the database
    cursor.execute("SELECT DISTINCT Username, CurrentTotal, TIMESTAMPDIFF(HOUR,last_sip,CURRENT_TIMESTAMP) FROM sips")
    records = cursor.fetchall()
    usernames = [i[0] for i in records]
    last5HoursUsers = [i[0] for i in records if i[2] >= 5]

    # If there is a Mention we need to make sure the user is setup in the database
    if mention is not None:
        member = bofautility.get_proper_member(mention)
        user = bot.get_user(member.id)
        
        if not(str(user) in usernames):
            print("Setting up User in the database")
            cursor.execute("INSERT INTO sips VALUES ('" + str(user) + "', 0, now())")

    # Lets early exit if there isn't a mention and no one has a last sip in the last 5 hours
    if mention is None and not last5HoursUsers:
        await ctx.send("Nobody currently sippin though")
        return bofautility.close_mysql_db(mydb=mydb, cursor=cursor, commit=False)

    # Lets add some sips
    
    # Doing things for a single sipper
    if mention is not None:
        cursor.execute("UPDATE sips SET CurrentTotal = CurrentTotal + " + str(sips) + " WHERE Username IN ('" + str(user) + "')")
        cursor.execute("UPDATE sips SET last_sip = now() WHERE Username IN ('" + str(user) + "')")
        await ctx.send(str(sips) + " sips added to " + mention)
    # Doing things for all sippers
    else:
        cursor.execute("UPDATE sips SET CurrentTotal = CurrentTotal + " + str(sips) + " WHERE Username IN ('" + "','".join(last5HoursUsers) + "')")
        cursor.execute("UPDATE sips SET last_sip = now() WHERE Username IN ('" + "','".join(last5HoursUsers) + "')")
        await ctx.send(str(sips) + " sips added to " + " and ".join(last5HoursUsers))
    bofautility.close_mysql_db(mydb=mydb, cursor=cursor, commit=True)
    
    
@bot.command()
async def whosesippin(ctx):
    print('Trying to see whose sipping over here')
    cursor, mydb = bofautility.get_mysql_db()
    
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
                if not (str(user) not in sippers):
                    print("adding user " + str(user) + " into sips table")
                    cursor.execute("INSERT INTO sips VALUES ('" + str(user) + "', 0, now())")
                
                CurrentSippers.append(str(user))
            
                print("Adding user " + str(user) + " to the sippin table")
                cursor.execute("UPDATE sips SET last_sip = now()")
    except asyncio.TimeoutError:
        await ctx.send("I've got the following users as Sippin " + " and ".join(CurrentSippers))
    bofautility.close_mysql_db(mydb=mydb, cursor=cursor, commit=True)
    
    
@bot.command()
async def mysips(ctx, mention=None):
    print('Trying to check someones sips')
    cursor, mydb = bofautility.get_mysql_db()

    # Setup the correct user variable
    if mention is not None:
        member = bofautility.get_proper_member(mention)
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
    bofautility.close_mysql_db(mydb=mydb, cursor=cursor, commit=False)
    

@bot.command()
async def sipclear(ctx, sips:int=None, mention=None):
    print('trying to sipclear over here')
    cursor, mydb = bofautility.get_mysql_db()
    
    # Setup the correct user variable
    if mention is not None:
        member = bofautility.get_proper_member(mention)
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
    bofautility.close_mysql_db(mydb=mydb, cursor=cursor, commit=True)
    
    # Display information back to user 
    if sips:
        await ctx.send(str(user) + "'s sips have been lowered by " + str(sips))
    else:
        await ctx.send(str(user) + "'s sips have been cleared")

@bot.event
async def on_ready():
    print('Logged on as', bot.user)

bot.run(Config.Token)

import discord, re, json, random, asyncio
from datetime import datetime 
from discord.ext import commands
import concurrent.futures

bot = commands.Bot(command_prefix='!', case_insensitive=True)

@bot.command()
async def HeadsUp(ctx, *args):
	# Pre built list from http://www.getcharadesideas.com/resources/famous-people-charades-ideas-the-complete-list/
	CharacterList = ['Leonardo Da Vinci','Mother Teresa','Abraham Lincoln','Marilyn Monroe','Nelson Mandela','Margaret Thatcher','Christopher Columbus','Rosa Parks','Martin Luther King','Anne Boleyn','Muhammad Ali','Queen Victoria','Albert Einstein','Amelia Earhart','Neil Armstrong','Ron Burgundy','Rapunzel','Jack Reacher','Wonder Woman','Homer Simpson','Hermione Granger','James Bond','Lois Lane','Indiana Jones','Lara Croft','Luke Skywalker','Dorothy Gale','Samwise Gamgee','Sarah Connor','Agent J','Michael Jordan','Serena Williams','Conor McGregor','Mia Hamm','Cristiano Ronaldo','Annika Sörenstam','Rodger Federer','Ronda Rousey','Brian O’Driscoll','Mao Asada','Rory McIlroy','Simone Biles','Michael Phelps','Rebecca Adlington','Usain Bolt','Justin Timberlake','Gwen Stefani','Niall Horan','Britney Spears','Kanye West','Beyoncé Knowles','Rod Stewart','Katie Perry','Anthony Kiedis','Adele','Robbie Williams','Samantha Mumba','Hozier','Susan Boyle','Ed Sheeran','Will Smith','Helen Mirren','Jude Law','Melissa McCarthy','Tom Cruise','Scarlett Johansson','Robert Downey Jr.','Sandra Bullock','Liam Neeson','Emma Watson','Matt Damon','Jodie Foster','Ryan Reynolds','Angelina Jolie','Colin Firth']
	users = []
	# Lets look at a everything that was sent with this command
	for arg in args:
		# If things look like it was a tagged user
		if re.compile('<.*>').search(str(arg)):
			# Lets extact the user id, get the user and add them to a list
			users.append(bot.get_user(int(re.sub(re.compile('[<>@!]'), "", arg))))
		# If it looks likt a json object containing data, we'll use this as our list
		if re.compile('{"data":\[.*\]').search(str(arg)):
			CharacterList = json.loads(arg)['data']
	
	userPersonAssignmentList = [
		# This will be a list of objects that look like this
		# { 
		#    'user' : The user we are talking about 
		#	 'person' : The character that person will be guessing
		#	 'assigner' : If we aren't going off of a character list this is who will be providing 
		# } 
	]
	
	# Lets describe how we are going to pick which users will pick the others characters
	async def UsertoUserAssignment(users, retry=0):
		userPersonAssignmentList = []
		# usersNotYetAssigned is a copy of our users list we will use later
		usersNotYetAssigned = users.copy()
		# Loop through our users list
		for user in users:
			# It's important to know of a weird edge case here, let me describe a basic version of it
			# There is 3 users. User1 assigner is User2. User2 assigner is User1
			# We can't assign User3 because there isn't a person left to assign him other than himself which is bad 
			# We try try to shuffle and assign 10 times
			for i in range(10):
				random.shuffle(usersNotYetAssigned)
				if usersNotYetAssigned[-1] != user:
					userPersonAssignmentList.append({'user':user, 'assigner':usersNotYetAssigned.pop()})
					break
			# If the shuffling and attemped assignment fails 10 times lets just start from scratch
			else:
				# If we have retryed too many times lets just stop
				if retry >= 5:
					ctx.send("Something Absolutely Horrible Happened")
					return 
				# Other wise Lets retry this
				else:
					UsertoUserAssignment(users, retry+1)
				
		# Lets define a coroutine to send messages out to users and wait for a response back
		async def userPersonAssignmentListLooper(i):
			await i['assigner'].send("I'm awaiting a message back from you with who " + str(i['user']) + " will guess")
			personMessage = await bot.wait_for('message', check=lambda x: x.author == i['assigner'])
			i['person'] = personMessage.content
		
		# Lets make a list of these coroutines 
		messagesGoingOutToPeople = []
		for i in userPersonAssignmentList:
			messagesGoingOutToPeople.append(userPersonAssignmentListLooper(i))
		
		# Send out them messages and await responses 
		await asyncio.gather(*messagesGoingOutToPeople)
	
	
	# Lets look to see if the keywords 'use' and 'list' are passed 
	if "use" in args and "list" in args:
		random.shuffle(CharacterList)
		for user in users:
			userPersonAssignmentList.append({'user':user, 'person':CharacterList.pop()})
	# We know we are source the character guess from our users
	else:
		UsertoUserAssignment(users)
	
	# Loop through our assignment list
	for i in userPersonAssignmentList:
		# If we have an assigner lets put that in our message back to the user
		message = str(i['assigner']) + " choose your character for you" if 'assigner' in i.keys() else ""
		# Lets look at every other thing in our list and append to our message
		for j in userPersonAssignmentList:
			if i['user'] == j['user']:
				continue
			message = message + "\n" + str(j['user']) + "'s person is " + j['person']
		# Send the message out to the user
		await user.send(message)

@bot.event
async def on_ready():
	print('Logged on as', bot.user)

bot.run('NzIzNjg3MDk4NzQxNDI0MTI4.Xu1ThQ.Zak5si1nJI1PyglinUTPAzKuMM0')
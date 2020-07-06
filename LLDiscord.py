import discord, re
from datetime import datetime 
from discord.ext import commands
from LL import LLGame

bot = commands.Bot(command_prefix='!', case_insensitive=True)
game = None

async def SendMessages(ctx):
	messages = [i['message'] for i in game.messages if i['who'] == 'all']
	await ctx.send('\n'.join(messages))   
	whoToMessage = []
	for i in game.messages:
		if i['who'] not in whoToMessage and i['who'] != 'all':
			whoToMessage.append(i['who'])
	for i in whoToMessage:
		privatemessages = [j for j in game.messages if j['who'] == i]
		await privatemessages[0]['who'].discordUser.send('\n'.join(j['message'] for j in privatemessages))
	game.messages = []

@bot.command(brief="Start a new game of Love Letter.",
             description="Start a new game of Love Letter. Use the keyword premium to play with the premium cards")
async def NewGame(ctx, *args):
	global game
	users = []
	premium = False
	for arg in args:
		if re.compile('<.*>').search(str(arg)):
			users.append(bot.get_user(int(re.sub(re.compile('[<>@!]'), "", arg))))
		else:
			try:
				if arg.upper() == "PREMIUM":
					premium = True
					print("Oh It's Premium")
			except:
				print("Well that messed up")
	game = LLGame(users, premium)
	await SendMessages(ctx)

@bot.command(brief="The command used to progess the game",
             description="The command used to progess the game. Please supply the proper number as an argument based on previous game text")
async def Action(ctx, text):
	game.Action(str(ctx.author), text)
	await SendMessages(ctx)

@bot.command(brief="Get the current Score of the Love Letter Game.")
async def Score(ctx):
	game.WhatsTheScore()
	await SendMessages(ctx)

@bot.command(brief="Get what the game is currently waiting for.")
async def WhatsNext(ctx):
	game.WhatsNext()
	await SendMessages(ctx)
	
@bot.command(brief="Get some descriptions of the cards in your hand.")
async def CardDescription(ctx):
	game.CardDescription(ctx.author)
	await SendMessages(ctx)

@bot.event
async def on_ready():
	print('Logged on as', bot.user)

bot.run('NzIzNjg3MDk4NzQxNDI0MTI4.Xu1ThQ.Zak5si1nJI1PyglinUTPAzKuMM0')

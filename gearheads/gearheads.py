import pysmash
import pandas as pd
import numpy as np

smash = pysmash.SmashGG()

tournament = 'tsundere-thursdays-xi'
event = 'guilty-gear-xrd-rev-2'
#tournament = input('tournament slug: ')
#event = input('event slug: ')
smash.set_default_event(event)

players = smash.tournament_show_players(tournament)
#sets = smash.tournament_show_sets(tournament) #Unsure how overall tournament sets interact with multiple brackets
brackets = smash.tournament_show_event_brackets(tournament)
bsets = smash.bracket_show_sets(brackets['bracket_ids'][0]) #[0] will only show first bracket, need to loop through if multiple

path = 'c:\\ScriptStuff\\gearheads\\'
headout = path + 'headcount.csv'
setout = path + 'sets.txt'
brackout = path + 'brackets.txt'
playout = path + 'players.txt'

#rating update functions
def exp_score_a(rating_a, rating_b):
    return 1.0 / (1 + 10**((rating_b - rating_a)/400.0))

def rating_adj(rating, exp_score, score, games, k=10):
	if games < 20:
		k = 40
	elif rating < 2400:
		k = 20
	
	return rating + k * (score - exp_score)
	
'''
def linear_adj(rating, diff, wins, losses, games, k=10):
	if games < 20:
		k = 40
	elif rating < 2400:
		k = 20
	return rating + k/2 * (wins - losses + 1/2(diff/200.0))
	
#Linear approximation: rating = rating + K/2(W - L + 1/2(Sum of each D / C))
#Where W = total wins, L = total losses, D = (opponent rating - player rating), and C = 200
'''


# General GG class to keep track of ELO rating, games played, and number of wins. Default rating is 1500
class GuiltyPlayer(object):
	def __init__(self, id, name, rating = 1500.0, games = 0, wins = 0):
	
		self.id = id
		self.rating = rating
		self.name = name
		self.games = games
		self.wins = wins
		
	def match(self, other, result):

		exp_a = exp_score_a(self.rating, other.rating)

		if result == self.name:
			self.rating = rating_adj(self.rating, exp_a, self.games, 1)
			other.rating = rating_adj(other.rating, 1 - exp_a, self.games, 0)
			self.wins += 1
		elif result == other.name:
			self.rating = rating_adj(self.rating, exp_a, self.games, 0)
			other.rating = rating_adj(other.rating, 1 - exp_a, self.games, 1)
			other.wins += 1
			
		self.games += 1
		other.games += 1
'''		
	#method for linear approximation formula
	#list: assumed list is based on every set in tournament with the GuiltyPlayer, formatted as (opponent rating, win(1)/loss(0))
	def update(self, list):
		
		for match in list:
			diff += (match[0] - self.rating)
			if match[1] == 1:
				wins += 1
			else:
				losses += 1
		
		self.rating = linear_adj(self.rating, diff, wins, losses, self.games)
		self.games += (wins + losses)
		self.wins += wins			
'''	
#Examples:
#Cashew = GuiltyPlayer(500000, 'Cashew')
#Oreo = GuiltyPlayer(123456, 'Oreo', games = 5, wins = 4)


'''
#General process (for general sets, haven't tested if bracket sets follow same pattern):
#
#Get set data
#(set data is sorted by API with Winners going all the way through first, then Losers)
#Import stats for players in tournament, or create new stats if new player
#If set is not Grand Finals:
#Get results of set
#Update winner/loser stats
#Repeat until Grand Finals
#
#When set is Grand Finals, skip it for now
#Go to set after Grand Finals (the beginning of losers)
#Update winner/loser stats
#Repeat until end of set data (end of losers finals)
#
#Go back to Grand Finals match (now with correctly updated ELO)
#Update winner/loser stats
#
#Export player list to update csv data

#Updating stats includes updating rating, total games, and total wins
'''

#csv formatted as: (id,name,rating,games,wins)

#this code throws an error if csv is empty or there's any blank lines
#there shouldn't be any blank lines. But if there needs to be in the future, after opening the file add:
#namelist = [l for l in (line.strip() for line in f) if l]
#and modify reader:
#reader = csv.reader(namelist, delimiter=',')
gearheads = []


df = pd.read_csv(headout, header=None, names = ['id','name','rating','games','wins'])

for player in players:
	for index, row in df.loc[df['name'] == player['tag']].iterrows():
		present = 1
		gearheads.append(GuiltyPlayer(row['id'], row['name'], row['rating'], row['games'], row['wins']))
		
	if present == 1:
		present = 0
		continue
			
	gearheads.append(GuiltyPlayer(player['player_id'], player['tag']))

'''
# Old code
with open(headout, newline='') as f:
	reader = csv.reader(f, delimiter=',')
	for player in players:
		for row in reader:
			if player['player_id'] == row[0]:
				present = 1
				gearheads.append(GuiltyPlayer(row[0], row[1], row[2], row[3], row[4]))
		if present == 1:
			present = 0
			continue
			
		gearheads.append(GuiltyPlayer(player['player_id'], player['tag']))
'''	

for head in gearheads:
	print(head.id)
	print(head.name)
	print(head.rating)
	print(head.games)
	print(head.wins)
	

	
with open(brackout, 'w') as f:
	print(brackets, file=f)

with open(setout, 'w') as f:
	print(bsets, file=f)
	
with open(playout, 'w') as f:
	print(players, file=f)

	

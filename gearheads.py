import pysmash
import pandas as pd

'''
get rid of player tags for non-new players after testing is done, all calculations are done with id anyways
Grand finals is currently counted as one match even if winner's side gets reset
'''

smash = pysmash.SmashGG()

#Test tournaments
#tournament = 'tsundere-thursdays-xi'
#event = 'guilty-gear-xrd-rev-2'
#tournament = 'socal-regionals-2017-1'
#event = 'guilty-gear-xrd-rev-2'
tournament = input('tournament slug: ')
event = input('event slug: ')
smash.set_default_event(event)

players = smash.tournament_show_players(tournament)
sets = smash.tournament_show_sets(tournament) #Unsure how overall tournament sets interact with multiple brackets
brackets = smash.tournament_show_event_brackets(tournament)
bsets = []
for bracket in brackets['bracket_ids']: # Final bracket in list is Grand Finals bracket
	bsets.append(smash.bracket_show_sets(bracket))

path = 'c:\\ScriptStuff\\gearheads\\'
headout = path + 'headcount.csv'
setout = path + 'sets.txt'
brackout = path + 'brackets.txt'
playout = path + 'players.txt'

# Takes results for a single match and updates winner/loser
def match_results(game, gamers):
	for winner in gamers:
			if winner.id == game['winner_id']:
				for loser in gamers:
					if loser.id == game['loser_id']:
						winner.match(loser, game['winner_id'])
						break
				break

# Rating update functions
def exp_score_a(rating_a, rating_b):
	return 1.0 / (1 + 10**((rating_b - rating_a)/400.0))

def rating_adj(rating, exp_score, score, k):
	return rating + k * (score - exp_score)
	
'''
def linear_adj(rating, diff, wins, losses, games, k=10):
	if games < 20:
		k = 40
	elif rating < 2400:
		k = 20
	return rating + k/2 * (wins - losses + 1/2(diff/200.0))
	
# Linear approximation: rating = rating + K/2(W - L + 1/2(Sum of each D / C))
# Where W = total wins, L = total losses, D = (opponent rating - player rating), and C = 200
'''


# General GG class to keep track of ELO rating, games played, and number of wins. Default rating is 1500
# id is a string not an int
class GuiltyPlayer(object):
	def __init__(self, id, trueid, name='', rating=1500.0, games=0, wins=0):
	
		self.id = id
		self.trueid = trueid
		self.rating = rating
		self.name = name
		self.games = games
		self.wins = wins
		
	@property
	def k(self):
		if self.games < 20:
			return 40
		elif self.rating < 2400:
			return 20
		else:
			return 10
		
	def match(self, other, result):

		exp_a = exp_score_a(self.rating, other.rating)

		if result == self.id:
			self.rating = rating_adj(self.rating, exp_a, 1, self.k)
			other.rating = rating_adj(other.rating, 1 - exp_a, 0, other.k)
			self.wins += 1
		elif result == other.id:
			self.rating = rating_adj(self.rating, exp_a, 0, self.k)
			other.rating = rating_adj(other.rating, 1 - exp_a, 1, other.k)
			other.wins += 1
			
		self.games += 1
		other.games += 1
'''		
	# method for linear approximation formula
	# list: assumed list is based on every set in tournament with the GuiltyPlayer, formatted as (opponent rating, win(1)/loss(0))
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
# Examples:
# Cashew = GuiltyPlayer('500000', '999999', 'Cashew')
# Oreo = GuiltyPlayer('123456', '234567', 'Oreo', games = 5, wins = 4)
# Cashew.match(Oreo, '500000')


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

# csv formatted as: (player_id,name,rating,games,wins)
# An important note here:
#  Players are represented site-wide on smash.gg with player_id
#  However, match winners/losers are represented by a tournament-local entrant_id

# Creates a GuiltyPlayer object for every player in tournament, creating new stats or inputting existing from csv
gearheads = []
present = 0
Guilty_list = pd.read_csv(headout, header=None, names=['id','name','rating','games','wins'], converters={'id': str})
print(Guilty_list.dtypes)
for player in players:
	for index, row in Guilty_list.loc[Guilty_list['id']==player['player_id']].iterrows():
		present = 1
		gearheads.append(GuiltyPlayer(str(player['entrant_id']), player['player_id'], row['name'], row['rating'], row['games'], row['wins']))
		
	if present == 1:
		present = 0
		continue
			
	gearheads.append(GuiltyPlayer(str(player['entrant_id']), player['player_id'], player['tag']))


# Update ELO's based on match results
for bracket in bsets[:-1]: # Every bracket except Grand Finals bracket
	for game in bracket:
		match_results(game, gearheads)
		#[winner.match(loser, game['winner_id']) for winner in gearheads if winner.id==game['winner_id'] for loser in gearheads if loser.id==game['loser_id']]
for game in bsets[-1]:  # Grand Finals bracket
	if game['short_round_text'] != 'GF':
		match_results(game, gearheads)
	else:
		Grand_finals = game
match_results(Grand_finals, gearheads)
			

for head in gearheads:
	print(head.id)
	print(head.name)
	print(head.rating)
	print(head.games)
	print(head.wins)
	print(' ')

# not sure if creating a new dataframe is faster than replacing/appending lines to the old one, probably not but easier to code atm
gearhead_list = [(head.trueid, head.name, round(head.rating), head.games, head.wins) for head in gearheads]
print(gearhead_list)
Guilty_new = pd.DataFrame(gearhead_list, columns=['id', 'name', 'rating', 'games', 'wins'])

print(Guilty_new)

Guilty_new.to_csv('c:\\ScriptStuff\\gearheads\\headcount.csv', index=False, header=False, encoding='utf-8')

'''
with open(brackout, 'w', encoding='utf8') as f:
	f.write(str(brackets))

with open(setout, 'w', encoding='utf8') as f:
	f.write(str(bsets))
	
with open(playout, 'w', encoding='utf8') as f:
	f.write(str(players))
'''
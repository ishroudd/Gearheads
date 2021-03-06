import pysmash
import pandas as pd

'''
get rid of player tags for non-new players after testing is done, all calculations are done with id anyways
'''

smash = pysmash.SmashGG()

# Test tournaments
#tournament = 'tsundere-thursdays-xi'
#event = 'guilty-gear-xrd-rev-2'
#tournament = 'socal-regionals-2017-1'
#event = 'guilty-gear-xrd-rev-2'
tournament = input('tournament slug: ')
event = input('event slug: ')
smash.set_default_event(event)

players = smash.tournament_show_players(tournament)
brackets = smash.tournament_show_event_brackets(tournament)
bsets = []
for bracket in brackets['bracket_ids']: # Final bracket in list is Grand Finals bracket
	bsets.append(smash.bracket_show_sets(bracket))

path = 'c:\\ScriptStuff\\gearheads\\'
headout = path + 'headcount.csv'
tournout = path + 'tournaments.csv'
'''
# Only used with testing
setout = path + 'sets.txt'
brackout = path + 'brackets.txt'
playout = path + 'players.txt'
'''

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


# General GG class to keep track of ELO rating, games played, and number of wins. Default rating is 1500
# id & trueid are strings not ints
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
# Examples:
# Cashew = GuiltyPlayer('500000', '999999', 'Cashew')
# Oreo = GuiltyPlayer('123456', '234567', 'Oreo', games = 5, wins = 4)
# Cashew.match(Oreo, '500000')


'''
#General process:
#
#Get tournament & event information
#If tournament has already been used to decide ELO, throw error
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
#(Grand Finals can be more than one match if there was a reset)
#Update winner/loser stats
#If there was a reset, updated winner/loser stats again with next set
#
#Export player list to update csv data

#Updating stats includes updating rating, total games, and total wins
'''


# Check if given tournament/event has already been used to calculate ELO
# csv formatted as: (tournament_slug,event_slug)
Tournament_list = pd.read_csv(tournout, header=None, names=['tournament','event'])
if ((Tournament_list['tournament'] == tournament) & (Tournament_list['event'] == event)).any():
	raise SystemExit('Tournament has already been used for calculations')

df = pd.DataFrame({'tournament': tournament, 'event': event}, index=[0])
Tournament_list = pd.concat([Tournament_list, df]) # csv file updated at end in case calculations fail


# Creates a GuiltyPlayer object for every player in tournament, creating new stats or inputting existing from csv
# csv formatted as: (player_id,name,rating,games,wins)
# An important note here:
#  Players are represented site-wide on smash.gg with player_id
#  However, match winners/losers are represented by a tournament-local entrant_id
gearheads = []
present = 0
Guilty_list = pd.read_csv(headout, header=None, names=['id','name','rating','games','wins'], converters={'id': str})
for player in players:
	for index, row in Guilty_list.loc[Guilty_list['id']==player['player_id']].iterrows():
		present = 1
		gearheads.append(GuiltyPlayer(str(player['entrant_id']), player['player_id'], row['name'], row['rating'], row['games'], row['wins']))
		
	if present == 1:
		present = 0
		continue
			
	gearheads.append(GuiltyPlayer(str(player['entrant_id']), player['player_id'], player['tag']))


# Update ELO's based on match results
Grand_finals = []
for bracket in bsets[:-1]: # Every bracket except Grand Finals bracket
	for game in bracket:
		match_results(game, gearheads)
for game in bsets[-1]:  # Grand Finals bracket
	if game['short_round_text'] != 'GF':
		match_results(game, gearheads)
	else:
		Grand_finals.append(game)
for game in Grand_finals:
	match_results(game, gearheads)
			

# Outputs updated stats to csv file
# not sure if creating a new dataframe is faster than replacing/appending lines to the old one, probably not but easier to code atm
gearhead_list = [(head.trueid, head.name, round(head.rating), head.games, head.wins) for head in gearheads]
Guilty_updated = pd.DataFrame(gearhead_list, columns=['id', 'name', 'rating', 'games', 'wins'])
Guilty_updated = (pd.concat([Guilty_list, Guilty_updated]).drop_duplicates('id', keep='last'))

# Output data to files
Tournament_list.to_csv(tournout, index=False, header=False, encoding='utf-8')
Guilty_updated.to_csv(headout, index=False, header=False, encoding='utf-8')

'''
# Only used with testing
with open(brackout, 'w', encoding='utf8') as f:
	f.write(str(brackets))

with open(setout, 'w', encoding='utf8') as f:
	f.write(str(bsets))
	
with open(playout, 'w', encoding='utf8') as f:
	f.write(str(players))
'''
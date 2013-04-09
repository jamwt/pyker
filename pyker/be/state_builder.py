def build_state(game, table_name, moves, showable):
	state = {}
	state['community'] = game.community
	state['pot'] = game.pot.alltotal
	state['blinds'] = game.sb_amt, game.bb_amt
	state['numplayers'] = len(game.active_players)
	state['blinds_timer'] = game.blinds_timer
	state['stack_start'] = game.stack_start
	state['table_name'] = table_name
	
	players = {}
	for pos, p in game.players.iteritems():
		if p != None:
			player = {}
			player['nick'] = p.nick
			if p.playing:
				player['state'] = 'in'
				if game.action and game.action[0] == pos:
					player['active'] = True
				player['bet'] = game.pot.round.get(pos, 0) or None
				if p.purse == 0:
					player['allin'] = game.pot._wagers[pos]

			elif p.sitting:
				player['state'] = 'fold'
			else:
				player['state'] = 'bust'
			player['purse'] = p.purse
			player['move'] = moves.get(pos, ('', True))
			if pos in showable:
				player['hand'] = p.hand
			if game.dealer == pos:
				player['dealer'] = True
			players[pos] = player	
			if pos in game.winners:
				player['winner'] = True
	state['players'] = players
	return state

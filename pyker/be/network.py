from eventful import MessageProtocol, call_later, call_every
from pyker import Player, Game, GameError, get_hand_phrase
from simplejson import loads as deserialize, dumps as serialize
from pyker.be.state_builder import build_state

all_players = {}
all_tables = {}
table_socks = {}
net_handlers = {} # nick -> handler
table_moves = {}

def table_emit(table_name, signal, *args, **kw):
	for sock in table_socks[table_name]:
		sock.emit(signal, *args, **kw)

class PykerServer(MessageProtocol):
	def on_init(self):
		self.set_readable(True)
		self.add_signal_handler('prot.message', self.on_message)
		self.add_signal_handler('pyker.cmd_sign_on', self.cmd_sign_on)
		self.add_signal_handler('pyker.sync', self._sync)
		self.add_signal_handler('prot.disconnected', self.on_disconnect)
		self.player = None
		self.game = None
		self.table_name = None
		self.position = None

	def reg_post_signon(self):
		self.add_signal_handler('pyker.cmd_create_table', self.cmd_create_table)
		self.add_signal_handler('pyker.cmd_join_table', self.cmd_join_table)
		self.add_signal_handler('pyker.cmd_sit_in', self.cmd_sit_in)
		self.add_signal_handler('pyker.cmd_list', self.cmd_list)
		self.add_signal_handler('pyker.cmd_chat', self.cmd_chat)
		self.add_signal_handler('pyker.cmd_who', self.cmd_who)
		self.add_signal_handler('pyker.cmd_check', self.cmd_check)
		self.add_signal_handler('pyker.cmd_fold', self.cmd_fold)
		self.add_signal_handler('pyker.cmd_call', self.cmd_call)
		self.add_signal_handler('pyker.cmd_bet', self.cmd_bet)
		self.add_signal_handler('pyker.cmd_raise', self.cmd_raise)
		self.add_signal_handler('pyker.cmd_say', self.cmd_say)
		self.add_signal_handler('pyker.say', self._say)
		self.add_signal_handler('pyker.chat', self._chat)
		self.add_signal_handler('pyker.log', self._log)
		self.add_signal_handler('pyker.action', self._action)
		self.add_signal_handler('pyker.cmd_start', self.cmd_start)

	def on_disconnect(self, evt):
		if self.player.nick in all_players:
			del all_players[self.player.nick]
		if self.player.nick in net_handlers:
			del net_handlers[self.player.nick]
		if self.game:
			tbl_socks = table_socks[self.table_name]
			if not self.game.started and self.position in self.game.players:
				del self.game.players[self.position]
			if self in tbl_socks:
				tbl_socks.remove(self)
			self.player.discard()
			self.player.sitting = False
			self.player.playing = False
			self.player.purse = 0
			self.gaction("%s has left the table" % self.player.nick)
			self.sync()
			if len(self.game.players) == 0:
				del table_socks[self.table_name]
				del all_tables[self.table_name]
				del table_moves[self.table_name]

	def on_message(self, evt, data):
		try:
			cmd, rest = data.strip().split(None, 1)
		except ValueError:
			cmd = data.strip()
			rest = ''
		cmd = cmd.lower()
		try:
			self.emit('pyker.cmd_%s' % cmd, rest)
		except GameError, v:
			self.error(str(v))

	def cmd_sign_on(self, evt, data):
		sn = data.strip().lower()
		while sn in all_players:
			sn += '_'
		self.write('nick %s\n' % sn)
		player = Player(sn)
		all_players[sn] = player
		self.player = player
		net_handlers[player.nick] = self
		self.reg_post_signon()

	def cmd_list(self, evt, data):
		self.action('-- Start of Table List --')
		for key in sorted(all_tables):
			self.action(key)
		self.action('-- End of Table List --')

	def error(self, message):
		self.write("error %s\n" % message)

	def action(self, message):
		self.write("action %s\n" % message)

	def command(self, message):
		self.write("command %s\n" % message)

	def cmd_create_table(self, evt, data):
		name, blinds_start, blinds_cap, blinds_timer, stack_start = data.strip().lower().split()

		try:
			blinds_start, blinds_cap, blinds_timer, stack_start = \
			map(int, (blinds_start, blinds_cap, blinds_timer, stack_start))
		except ValueError:
			self.error("blinds start, cap, timer, and stack size must all be integers")
			return

		if name in all_tables:
			self.error("cannot create table: '%s' already exists" % name)
		else:
			game = Game(blinds_start, blinds_cap, blinds_timer, stack_start)
			all_tables[name] = game
			self.game = game
			self.send_joined(name)
			table_socks[name] = [self]
			self.table_name = name
			table_moves[name] = {}
			self.sync()

	def cmd_join_table(self, evt, data):
		if self.table_name:
			self.error("cannot join table: you are already at a table")
		else:
			name = data.strip().lower()
			if name not in all_tables:
				self.error("cannot join table: '%s' does not exist" % name)
			else:
				self.game = all_tables[name]
				self.send_joined(name)
				table_socks[name].append(self)
				self.table_name = name
				self.gaction("%s has joined the table" % self.player.nick)
				self.sync()

	def send_joined(self, name):
		self.command('You have joined the table "%s"' % name)

	def cmd_say(self, evt, data):
		table_emit(self.table_name, 'pyker.say', self.player.nick, data)

	def _say(self, evt, nick, what):
		self.write("say %s %s\n" % (nick, what))

	def cmd_who(self, evt, data):
		playing, kibitz = [], []
		if data.strip():
			tbl = data.strip().lower()
		elif self.table_name:
			tbl = self.table_name
		else:
			self.error("you're not sitting at any table")
			return

		if tbl and tbl in table_socks:
			for sock in table_socks[tbl]:
				if sock.player.sitting:
					playing.append(sock.player.nick)
				else:
					kibitz.append(sock.player.nick)
		out = []
		if playing:
			out.append("playing: " + ', '.join(playing))
		if kibitz:
			out.append("watching: " + ', '.join(kibitz))
		out = out or ['<no players>']
		self.action('who results for "%s": %s' % (tbl, '; '.join(out)))

	def sync(self):
		table_emit(self.table_name, 'pyker.sync')

	def gaction(self, msg):
		table_emit(self.table_name, 'pyker.action', msg)

	def _action(self, evt, msg):
		self.action(msg)

	def glog(self, msg):
		table_emit(self.table_name, 'pyker.log', msg)

	def log(self, msg):
		self.action(msg)

	def _log(self, evt, msg):
		self.log(msg)

	def _sync(self, evt):
		if self.game.show_all:
			showable = [pos for pos, play in self.game.in_players]
		elif self.game.show:
			showable = [i[0] for i in self.game.show if i[1]]
		else:
			showable = [self.position]
		s_state = serialize(build_state(self.game, self.table_name, table_moves[self.table_name], showable))
		self.write('state %s\n%s\n' % (len(s_state), s_state))

	def cmd_sit_in(self, evt, data):
		if not self.table_name:
			self.error("you must join a table first")
		elif self.game.started:
			self.error("you cannot sit after the game has already started")
		else:
			try:
				position = int(data)
			except ValueError:
				self.error("you must specify and integer sitting position")
				return
			self.game.add_player(self.player, position)
			self.gaction("%s has taken seat #%s" % (self.player.nick, position))
			self.sync()
			self.position = position

	def chat(self, msg):
		table_emit(self.table_name, 'pyker.chat', self.player.nick, msg)

	def _chat(self, evt, who, msg):
		self.write("chat %s: %s\n" % (who, msg))

	def cmd_chat(self, evt, data):
		self.chat(data.strip())

	def cmd_start(self, evt, data):
		if not self.player.sitting:
			self.error("you are not sitting down at a table")
		elif self.game.started:
			self.error("game is already started")
		else:
			self.game.start()
			call_later(self.game.blinds_timer * 60,
			blinds_iter, self.table_name, self.game)
			self.gaction("%s has started the game" % self.player.nick)
			call_later(1.0, self.gaction, "cards are dealt to determine initial dealer")
			call_later(1.5, self.sync)
			call_later(1.7, self.gaction, "%s has the high card and will start as dealer" % 
			self.game.players[self.game.dealer].nick)
			call_later(5.5, start_hand, self.table_name, self.game)

	def cmd_check(self, evt, data):
		self.game.bet(self.position, 0)
		self.gaction("%s checks" % self.player.nick)
		self.user_move("check", passive=True)
		bet_iter(self.table_name, self.game)

	def cmd_fold(self, evt, data):
		self.game.bet(self.position, -1)
		self.gaction("%s folds" % self.player.nick)
		self.user_move("fold", passive=True)
		bet_iter(self.table_name, self.game)

	def cmd_call(self, evt, data):
		if not self.game.bet_made or self.game.pot.deficit(self.position) == 0:
			self.error("you have no deficit to call")
		else:
			self.game.bet(self.position, self.game.pot.deficit(self.position))
			self.gaction("%s calls $%s" % (self.player.nick, self.game.pot.bet_amount))
			self.user_move("call $%s" % self.game.pot.bet_amount)
			bet_iter(self.table_name, self.game)

	def cmd_bet(self, evt, data):
		if self.game.bet_made:
			self.error("An initial bet has already been placed; fold, call, or raise")
		else:
			try:
				bet = int(data)
			except ValueError:
				self.error("Bet amount must be an integer")
			else:
				self.game.bet(self.position, bet)
				self.gaction("%s bets $%s" % (self.player.nick, self.game.pot.bet_amount))
				self.user_move("bet $%s" % self.game.pot.bet_amount)
				bet_iter(self.table_name, self.game)

	def cmd_raise(self, evt, data):
		if not self.game.bet_made:
			self.error("An initial bet has not yet been placed; bet first")
		else:
			try:
				bet = int(data)
			except ValueError:
				self.error("Raise amount must be an integer")
			else:
				self.game.bet(self.position, max(bet - self.game.pot.round.get(self.position, 0), 0))
				self.gaction("%s raises to $%s" % (self.player.nick, self.game.pot.bet_amount))
				self.user_move("raise to $%s" % self.game.pot.bet_amount)
				bet_iter(self.table_name, self.game)

	def user_move(self, move, passive=False):
		table_moves[self.table_name][self.position] = (move, passive)

def blinds_iter(table_name, game):
	try:
		game.advance_blinds()
	except StopIteration:
		pass
	else:
		gaction(table_name, 
		"the blinds will increase to $%s, $%s on the next hand"
		% (game.sb_amt, game.bb_amt))
		call_later(game.blinds_timer * 60,
		blinds_iter, table_name, game)

def gaction(table_name, msg):
	table_emit(table_name, 'pyker.action', msg)

def gsync(table_name):
	table_emit(table_name, 'pyker.sync')

def deal_pockets(table_name, game):
	game.deal_pockets()
	for sock in table_socks[table_name]:
		if sock.position in game.active_players:
			sock.command("You are dealt %s" % ', '.join(sock.player.hand))

def start_hand(table_name, game):
	game.start_hand()
	game.state['handnum'] = game.state.get('handnum', 0) + 1
	gaction(table_name, "starting hand #%d" % game.state['handnum'])
	gsync(table_name)
	call_later(1.3, deal_pockets, table_name, game)
	call_later(1.5, gsync, table_name)
	call_later(2, betting_round, table_name, game)

def betting_round(table_name, game):
	game.start_betting_round()
	table_moves[table_name] = {}
	bet_iter(table_name, game)

def hand_iter(table_name, game):
	if game.hand_over:
		table_moves[table_name] = {}
		game.evaluate()
		shown_hands = 0
		for pos, info in game.show:
			if info:
				phrase = get_hand_phrase(info[0])
				gaction(table_name, "%s shows %s" % 
				(game.players[pos].nick, phrase))
				table_moves[table_name][pos] = (phrase, None)
				shown_hands += 1
			else:
				gaction(table_name, "%s folds" % 
				(game.players[pos].nick,))
				table_moves[table_name][pos] = ('fold', True)
		winners = {}
		for x, pot in enumerate(game.payouts):
			ind = len(game.payouts) - x
			if ind == 1:
				p_name = 'main pot'
			else:
				p_name = 'side pot'
			if len(pot) > 1:
				o = []
				for pos, amt in pot:
					o.append('%s ($%s)' % (game.players[pos].nick, amt))
				gaction(table_name, '%s split %s' % (', '.join(o), p_name))
			else:
				pos, amt = pot[0]
				gaction(table_name, '%s wins %s ($%s)' % (game.players[pos].nick,
				p_name, amt))
		gsync(table_name)
		call_later(4.0 + (2 * shown_hands), end_hand, table_name, game)

	else:
		c_l = len(game.community)
		game.deal_community()
		new_cards = game.community[c_l:]
		gaction(table_name, "community cards dealt: %s" % ', '.join(new_cards))
		gsync(table_name)
		if game.show_all:
			if len(game.community) == 5:
				game.check_for_winners()
			call_later(2.0, hand_iter, table_name, game)
		else:
			call_later(2.0, betting_round, table_name, game)

def end_hand(table_name, game):
	game.make_payments()
	game.finish_hand()
	if game.game_ended:
		gaction(table_name, "%s wins the game" % game.active_players.values()[0].nick)
	else:
		call_later(1.0, start_hand, table_name, game)

def bet_iter(table_name, game):
	if game.action == None:
		call_later(0.8, hand_iter, table_name, game)
	else:
		pos, play = game.action
		nh = net_handlers[play.nick]
		if game.bet_made and game.pot.deficit(pos):
			c_s = ' ($%s to call)' % (game.pot.deficit(pos))
		else:
			c_s = ''
		nh.command("Action is to you%s" % c_s)
		gsync(table_name)

import curses
import locale
import time
import os
import pwd
import Queue
locale.setlocale(locale.LC_ALL, '')

SYS_UNAME = pwd.getpwuid(os.getuid())[0]

from pyker.fe.supertextpad import TextboxSupreme, make_rectangle
from pyker.fe.scrollwin import ScrollingWindow
from pyker.fe.posconst import *
from pyker.fe.gstate import LockedState
from pyker.fe.net import PykerClient, VALID_COMMANDS
from pyker.game import Game

suitemap = {
	'H' : u"\u2665",
	'S' : u"\u2660",
	'D' : u"\u2666",
	'C' : u"\u2663",
}

ends = {1 : 'st', 2 : 'nd', 3 : 'rd'}
def placestr(plc):
	if plc > 3 and plc < 20:
		return str(plc) + 'th'
	return str(plc) + ends.get(plc % 10, 'th')

class PykerScrollingWindow(ScrollingWindow):
	def error(self, msg):
		self.newline()
		self.write('Error: ' + msg, curses.color_pair(CLR_RED_DEF) | curses.A_BOLD)

	def game_action(self, msg):
		self.newline()
		self.write(' * ' + msg, curses.color_pair(CLR_BLUE_DEF))

	def game_command(self, msg):
		self.newline()
		self.write(msg, curses.color_pair(CLR_GRN_DEF) | curses.A_BOLD)

	def say(self, who, what):
		prefix = '<%s> ' % who
		self.newline(len(prefix))
		self.write(prefix, curses.color_pair(CLR_YEL_DEF) | curses.A_DIM)
		self.write(what)

def render_cards(cards, wide_spacing=False):
	def igen():
		for c in cards:
			if c == None:
				yield '? ?'
			else:
				yield '%s %s' % (c[0], suitemap[c[1]])
	spacing = wide_spacing and '   ' or  '  '
	return (spacing.join(list(igen())) + ' ' * len(cards)).encode('utf-8')

is_blank = True
def redraw_main_window(stdscr, gstate, serverstate):
	global is_blank 
	height, width = stdscr.getmaxyx()
	if gstate.state == {} and not is_blank:
		is_blank = True
		stdscr.clear()
	stdscr.addstr(0, 0, 'Pyker 0.1a'.center(width), curses.color_pair(CLR_BLUE_WHT) | curses.A_BOLD)
	stdscr.vline(1, 39, '|', height - 3)
	stdscr.addstr(height - 1, 0, '$')
	if gstate.state == {}:
		stdscr.addstr(height - 2, 0, ''.ljust(width), curses.color_pair(CLR_SBAR) | curses.A_BOLD)
		return
	state = gstate.state

	is_blank = False
	stdscr.addstr(height - 2, 0, ('#%s  players=%s blinds=%r timer=%sm original-stack=$%s'
	% (state['table_name'], state['numplayers'], state['blinds'], state['blinds_timer'],
	state['stack_start'])).ljust(width), curses.color_pair(CLR_SBAR) | curses.A_BOLD)

	stdscr.addstr(COMM_LINE, COMM_COL, ' ' * 24)
	stdscr.addstr(COMM_LINE, COMM_COL, render_cards(state.get('community', [])), curses.color_pair(CLR_GRN_DEF))

	stdscr.addstr(POT_LINE, POT_COL, ("Pot is $%d" % state.get('pot', 0)).ljust(19), curses.A_BOLD)

	for x in xrange(Game.NUM_PLAYERS):
		this_base = BASE_PLINES + (x * PLINES_SPACING)
		stdscr.addstr(this_base, 0, ' ' * 38)
		stdscr.addstr(this_base + 1, 0, ' ' * 38)
		stdscr.addstr(this_base, PLACEMARK_COL, '%d]' %( x + 1), curses.A_DIM)
		player = state.get('players', {}).get(str(x+1), None)
		if player:
			if player['state'] == 'in':
				stdscr.addstr(this_base, NICK_COL, player['nick'], curses.A_BOLD)
				if player.get('dealer'):
					stdscr.addstr(this_base, NICK_COL + len(player['nick']) + 1, 'D', curses.color_pair(CLR_GRN_DEF))
				hand = player.get('hand')
				if hand is None:
					stdscr.addstr(this_base, HAND_COL, render_cards([None, None]))
				else:
					stdscr.addstr(this_base, HAND_COL, render_cards(hand), curses.color_pair(CLR_GRN_DEF) | curses.A_BOLD)
				bet = player.get('bet')
				if bet:
					bstr = '$%d' % bet
					stdscr.addstr(this_base, BET_COL, bstr.rjust(BET_WIDTH), curses.A_BOLD)
				stack = player.get('purse')
				if stack:
					stdscr.addstr(this_base + 1, STACK_COL, ('$%d' % stack).ljust(15), curses.A_DIM)
					move = player.get('move')
					if move:
						move_txt, passive = move
						if passive is True:
							stdscr.addstr(this_base + 1, STATUS_COL, move_txt, curses.A_DIM)
						elif passive is None: # show hand
							stdscr.addstr(this_base + 1, STACK_COL, move_txt, 
							curses.color_pair(CLR_YEL_DEF) | curses.A_BOLD)
						else:
							stdscr.addstr(this_base + 1, STATUS_COL, move_txt, curses.A_BOLD)

				elif player.get('allin'):
					stdscr.addstr(this_base + 1, STACK_COL, ('- ALL-IN $%s -' % 
					player.get('allin')).ljust(22), curses.A_BOLD)

				if player.get('active'):
					stdscr.addstr(this_base, ACTIVE_COL, '>', curses.color_pair(CLR_YEL_DEF) | curses.A_BOLD)
				else:
					stdscr.addstr(this_base, ACTIVE_COL, ' ')
				if player.get('winner'):
					stdscr.addstr(this_base + 1, WINNER_COL, '*', curses.color_pair(CLR_RED_DEF) | curses.A_BOLD)

			elif player['state'] in 'fold':
				stdscr.addstr(this_base, NICK_COL, player['nick'], curses.color_pair(CLR_BLUE_DEF) | curses.A_DIM)
				bet = player.get('bet')
				if bet:
					bstr = '$%d' % bet
					stdscr.addstr(this_base, BET_COL, bstr.rjust(BET_WIDTH), curses.color_pair(CLR_BLUE_DEF) |curses.A_DIM)
				stack = player.get('purse')
				if stack:
					stdscr.addstr(this_base + 1, STACK_COL, '$%d' % stack, curses.color_pair(CLR_BLUE_DEF) |curses.A_DIM)
				if player.get('dealer'):
					stdscr.addstr(this_base, NICK_COL + len(player['nick']) + 1, 'D', curses.color_pair(CLR_GRN_DEF))
			elif player['state'] in 'bust':
				stdscr.addstr(this_base, NICK_COL, player['nick'], curses.color_pair(CLR_BLUE_DEF) | curses.A_DIM)
				if player.get('place'):
					stdscr.addstr(this_base + 1, STACK_COL, placestr(player['place']), curses.color_pair(CLR_BLUE_DEF) |curses.A_DIM)

CLR_BLUE_DEF = 1
CLR_GRN_WHT = 2
CLR_RED_DEF = 3
CLR_GRN_DEF = 4
CLR_YEL_DEF = 5
CLR_SBAR = 6
CLR_BLUE_WHT = 7

def setup_colors():
	curses.init_pair(CLR_BLUE_DEF, curses.COLOR_BLUE, -1)
	curses.init_pair(CLR_GRN_WHT, curses.COLOR_GREEN, curses.COLOR_WHITE)
	curses.init_pair(CLR_RED_DEF, curses.COLOR_RED, -1)
	curses.init_pair(CLR_GRN_DEF, curses.COLOR_GREEN, -1)
	curses.init_pair(CLR_YEL_DEF, curses.COLOR_YELLOW, -1)
	curses.init_pair(CLR_SBAR, curses.COLOR_WHITE, curses.COLOR_BLUE)
	curses.init_pair(CLR_BLUE_WHT, curses.COLOR_BLUE, curses.COLOR_WHITE)

def parse_command(cli):
	cli = cli.lstrip('/')
	return tuple(cli.split())

def establish_base_size(stdscr):
	h, w = stdscr.getmaxyx()

	while h < MIN_HEIGHT:
		stdscr.clear()
		stdscr.addstr(3, 3, "Please increase the height of this terminal window")
		stdscr.refresh()
		time.sleep(0.3)
		h, w = stdscr.getmaxyx()

	while w < MIN_WIDTH:
		stdscr.clear()
		stdscr.addstr(3, 3, "Please increase the width of this terminal window")
		stdscr.refresh()
		time.sleep(0.3)
		h, w = stdscr.getmaxyx()

	stdscr.clear()

def loop(stdscr):
	h, w = stdscr.getmaxyx()

	event_panel = PykerScrollingWindow(stdscr, 1, 40, -2, -1)
	gstate = LockedState()
	serverstate = LockedState()
	sst = serverstate.co()
	sst['nick'] = SYS_UNAME
	serverstate.update(sst)
	redraw_main_window(stdscr, gstate, serverstate)
	stdscr.refresh()

	tb_actions = {
		curses.KEY_PPAGE : event_panel.page_up,
		curses.KEY_NPAGE : event_panel.page_down,
	}

	editor = TextboxSupreme(stdscr.derwin(1, w - 2, h - 1, 2), 
	make_completer(gstate, serverstate),
	tb_actions,
	)
	netclient = PykerClient(gstate, serverstate)
	netclient.start()
	res = ''
	while res != '/quit':
		res = editor.edit(make_ticker(stdscr, editor, event_panel, gstate, serverstate))
		if not res:
			continue
		if not res.startswith('/'):
			netclient.say(res)
		else:
			res = res.lower()
			netclient.handle_command(parse_command(res))

		editor.add_to_history(res)
		editor.reset()

def process_serverstate(serverstate, stdscr, panel):
	try:
		while 1:
			ev = serverstate.state['events'].get_nowait()
			if ev[0] == 'error':
				panel.error(ev[1])
			elif ev[0] == 'command':
				panel.game_command(ev[1])
			elif ev[0] == 'action':
				panel.game_action(ev[1])
			elif ev[0] == 'say':
				panel.say(ev[1], ev[2])
	except Queue.Empty:
		pass

def make_ticker(stdscr, editor, panel, gstate, serverstate):
	def realtick(chr):
		gstate.lock()
		if gstate.updated or serverstate.updated:
			gstate.updated = False
			serverstate.updated = False
			redraw_main_window(stdscr, gstate, serverstate)
			process_serverstate(serverstate, stdscr, panel)
			stdscr.refresh()
		gstate.unlock()
		return chr
	return realtick

def mixitup(gstate):
	cards = ['AH', 'KD', 'QC', 'QH', '2S']
	while 1:
		import random
		time.sleep(2)
		state = gstate.state
		state['community'] = cards[:random.randint(3, 5)]
		gstate.update(state)
		random.shuffle(cards)

def make_completer(gstate, serverstate):
	def realcomp():
		std_set = [('/' + c + ' ') for c in VALID_COMMANDS]
		plays = gstate.state.get('players')
		if plays:
			for person in plays.itervalues():
				std_set.append(person['nick'] + ': ')
		return std_set
	return realcomp

def _main(stdscr):
	curses.use_default_colors()
	curses.halfdelay(2)
	setup_colors()
	stdscr.clear()
	establish_base_size(stdscr)
	loop(stdscr)

def main():
	curses.wrapper(_main)

if __name__ == '__main__':
	main()

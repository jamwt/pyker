import Queue
import thread
import socket

from simplejson import loads as deserialize

VALID_COMMANDS = ['connect', 'quit', 'check', 'call', 'fold', 'bet', 'raise',
		'leave', 'join', 'list', 'start', 'sit']


class PykerClient:
	def __init__(self, gstate, serverstate):
		self.gstate = gstate
		self.serverstate = serverstate
		state = serverstate.state
		state['events'] = Queue.Queue()
		serverstate.update(state)
		self._inmsgs = Queue.Queue()
		self._running = True

	def start(self):
		thread.start_new_thread(self._run, ())

	def handle_command(self, pieces):
		self._inmsgs.put(pieces)

	def say(self, what):
		self.send_server_msg('say %s' % what)

	def _run(self):
		try:
			while self._running:
				m = self._inmsgs.get()
				if m[0] == 'connect':
					if len(m[1:]) != 1:
						self.error("/connect takes exactly one argument (the server name)")
					else:
						self.connected_loop(*m[1:])
				elif m[0] in VALID_COMMANDS:
					self.error("please /connect <server> first")
		except:
			import curses
			curses.endwin()
			import traceback
			traceback.print_exc()
			raise SystemExit(0)

	def error(self, msg):
		sst = self.serverstate.co()
		sst['events'].put(('error', msg))
		self.serverstate.update(sst)

	def insay(self, msg):
		who, what = msg.split(' ', 1)
		sst = self.serverstate.co()
		sst['events'].put(('say', who, what))
		self.serverstate.update(sst)

	def command(self, msg):
		sst = self.serverstate.co()
		sst['events'].put(('command', msg))
		self.serverstate.update(sst)

	def action(self, msg):
		sst = self.serverstate.co()
		sst['events'].put(('action', msg))
		self.serverstate.update(sst)

	def setserv(self, key, val):
		sst = self.serverstate.co()
		sst[key] = val
		self.serverstate.update(sst)

	def connected_loop(self, server):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.command('Attempting to connect to server %s...' % server)
		try:
			self.sock.connect((server, 17777))
		except socket.error:
			self.error('could not connect to %s' % server)
			return
		self.command('Connected to %s' % server)
		self.setserv('server', server)

		self.command('Signing on as %s...' % self.serverstate.state['nick'])
		self.send_server_msg('sign_on %s' % self.serverstate.state['nick'])
		self._connected	= True
		self.sock.settimeout(0.2)
		self.recv_state = 'start'
		self.acc = []
		while self._connected:
			try:
				datain = self.sock.recv(4096)
			except socket.timeout:
				pass
			else:
				if datain == '':
					self.setserv('server', None)
					self.error('unexpected disconnection from server %s' % server)
					self.gstate.update({})
					return
				self.take_data(datain)
			try:
				while 1:
					msg = self._inmsgs.get_nowait()
					self.handle_message_connected(msg)
			except Queue.Empty:
				pass

	def send_server_msg(self, msg):
		self.sock.sendall(msg + '\r\n')

	def handle_incoming_command(self, cli):
		cmd, rest = cli.split(' ', 1)
		if cmd == 'nick':
			self.command('You are signed on')
			nick = rest
			if nick != self.serverstate.state['nick']:
				self.action(
				'the server has named you "%s" instead of "%s" because of a conflict with another player' %
				(nick, self.serverstate.state['nick']))
				self.setserv('nick', nick)
		elif cmd == 'action':
			self.action(rest)
		elif cmd == 'command':
			self.command(rest)
		elif cmd == 'error':
			self.error(rest)
		elif cmd == 'state':
			self.needlen = int(rest)
			self.handle_chunk = self.handle_gstate
			self.recv_state = 'gstate'
		elif cmd == 'say':
			self.insay(rest)

	def handle_gstate(self, data):
		open('gstate.log', 'a').write('got gamestate:\n%s\n' % data) #XXX temp
		self.gstate.update(deserialize(data))
		self.recv_state = 'start'

	def take_data(self, data):
		self.acc.append(data)
		if self.recv_state == 'start':
			while self.recv_state == 'start':
				all = ''.join(self.acc)
				if '\n' in all:
					cli, rest = all.split('\n', 1)
					self.handle_incoming_command(cli)
					self.acc = [rest]
				else:
					break
		if self.recv_state == 'gstate':
			all = ''.join(self.acc)
			if len(all) >= self.needlen + 1:
				self.acc = [all[self.needlen + 1:].lstrip()]
				self.handle_chunk(all[:self.needlen])
				self.take_data('') # handle any followup commands
			
	def handle_message_connected(self, msg):
		if msg[0] == 'connect':
			self.error('already connected to a game server;  /disconnect first')
		elif msg[0] == 'list':
			if len(msg[1:]) != 0:
				self.error('/list takes no arguments')
			else:
				self.send_server_msg('list')
		elif msg[0] == 'create':
			if len(msg[1:]) != 5:
				self.error('/create takes five arguments (<table name> <blinds start> <blinds cap> <blind timer> <starting stack>)')
			else:
				self.send_server_msg('create_table %s %s %s %s %s' % tuple(msg[1:]))
		elif msg[0] == 'join':
			if len(msg[1:]) != 1:
				self.error('/create takes one argument (<table name>)')
			else:
				self.send_server_msg('join_table %s' % tuple(msg[1:]))
		elif msg[0] == 'who':
			args = msg[1:]
			if len(args) > 1:
				self.error('/who takes at most one argument (<table name>)')
			elif len(args) == 1:
				self.send_server_msg('who %s' % args)
			else:
				self.send_server_msg('who')
		elif msg[0] == 'start':
			args = msg[1:]
			if len(args) != 0:
				self.error('/start takes no arguments')
			else:
				self.send_server_msg('start')
		elif msg[0] == 'sit':
			args = msg[1:]
			if len(args) != 1:
				self.error('/sit takes one argument (position)')
			else:
				self.send_server_msg('sit_in %s' % args)
		elif msg[0] == 'check':
			args = msg[1:]
			if len(args) != 0:
				self.error('/check takes no arguments')
			else:
				self.send_server_msg('check')
		elif msg[0] == 'fold':
			args = msg[1:]
			if len(args) != 0:
				self.error('/fold takes no arguments')
			else:
				self.send_server_msg('fold')
		elif msg[0] == 'call':
			args = msg[1:]
			if len(args) != 0:
				self.error('/call takes no arguments')
			else:
				self.send_server_msg('call')
		elif msg[0] == 'bet':
			args = msg[1:]
			if len(args) != 1:
				self.error('/bet takes one argument (bet amount)')
			else:
				self.send_server_msg('bet %s' % args)
		elif msg[0] == 'raise':
			args = msg[1:]
			if len(args) != 1:
				self.error('/raise takes one argument (raise amount above current bet)')
			else:
				self.send_server_msg('raise %s' % args)

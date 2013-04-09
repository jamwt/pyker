import curses
import time
from vtext import VirtualTextFormatter

class ScrollingWindow:
	SIZE = 32000
	def __init__(self, stdscr, y, x, height, width):
		self.stdscr = stdscr
		self.y = y
		self.x = x
		self.want_height = height
		self.want_width = width
		self._scrollpos = -1
		self.win = None
		self.create_win()
		self.evhistory = []
		self.formatter = None
		self.create_win()

	def _get_lastline(self):
		return len(self.formatter.format)
	lastline = property(_get_lastline)

	def create_win(self):
		if self.win:
			self.win.clear()
		h, w = self.stdscr.getmaxyx()
		if self.want_height < 0:
			self.make_height = h - self.y + self.want_height
		else:
			self.make_height = self.want_height
		if self.want_width < 0:
			self.make_width = w - self.x + self.want_width
		else:
			self.make_width = self.want_width

		self.win = self.stdscr.derwin(self.make_height, self.make_width, self.y, self.x)

		self.formatter = VirtualTextFormatter(self.make_width - 1)

	def newline(self, indent=0):
		self.evhistory.append((None, indent))
		self.formatter.newline(indent)

	def write(self, text, opts=None):
		self.evhistory.append((text, opts))
		self.formatter.add(text, opts)
		if self._scrollpos == -1:
			self.draw()

	def backfill(self):
		for obj, opts in self.evhistory:
			if obj is None:
				self.formatter.newline(opts)
			else:
				self.formatter.add(obj, opts)

	def check_resize(self):
		# Screen has been resized!
		if self.want_height < 0  or self.want_width < 0:
			self.create_win()
			self.backfill()
			self.draw()

	def page_up(self):
		scrollpos = self._scrollpos
		if scrollpos == -1:
			scrollpos = self.lastline - self.make_height
		if scrollpos != 0:
			self._scrollpos = max(scrollpos - (self.make_height / 2), 0)
			self.draw()

	def page_down(self):
		if self._scrollpos != -1:
			self._scrollpos = self._scrollpos + (self.make_height / 2)
			if self._scrollpos >= self.lastline - self.make_height:
				self._scrollpos = -1
			self.draw()

	def draw(self):
		self.win.clear()
		scrollpos = self._scrollpos
		if scrollpos == -1:
			scrollpos = max(self.lastline - self.make_height, 0)

		for y_pos, x in enumerate(xrange(scrollpos, scrollpos + self.make_height)):
			try:
				line = self.formatter.format[x]
			except IndexError:
				break
			x_pos = 0
			for s, opts in line:
				if opts:
					self.win.addstr(y_pos, x_pos, s, opts)
				else:
					self.win.addstr(y_pos, x_pos, s)
				x_pos += len(s)
			
		self.win.refresh()

resize_event_ts = None
def handle_resize(sig, frame):
	global resize_event_ts
	resize_event_ts = time.time()

def main(stdscr):
	global resize_event_ts
	curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
	sr = ScrollingWindow(stdscr, 1, 10, -1, -1)
	sr.newline(8)
	sr.write("<jamwt> ", curses.color_pair(1) | curses.A_DIM)
	sr.write("what's the deal with that thing, eh?  I think it's pretty darn cool, don't you?  yep, that's where all the cool cats hang out...")
	sr.newline(8)
	sr.write("what's the deal with that thing, eh?  I think it's pretty darn cool, don't you?  yep, that's where all the cool cats hang out... and this is a really long line.. we should see it fail here at some point")

	for c in xrange(1, 100):
		sr.newline(11)
		sr.write("x " * c, curses.color_pair(1) | curses.A_DIM)
		time.sleep(0.2)

#	for c in xrange(1, 100):
#		sr.newline(11)
#		sr.write("x" * c, curses.color_pair(1) | curses.A_DIM)
#		time.sleep(0.2)
	
	sr.newline()
	sr.write("== Error: You cannot bet out of turn ==",
	curses.color_pair(2) | curses.A_BOLD)
	sr.newline()
	sr.write("* bgstults raises to $300",
	curses.color_pair(3) | curses.A_BOLD)

	sr.newline(9)
	sr.write("<mrshoe> ", curses.color_pair(1) | curses.A_DIM)
	sr.write("I knew you were going to try to bluff this hand...")
	sr.write("I knew you were going to try to bluff this hand...")
	sr.write("I knew you were going to try to bluff this hand...")
	sr.write("I knew you were going to try to bluff this hand...")
	sr.write("I knew you were going to try to bluff this hand...")
	sr.write("I knew you were going to try to bluff this hand...")

	sr.newline(11)
	sr.write("<bgstults> ", curses.color_pair(1) | curses.A_DIM)
	sr.write("You don't know squat, shoeboy")
	sr.draw()
	import signal
	signal.signal(signal.SIGWINCH, handle_resize)
	x = 1
	while 1:
		time.sleep(0.2)
		if resize_event_ts: 
			resize_event_ts = None
			while 1:
				try: curses.endwin(); break
				except: time.sleep(0.5)
			stdscr.clear()
			sr.check_resize()
			stdscr.refresh()
		sr.newline(11)
		sr.write("<bgstults> ", curses.color_pair(1) | curses.A_DIM)
		sr.write("You don't know squat #%d" % x)
		sr.draw()
		x += 1
		if x > 40:
			break
	sr.page_down()
	time.sleep(3)
	sr.page_up()
	time.sleep(3)
	sr.page_up()
	time.sleep(3)
	sr.page_up()
	time.sleep(3)
	sr.page_down()
	time.sleep(3)
	sr.page_down()
	time.sleep(3)
	sr.page_down()
	time.sleep(3)
	sr.page_down()
	sr.newline(11)
	sr.write("<bgstults> ", curses.color_pair(1) | curses.A_DIM)
	sr.write("You don't know squat #infinity")
	sr.draw()
	time.sleep(2)
	sr.newline(11)
	sr.write("<bgstults> ", curses.color_pair(1) | curses.A_DIM)
	sr.write("You don't know squat #infinity")
	sr.draw()
	time.sleep(2)


if __name__ == '__main__':
	curses.wrapper(main)

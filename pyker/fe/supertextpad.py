import string
import curses
from curses import ascii
from curses import textpad

make_rectangle = textpad.rectangle

class TextboxSupreme(textpad.Textbox):
	def __init__(self, win, tc_callable=None, action_mappings={}):
		textpad.Textbox.__init__(self, win)
		self.history = []
		self.tc_callable = tc_callable
		self.action_mappings = action_mappings

	def fill_from_history(self, chr):
		curval = self.gather()
		if self.history_mark is None:
			self.buf = curval
		else:
			self.history[self.history_mark] = curval
		newval = curval
		if chr == curses.KEY_UP:
			if self.history_mark != 0 and self.history:
				if self.history_mark is None:
					self.history_mark = len(self.history)
				self.history_mark -= 1
				newval = self.history[self.history_mark]
		else:
			if self.history_mark == len(self.history) - 1:
				newval = self.buf
				self.history_mark = None
			elif self.history_mark is not None:
				self.history_mark += 1
				newval = self.history[self.history_mark]
		
		self.win.clear()
		self.win.addstr(newval)
		self.win.refresh()

	def tab_complete(self):
		save = self.win.getyx()
		curval = self.gather()
		comps = []
		for potential in self.tc_callable():
			if potential.startswith(curval):
				comps.append(potential)
		if len(comps) == 1:
			replace = comps[0]
			self.win.clear()
			self.win.addstr(replace)
		else:
			self.win.move(*save)
		self.win.refresh()
		
	def do_command(self, chr):
		if chr in self.action_mappings:
			self.action_mappings[chr]()
		elif chr in (curses.KEY_UP, curses.KEY_DOWN):
			self.fill_from_history(chr)
		elif chr == ascii.TAB and self.tc_callable:
			self.tab_complete()
		elif chr == ascii.NAK: # ^U
			self.win.clear()
			self.win.move(0, 0)
			self.win.refresh()
		elif chr == ascii.ETB: # ^W
			x = self.win.getyx()[1] - 1
			cur_val = self.gather()
			start = x + 2
			while x > 0 and cur_val[x - 1] in string.letters:
				x -= 1
			self.win.clear()
			self.win.addstr(cur_val[:x] + cur_val[start:])
			self.win.move(0, x)
			self.win.refresh()
		else:
			return textpad.Textbox.do_command(self, chr)
		return 1

	def reset(self):
		self.win.clear()
		self.win.move(0, 0)

	def edit(self, *args, **kw):
		self.history_mark = None
		self.buf = None
		return textpad.Textbox.edit(self, *args, **kw)

	def add_to_history(self, text):
		if not len(self.history) or self.history[-1] != text:
			self.history.append(text)

	def freeze(self):
		self.cursor_pos = self.win.getyx()
		self._save = self.gather()

	def restore(self):
		self.win.clear()
		self.win.addstr(self._save)
		self.win.move(*self.cursor_pos)
		self.win.refresh()

if __name__ == '__main__':
	def main(stdscr):
		output = ''
		def tc_callable():
			return ['foobar', 'jamie', 'dave']
		edit = TextboxSupreme(stdscr.derwin(1, 40, 3, 3), tc_callable)
		while output != '/quit':
			output = edit.edit()
			edit.add_to_history(output)
			edit.reset()

	foo = curses.wrapper(main)

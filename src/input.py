#!/usr/bin/python3
################################################################################
# @file      input.py
# @brief     
# @date      Fr Nov 2025
# @author    Dimitri Simon
# 
# PROJECT:   language-learning-cli
# 
# MODIFIED:  Fri Nov 07 2025
# BY:        Dimitri Simon
# 
# Copyright (c) 2025 Dimitri Simon
# 
################################################################################

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.keys import Keys

ALWAYS_VISIBLE = [" ", "-", "'"]

def slot_input(from_colour: str, to_colour: str, from_text: str, to_text: str, prompt_text: str, length: int, filled_slots: dict = {}, newline: bool = True, expect_full_input: bool = False) -> str:
	entered = ""

	def autofill(res: str):
		curr_len = len(res)
		if curr_len in filled_slots:
			res += filled_slots[curr_len]
			return autofill(res)
		return res

	entered = autofill(entered)
	min_len = len(entered)

	def autodelete(res: str):
		nonlocal min_len
		curr_len = len(res)
		if curr_len > min_len and curr_len in filled_slots:
			return autodelete(res[:-1])
		return res


	style = Style.from_dict({
		"from": from_colour,
		"to": to_colour,
		# "prompt": "#00ffff bold",
		# "filled": "#00ff00",
		# "empty": "#ffffff",
        "highlight": "bold #00dd00",
	})

	# dynamic content
	def get_display():
		fragments = [
      		("class:prompt", "["),
        	("class:from", from_text),
			("class:prompt", f"] {prompt_text}  ["),
			("class:to", to_text),
			("class:prompt", "]> ")
		]
  
		for i in range(length):
			# char = entered[i]
			if i in filled_slots:
				fragments.append(("class:highlight", filled_slots[i]))
			elif i < len(entered):
				fragments.append(("class:filled", entered[i]))
			else:
				fragments.append(("class:empty", "▉"))
		return fragments

	control = FormattedTextControl(get_display, show_cursor=False)
	window = Window(content=control)
	layout = Layout(container=window)

	kb = KeyBindings()

	@kb.add("c-c")
	def _(event):
		event.app.exit(exception=KeyboardInterrupt)
		
	@kb.add("c-d")
	def _(event):
		event.app.exit()

	@kb.add("c-x")
	def _(event):
		event.app.exit(result="")
  
	@kb.add("enter")
	def _(event):
		if expect_full_input:
			if len(entered) == length:
				event.app.exit(result=entered)
		else:
			event.app.exit(result=entered)

	@kb.add("backspace")
	def _(event):
		nonlocal entered
		nonlocal min_len

		if len(entered) > min_len:
			entered = entered[:-1]
			event.app.invalidate()
			entered = autodelete(entered)

	@kb.add(Keys.Any)
	def _(event):
		nonlocal entered
		if event.data not in ALWAYS_VISIBLE and len(entered) < length and event.data.isprintable():
			entered += event.data
			event.app.invalidate()
			entered = autofill(entered)


	app = Application(layout=layout, key_bindings=kb, style=style, full_screen=False)
	result = app.run()
	# if newline:
	# 	print()
	return result

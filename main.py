#!/usr/bin/env python3
################################################################################
# @file      main.py
# @brief     
# @date      Tu Oct 2025
# @author    Dimitri Simon
# 
# PROJECT:   language-learning-cli
# 
# MODIFIED:  Tue Oct 07 2025
# BY:        Dimitri Simon
# 
# Copyright (c) 2025 Dimitri Simon
# 
################################################################################

from dotenv import load_dotenv
import argparse
import sys, os
import re, random, math, json
from unidecode import unidecode
from wrpy import WordReference


def conjugation_table(_from: str, _to: str, time: str|None=None):
	try:
		with open(os.path.join(os.path.dirname(__file__), "time", f"{_from}-{_to}.md"), "r") as f:
			def highlight(match):
				return f"\x1b[1;36m{match.group(0)}\x1b[0m"
			print(re.sub(r"#(.*)", highlight, f.read()))
	except FileNotFoundError:
		print(f"Error: No conjugation table found for '{_from}' to '{_to}'.", file=sys.stderr)
		sys.exit(1)

MIN_COLOUR = 0x99
MAX_DIV = (0x100-MIN_COLOUR)
MAX_MOD_COLOUR = (0x100-MIN_COLOUR) * 3 - 1

def str_to_shell_colour(s: str) -> int:
	res = (sum([(ord(c))**2 for c in s.upper()]) + 60) % MAX_MOD_COLOUR
	if res < MAX_DIV:
		return "bold #"+hex(MIN_COLOUR + (res % 7) * 0x11)[2:]+"0000"
	elif res < (MAX_DIV*2):
		return "bold #00"+hex(MIN_COLOUR + (res % 7) * 0x11)[2:]+"00"
	return "bold #0000"+hex(MIN_COLOUR + (res % 7) * 0x11)[2:]

facultative_words = {
	"fr": r"une?|le(ur)?s?|la|du|des",
	"en": r"a|the(ir)?s?",
	"es": r"el|los|las?|sus?",
}

always_visible = [" ", "-", "'"]

PADDING = 16
HINT_RATIO = 10.0
ALMOST_RATIO = 15.0
ALMOST_RETRY = True

def train_vocabulary(_from: str, _to: str):
	wordlist = {}
	failed_once = set()

	with open(os.path.join(os.path.dirname(__file__), "most-common-words-multilingual/data/wordfrequency.info", _from+".txt"), "r") as ff:
		with open(os.path.join(os.path.dirname(__file__), "most-common-words-multilingual/data/wordfrequency.info", _to+".txt"), "r") as ft:
			wordlist = {
				(re.sub(r"^("+ facultative_words[_from] +r")\s+", "", k) if k in facultative_words else k).strip():
					(re.sub(r"^("+ facultative_words[_to] +r")\s+", "", v) if v in facultative_words else v).strip()
				for k, v in dict(zip(ff.read().splitlines(), ft.read().splitlines())).items()
			}
			wordlist = {
				k: v
				for k, v in wordlist.items()
				if len(k) > 2 and len(v) > 2
			}

	from_colour = str_to_shell_colour(_from)
	to_colour = str_to_shell_colour(_to)
 
	if from_colour == to_colour:
		from_colour = "bold #000000"

	continue_training = True
	while continue_training:
		word = random.choice(list(wordlist.keys()))

		# if not " " in word:
		# 	continue

		lword = wordlist[word].strip().lower()
		if _to in facultative_words:
			lword = re.sub(r"^("+ facultative_words[_to] +r")\s+", "", lword).strip()

		visible_slots = {index: value for index, value in enumerate(lword) if value in always_visible}

		current_pos = 0  # tracks the letter index in the whole sentence

		for w in re.split(r"|".join(always_visible), lword):
			letter_idx_in_word = random.randrange(len(w))
			global_idx = current_pos + letter_idx_in_word
			visible_slots[global_idx] = w[letter_idx_in_word]
			current_pos += len(w) + 1

		# print(len(lword))
		if len(lword) >= HINT_RATIO:
			remaining = math.floor(len(lword) / HINT_RATIO)
			# print(HINT_RATIO, remaining)

			while remaining > 0:
				global_idx = random.randrange(len(lword))
				if global_idx not in visible_slots:
					visible_slots[global_idx] = lword[global_idx]
					remaining -= 1

		retry = True
		while continue_training and retry:
			user_answer = slot_input(from_colour, to_colour, _from.upper(), _to.upper(), word.ljust(PADDING, " "), len(lword), visible_slots)
			retry = False
			if user_answer is None:
				continue_training = False
			elif user_answer == "":
					print(f"            {word:>{PADDING}s} = {wordlist[word]}")
			else:
				luser = user_answer.lower()

				if _to in facultative_words:
					lword = re.sub(r"^("+ facultative_words[_to] +r")\s+", "", lword)
					luser = re.sub(r"^("+ facultative_words[_to] +r")\s+", "", luser)

				ulword = unidecode(lword)
				uluser = unidecode(luser)
				count = sum(1 for a, b in zip(ulword, luser) if a != b) + abs(len(ulword) - len(luser))
				almost = 1 + (len(ulword) / HINT_RATIO)

				# print(count, almost)
				if lword == re.sub(r"^(el|le|la|un(a|e)?|du) ", "", luser):
					print("\x1b[1;32m\u2714 Correct !\x1b[0m")
				elif ulword == uluser:
					print(f"\x1b[1;33m\u2714 Typo\x1b[0m      {word:>{PADDING}s} = {wordlist[word]}")
				elif count <= almost:
					print(f"\x1b[1;33m  Almost!\x1b[0m")
					retry = True
				else:
					print(f"\x1b[1;31m\u2a2f Incorrect\x1b[0m {word:>{PADDING}s} = {wordlist[word]}")
		print()


from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.keys import Keys

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
		if event.data not in always_visible and len(entered) < length and event.data.isprintable():
			entered += event.data
			event.app.invalidate()
			entered = autofill(entered)


	app = Application(layout=layout, key_bindings=kb, style=style, full_screen=False)
	result = app.run()
	# if newline:
	# 	print()
	return result


WORD_CONTEXT_ADJUST = 15
WORD_FROM_ADJUST_FULL = 25
WORD_FROM_ADJUST = WORD_FROM_ADJUST_FULL - 10

def translate_word(_from: str, _to: str, word: str, compound_forms: bool = False):
	data = WordReference(_from, _to).translate(word)

	def show_unique(translation: dict):
		return f"\x1b[1m{translation['meaning']}  \x1b[2m{translation['notes']}, {translation['grammar']}\x1b[0m"

	def print_unique_example(text_from: str, text_to: str, padding: int = 0):
		print(f"{'':>{padding}s}\x1b[2m{text_from}\n{'':>{padding}s}\x1b[3m{text_to}\x1b[0m")

	print(f"\x1b[1m{data['from_lang']} 🠲  {data['to_lang']}\x1b[0m")
	for translation in data["translations"]:
		if translation['title'].strip().lower() == "compound forms":
			if not compound_forms:
				continue
		# Title
		print(f"\n\n\x1b[1m{translation['title']}\x1b[0m")
		previous_line_from = ""
		for entry in translation["entries"]:
			# 1st line
			line = f"{entry['from_word']['source']}\x1b[0;2m {entry['from_word']['grammar']}.\x1b[0m"
			if line == previous_line_from:
				print(f"  {''.ljust(WORD_FROM_ADJUST)} {entry['context'].rjust(WORD_CONTEXT_ADJUST, ' ')}: {show_unique(entry['to_word'][0])}")
			else:
				print(f"  {line.ljust(WORD_FROM_ADJUST_FULL)} {entry['context'].rjust(WORD_CONTEXT_ADJUST, ' ')}: {show_unique(entry['to_word'][0])}")
				previous_line_from = line

			for to_word in entry["to_word"][1:]:
				print(f"  {''.ljust(WORD_FROM_ADJUST)} {entry['context'].rjust(WORD_CONTEXT_ADJUST, ' ')}: {show_unique(to_word)}")
				
			# Example
			if entry["from_example"] is not None and len(entry["to_example"]) != 0:
				print_unique_example(entry["from_example"], entry["to_example"][0], 8)
			print()


if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog="language-learning-cli", description="A CLI tool for language learning.")
	parser.add_argument('TO', nargs="?")
	parser.add_argument('FROM', nargs="?")
	parser.add_argument('-c', '--conjugation', action='store_true', help='Conjugate verbs')
	parser.add_argument('-w', '--translate-word', type=str, help='Translate word')
	parser.add_argument('-f', '--compound-forms', action='store_true', help='Include compound forms')
	parser.add_argument('-t', '--translate-text', type=str, help='Translate text')
	args = parser.parse_args()

	# print(args)

	load_dotenv()

	_from = (os.getenv("DEFAULT_LANGUAGE_FROM", "en") if args.FROM is None else args.FROM).lower()
	_to = (os.getenv("DEFAULT_LANGUAGE_TO", "es") if args.TO is None else args.TO).lower()
	# wr

	if args.conjugation:
		conjugation_table(_from, _to)
	elif args.translate_word:
		translate_word(_from, _to, args.translate_word, args.compound_forms)
		# print(json.dumps(WordReference(_from, _to).translate(args.translate_word)))
	else:
		train_vocabulary(_from, _to)


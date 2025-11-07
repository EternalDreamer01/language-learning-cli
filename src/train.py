#!/usr/bin/python3
################################################################################
# @file      train.py
# @brief     
# @date      Fr Nov 2025
# @author    Dimitri Simon
# 
# PROJECT:   src
# 
# MODIFIED:  Fri Nov 07 2025
# BY:        Dimitri Simon
# 
# Copyright (c) 2025 Dimitri Simon
# 
################################################################################

import os
import re, random, math, json
from pathlib import Path
from unidecode import unidecode

from .input import *


MIN_COLOUR = 0x99
MAX_DIV = (0x100-MIN_COLOUR)
MAX_MOD_COLOUR = (0x100-MIN_COLOUR) * 3 - 1

def str_to_shell_colour(s: str) -> str:
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

PADDING = 16
HINT_RATIO = 10.0
ALMOST_RATIO = 15.0
ALMOST_RETRY = True

def train_vocabulary(_from: str, _to: str):
	wordlist = {}
	
	never_failed = []
	never_failed_all = {}
	wordlist_failed = set()

	path_cache = os.path.join(str(Path.home()), ".cache/language-learning")
	never_failed_path = os.path.join(path_cache, "never_failed.json")
	os.makedirs(path_cache, exist_ok=True)

	try:
		with open(never_failed_path, "r") as f:
			never_failed_all = json.load(f)
		# print(never_failed_all)
		if (_from+_to) in never_failed_all:
			never_failed = never_failed_all[_from+_to]
	except FileNotFoundError:
		pass

	# print(never_failed)
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
				if len(k) > 2 and len(v) > 2 and k not in never_failed
			}

	from_colour = str_to_shell_colour(_from)
	to_colour = str_to_shell_colour(_to)

	if from_colour == to_colour:
		from_colour = "bold #000000"

	def user_succeed(w: str):
		# never_failed.append(w)
		wordlist_failed.discard(w)

	def user_failed(w: str):
		wordlist_failed.add(w)

	continue_training = True
	while continue_training:
		word = random.choice(list(wordlist.keys()))

		# if not " " in word:
		# 	continue

		lword = wordlist[word].strip().lower()
		if _to in facultative_words:
			lword = re.sub(r"^("+ facultative_words[_to] +r")\s+", "", lword).strip()

		visible_slots = {index: value for index, value in enumerate(lword) if value in ALWAYS_VISIBLE}

		current_pos = 0  # tracks the letter index in the whole sentence

		for w in re.split(r"|".join(ALWAYS_VISIBLE), lword):
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
			user_answer = None
			try:
				user_answer = slot_input(from_colour, to_colour, _from.upper(), _to.upper(), word.lower().ljust(PADDING, " "), len(lword), visible_slots)
			except KeyboardInterrupt:
				pass

			retry = False
			if user_answer is None:
				continue_training = False

			elif not user_answer:
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

				if lword == re.sub(r"^(el|le|la|un(a|e)?|du) ", "", luser):
					print("\x1b[1;32m\u2714 Correct !\x1b[0m")
					user_succeed(word)

				elif ulword == uluser:
					print(f"\x1b[1;33m\u2714 Typo\x1b[0m      {word:>{PADDING}s} = {wordlist[word]}")
					user_succeed(word)

				elif count <= almost:
					print(f"\x1b[1;33m  Almost!\x1b[0m")
					retry = True

				else:
					print(f"\x1b[1;31m\u2a2f Incorrect\x1b[0m {word:>{PADDING}s} = {wordlist[word]}")
					user_failed(word)
		print()

	with open(never_failed_path, 'w') as f:
		never_failed_all[_from+_to] = never_failed
		json.dump(never_failed_all, f)

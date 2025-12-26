#!/usr/bin/python3
################################################################################
# @file      translate.py
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

import sys
import re
from wrpy import WordReference


WORD_CONTEXT_ADJUST = 28
WORD_FROM_ADJUST_FULL = 25
WORD_FROM_ADJUST = WORD_FROM_ADJUST_FULL - 10

def translate_word(_from: str, _to: str, word: str, compound_forms: bool = False, compact: bool = False, main_translations: bool = False, get_first_string: bool = False):
	data = {}
	changed_to_english = False
	while not data:
		try:
			data = WordReference(_from, _to).translate(word)
		except NotImplementedError:
			print(f"\x1b[31mTranslation dictionary '{_from} <> {_to}' not available\x1b[0m", file=sys.stderr)
			if _from != "en":
				_from = "en"
				changed_to_english = True
				continue
			return
		except NameError:
			print(f"Error: No translation for '{word}'", file=sys.stderr)
			return

	if changed_to_english:
		print(f"\x1b[31m  changed to '{_from} <> {_to}' instead\x1b[0m\n")

	if get_first_string:
		if data["translations"] and data["translations"][0]["entries"]:
			first_entry = data["translations"][0]["entries"][0]
			if first_entry["to_word"]:
				# print(next((
				# 	w["meaning"]
				# 	for w in first_entry["to_word"]
				# 	if not re.search(r"\b(out|in)$", w["meaning"])
				# ), None))
				return next((
					w["meaning"]
					for w in first_entry["to_word"]
					if not re.search(r"\b(out|in)$", w["meaning"])
				), None)
		return None

	def show_unique(translation: dict):
		if translation['notes'] is not None:
			translation['notes'] = re.sub(r"^can,\s*", "", translation['notes'], flags=re.IGNORECASE).strip()
			if translation['notes']:
				translation['notes'] += ", "
		else:
			translation['notes'] = ''
		# translation['grammar'] = re.sub(r"(n(m|f)|pl)+", r"\1. ", translation['grammar'], flags=re.IGNORECASE).strip()
		return f"\x1b[1m{translation['meaning']}  \x1b[2m{translation['notes']}{translation['grammar']}.\x1b[0m"

	def print_unique_example(text_from: str, text_to: str, padding: int = 0):
		print(f"{'':>{padding}s}\x1b[2m{text_from}\n{'':>{padding}s}\x1b[3m{text_to}\x1b[0m")

	print(f"\x1b[1m{data['from_lang']} 🠲  {data['to_lang']}\x1b[0m")
	for translation in data["translations"]:
		if translation['title'].strip().lower() == "compound forms":
			if not compound_forms:
				continue
		# Title
		print(f"\n\n\x1b[1m{translation['title']}\x1b[0m")
		previous_word_from = ""
		previous_context = ""
		for entry in translation["entries"]:
			# 1st line
			word_from = f"{entry['from_word']['source']}\x1b[0;2m {entry['from_word']['grammar']}.\x1b[0m"
			context = entry['context'] or ""
			if word_from != previous_word_from:
				print(f"  {word_from.ljust(WORD_FROM_ADJUST_FULL)}")
				previous_word_from = word_from

			for to_word in entry["to_word"]:
				if context == previous_context:
					print(f"  {''.rjust(WORD_CONTEXT_ADJUST)}  {show_unique(to_word)}")
				else:
					print(f"  {context.rjust(WORD_CONTEXT_ADJUST)}: {show_unique(to_word)}")
					previous_context = context
				
			# Example
			if not compact and entry["from_example"] is not None and len(entry["to_example"]) != 0:
				print_unique_example(entry["from_example"], entry["to_example"][0], 8)
			print()

		if main_translations:
			break
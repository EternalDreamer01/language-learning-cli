#!/usr/bin/python3
################################################################################
# @file      train copy.py
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

import sys, os
import re
# from verbecc import CompleteConjugator, LangCodeISO639_1 as Lang, grammar_defines, Moods, Tenses
from benedict import benedict
from rich.console import Console
from rich.table import Table


DEFAULT_VERB = {
	"fr": "manger",
	"es": "hablar"
}

def conjugation_table(_from: str, _to: str, verb: str | None = None, time: str|None=None):
	try:
		d = benedict(f"https://verbe.cc/verbecc/conjugate/{_to}/{verb if verb is not None else DEFAULT_VERB[_to]}", format="json")
		# ccgs = {lang : CompleteConjugator(lang) for lang in grammar_defines.SUPPORTED_LANGUAGES}
		for mood in d.get("value.moods", {}):
			# print(mood.upper())
			table = Table(title=mood.upper())
			conj_lists = []
			
			for submood in d.get("value.moods."+mood, {}):
				# print("  "+submood.upper().replace("-", " "))
				table.add_column(submood.upper(), justify="left", style="green")
				i = 0
				for conj in d.get(f'value.moods.{mood}.{submood}', []):
					# print("    "+conj["c"][0])
					if i >= len(conj_lists):
						conj_lists.append([])
					conj_lists[i].append(conj["c"][0])
					i += 1

			# print()
			for r in conj_lists:
				table.add_row(*r)

			console = Console()
			console.print(table)
		# print([c[0] for c in ccgs[Lang.fr].conjugate('être')[Moods.fr.Indicatif][Tenses.fr.Présent]])
	except FileNotFoundError:
		print(f"Error: No conjugation table found for '{_from}' to '{_to}'.", file=sys.stderr)
		sys.exit(1)

# def conjugation_table(_from: str, _to: str, time: str|None=None):
# 	try:
# 		with open(os.path.join(os.path.dirname(__file__), "time", f"{_from}-{_to}.md"), "r") as f:
# 			def highlight(match):
# 				return f"\x1b[1;36m{match.group(0)}\x1b[0m"
# 			print(re.sub(r"#(.*)", highlight, f.read()))
# 	except FileNotFoundError:
# 		print(f"Error: No conjugation table found for '{_from}' to '{_to}'.", file=sys.stderr)
# 		sys.exit(1)

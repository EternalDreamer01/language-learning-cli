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
import unicodedata
# from verbecc import CompleteConjugator, LangCodeISO639_1 as Lang, grammar_defines, Moods, Tenses
from benedict import benedict
from rich.console import Console
from rich.table import Table

def remove_accents(text):
	"""Remove accents from a string for comparison."""
	return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def canonicalize(text: str) -> str:
	"""Normalize a string for stable comparisons: normalize unicode, replace NBSP,
	remove accents, collapse spaces, lowercase and strip."""
	if text is None:
		return ""
	s = unicodedata.normalize('NFKC', text)
	s = s.replace('\u00A0', ' ')
	s = remove_accents(s)
	s = s.lower()
	# collapse whitespace
	s = re.sub(r'\s+', ' ', s)
	return s.strip()


DEFAULT_VERB = {
	"fr": "manger",
	"es": "hablar"
}

def conjugation_table(_from: str, _to: str, verb: str | None = None, time: str|None=None):
	d = benedict(f"https://verbe.cc/verbecc/conjugate/{_to}/{verb if verb is not None else DEFAULT_VERB[_to]}", format="json")
	# ccgs = {lang : CompleteConjugator(lang) for lang in grammar_defines.SUPPORTED_LANGUAGES}
	for mood in d.get("value.moods", {}):
		# print(mood.upper())
		table = Table(title=mood.upper())
		table.add_column("", justify="left", style="green")
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
		pronoun = []
		last_conj = ""
		prev_r = None
		prev_row_no_pronoun = None
		prev_row_no_pronoun_key = None
		row_no_pronoun_count = 0
		
		def output_row_no_pronoun(row_data, count):
			"""Output a row without pronouns, with optional count indicator."""
			label = f"{count}x" if count > 1 else ""
			table.add_row(label, *row_data)
		
		def strip_pronouns(r, pronoun_list=None):
			"""Strip pronouns from all columns in a row."""
			row_data = []
			for col in r:
				if col.startswith("no "):
					# Handle "no " prefix
					after_no = col[3:]
					col_parts = after_no.split(" ", 1)
					if len(col_parts) == 2:
						row_data.append("no " + col_parts[1])
					else:
						row_data.append(col)
				else:
					# If a pronoun list is provided, try to strip any of its forms
					if pronoun_list:
						# build candidate prefixes (full and short apostrophe tokens)
						candidates = []
						for pl in pronoun_list:
							candidates.append(pl)
							if pl.startswith("que "):
								after = pl.split(" ", 1)[1]
							else:
								after = pl
							if "'" in after:
								candidates.append(after.split("'", 1)[0] + "'")
						# sort by length so longest match first
						candidates = sorted(set(candidates), key=len, reverse=True)
						matched = False
						for cand in candidates:
							if col.startswith(cand):
								rem = col[len(cand):].lstrip()
								row_data.append(rem)
								matched = True
								break
						if not matched:
							# fallback: try to strip leading apostrophe token or by space
							m = re.match(r"^([^\s']+'?)(.*)$", col)
							if m and "'" in m.group(1):
								row_data.append(m.group(2))
							else:
								col_parts = col.split(" ", 1)
								if len(col_parts) == 2:
									row_data.append(col_parts[1])
								else:
									row_data.append(col)
					else:
						# No specific pronoun provided: attempt to strip leading apostrophe-based pronoun
						m = re.match(r"^([^\s']+'?)(.*)$", col)
						if m and "'" in m.group(1):
							row_data.append(m.group(2))
						else:
							# Fallback: strip by space
							col_parts = col.split(" ", 1)
							if len(col_parts) == 2:
								row_data.append(col_parts[1])
							else:
								row_data.append(col)
			return row_data
		
		def normalize_pronoun(p):
			"""Normalize pronoun for grouping: handle apostrophes and 'que' cases."""
			# If pronoun starts with "que " or "qu'", keep the full form (don't split on apostrophe)
			if p.startswith("que ") or p.startswith("qu'"):
				return p
			# Otherwise, if there's an apostrophe, split and use the second part for grouping
			if "'" in p:
				return p.split("'", 1)[1]
			return p
		
		for r in conj_lists:
			parts = r[0].split(" ", 1)
			if len(parts) == 2:
				word1, rest = parts
				# Special handling for "que" prefix
				if word1 == "que":
					if "'" in rest:
						# "que j'aie" → p="que j'", c="aie"
						apos_parts = rest.split("'", 1)
						p = word1 + " " + apos_parts[0] + "'"
						c = apos_parts[1]
					else:
						# "que tu aies" → p="que tu", c="aies"
						space_parts = rest.split(" ", 1)
						p = word1 + " " + space_parts[0]
						c = space_parts[1] if len(space_parts) == 2 else ""
				else:
					p = word1
					c = rest
			else:
				# No space in the string: try to detect apostrophe-based pronoun (e.g., "j'ai", "qu'il")
				cell = parts[0]
				if "'" in cell:
					idx = cell.find("'")
					# treat left side including apostrophe as pronoun, right side as conjugation
					p = cell[:idx+1]
					c = cell[idx+1:]
				else:
					p, c = "", cell
			
			# If no pronoun, group identical rows
			if not p:
				row_data = strip_pronouns(r)
				# canonical key: tuple of stripped strings for stable comparison
				row_key = tuple(canonicalize(s) for s in row_data)
			
				if prev_row_no_pronoun_key is None or prev_row_no_pronoun_key != row_key:
					# Different row or first row without pronoun
					if prev_row_no_pronoun is not None:
						# Output previous accumulated rows
						output_row_no_pronoun(prev_row_no_pronoun, row_no_pronoun_count)
					# Output any pending pronoun group
					if pronoun and prev_r:
						row_data_with_pronoun = strip_pronouns(prev_r, pronoun)
						table.add_row(', '.join(pronoun), *row_data_with_pronoun)
						pronoun = []
						last_conj = ""
					prev_row_no_pronoun = row_data
					prev_row_no_pronoun_key = row_key
					row_no_pronoun_count = 1
				else:
					# Same row, increment count
					row_no_pronoun_count += 1
				prev_r = None
				continue
			
			# Row with pronoun: output any accumulated rows without pronouns first
			if prev_row_no_pronoun is not None:
				output_row_no_pronoun(prev_row_no_pronoun, row_no_pronoun_count)
				prev_row_no_pronoun_key = None
				prev_row_no_pronoun = None
				row_no_pronoun_count = 0
			
			# Compare conjugations without accents
			c_normalized = remove_accents(c)
			#p_normalized = normalize_pronoun(p)
			
			if c_normalized != last_conj:
				# Output the previous pronoun group if it exists
				if pronoun and prev_r:
					row_data = strip_pronouns(prev_r, pronoun)
					table.add_row(', '.join(pronoun), *row_data)
				# Start a new group
				pronoun = [p]
				last_conj = c_normalized
			else:
				# Same conjugation, accumulate pronoun
				pronoun.append(p)
			prev_r = r
		
		# Output any remaining accumulated data
		if prev_row_no_pronoun is not None:
			output_row_no_pronoun(prev_row_no_pronoun, row_no_pronoun_count)
		elif pronoun and prev_r:
			row_data = strip_pronouns(prev_r, pronoun)
			table.add_row(', '.join(pronoun), *row_data)

		console = Console()
		console.print(table)

# def conjugation_table(_from: str, _to: str, time: str|None=None):
# 	try:
# 		with open(os.path.join(os.path.dirname(__file__), "time", f"{_from}-{_to}.md"), "r") as f:
# 			def highlight(match):
# 				return f"\x1b[1;36m{match.group(0)}\x1b[0m"
# 			print(re.sub(r"#(.*)", highlight, f.read()))
# 	except FileNotFoundError:
# 		print(f"Error: No conjugation table found for '{_from}' to '{_to}'.", file=sys.stderr)
# 		sys.exit(1)

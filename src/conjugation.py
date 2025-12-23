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

import sys
from rich.console import Console
from rich.table import Table
from .translate import translate_word


DEFAULT_VERB = {
	"fr": "manger",
	"es": "hablar"
}

from bs4 import BeautifulSoup
import requests

short_names = {
	"en": "English",
	"fr": "French",
	"es": "Spanish",
	"de": "German",
	"it": "Italian",
	"pt": "Portuguese",
	"he": "Hebrew",
	"ru": "Russian",
	"ar": "Arabic",
	"jp": "Japanese"
}



def parse_conjugation_data(html_string):
	"""Parse conjugation HTML and extract moods, tenses, and conjugations."""
	try:
		soup = BeautifulSoup(html_string, 'html.parser').find("div", id="ch_divSimple")
		result = {}
		last_mood = None
		
		# Find all mood sections (h4 tags contain mood names)
		for mood_header in soup.find_all('div', class_='word-wrap-row'):
			# mood = mood_header.get_text(strip=True)
			
			# Find parent container of this mood
			mood = mood_header.find('h4')
			if not mood:
				mood = last_mood
				result[mood].append({})
			else:
				mood = mood.get_text(strip=True)
				last_mood = mood

				result[mood] = [{}]

			# print()
			# print(mood)
			
			# Find all tense boxes within this mood
			for tense_box in mood_header: #.find_all('div', class_='blue-box-wrap'):
				tense_title = tense_box.find('p')
				if tense_title:
					tense = tense_title.get_text(strip=True)
					# print("  " +tense)
					# print(tense_box)
					result[mood][-1][tense] = {}
					
					# Extract pronouns and conjugations from list items
					for li in tense_box.find_all('li'):
						# print(li)
						# Split by italic tags
						pronoun = ''.join(it.get_text() for it in li.find_all('i', class_="particletxt") + li.find_all('i', class_="graytxt"))
						conj = ''.join(it.get_text() for it in li.find_all('i', class_="auxgraytxt") + li.find_all('i', class_="verbtxt"))
						# print(items)
						# if len(items) >= 2:
						# 	pronoun = items[0].get_text().strip()
						# 	conjugation = ''.join(it.get_text() for it in items[1:])  # Last i tag has the verb form
						result[mood][-1][tense][pronoun] = conj
		return result
	except AttributeError:
		pass

def conjugation_table(_from: str, _to: str, verb: str | None = None, time: str|None=None):
	if _to not in short_names:
		print(f"Error: Language '{_to}' not supported for Reverso conjugation.", file=sys.stderr)
		sys.exit(1)

# Get conjugation in target language
	language = short_names[_to] or _to
	verb = verb if verb is not None else DEFAULT_VERB[_to]

	d = requests.get(
		f"https://conjugator.reverso.net/conjugation-{language}-verb-{verb}.html",
		headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"}
	).text

	data = parse_conjugation_data(d)
	if data is None:
		print(f"Error: Unable to fetch conjugation data for verb '{verb}' in language '{_to}'.", file=sys.stderr)
		sys.exit(1)

# Get conjugation in source language
	# verb_from = translate_word(_to, _from, verb, get_first_string=True)
	# language = short_names[_from] or _from

	# d = requests.get(
	# 	f"https://conjugator.reverso.net/conjugation-{language}-verb-{verb_from}.html",
	# 	headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"}
	# ).text

	# data_from = {"": None, "": None, "": None, "": None, "": None, "": None, "": None, "": None, "": None, "": None, "": None, "": None} # parse_conjugation_data(d)
	# if data_from is None:
	# 	print(f"Error: Unable to fetch conjugation data for verb '{verb}' in language '{_to}'.", file=sys.stderr)
	# 	sys.exit(1)

	for mood in data:
	# for mood in data:
		# print(mood.upper())
		for t in data[mood]:
			table = Table(title=mood.upper())
			table.add_column("", justify="left", style="green")
			conj_lists = []
			col0 = True
			# print(t)
			if t:
				for submood in t:
					# print("  "+submood.upper().replace("-", " "))
					table.add_column(submood.upper(), justify="left", style="green")
					i = 0
					for conj in t[submood]:
						# print("    "+conj)
						if i >= len(conj_lists):
							conj_lists.append([])
						if col0:
							conj_lists[i].append(conj)
						conj_lists[i].append(t[submood][conj])
						i += 1
					col0 = False
			# print(conj_lists)
				for r in conj_lists:
					table.add_row(*r)

				console = Console()
				console.print(table)
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
from benedict import benedict
from rich.console import Console
from rich.table import Table
from rich.text import Text
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
		
		for row in soup.find_all('div', class_='word-wrap-row'):
			cols = row.find_all('div', class_='wrap-three-col')
			
			# Check if row has row-level h4 (only use if NO columns have h4s)
			row_h4_div = row.find('div', class_='word-wrap-title')
			has_col_h4 = any(col.find('div', class_='word-wrap-title') for col in cols)
			
			if row_h4_div and not has_col_h4:
				h4_elem = row_h4_div.find('h4')
				if h4_elem:
					last_mood = h4_elem.get_text(strip=True)
			
			for col in cols:
				col_h4_div = col.find('div', class_='word-wrap-title')
				col_mood = None
				if col_h4_div:
					h4_elem = col_h4_div.find('h4')
					if h4_elem:
						col_mood = h4_elem.get_text(strip=True)
						last_mood = col_mood
				
				current_mood = col_mood if col_mood else last_mood
				
				if current_mood is None:
					continue
				
				for tense_box in col.find_all('div', class_='blue-box-wrap', recursive=False):
					if current_mood not in result:
						result[current_mood] = {}
					
					tense_title = tense_box.find('p')
					tense = tense_title.get_text(strip=True) if tense_title else current_mood
					
					result[current_mood][tense] = {}
					
					for li in tense_box.find_all('li'):
						pronoun = ''.join(it.get_text() for it in li.find_all('i', class_="particletxt") + li.find_all('i', class_="graytxt"))
						conj = ''.join(it.get_text() for it in li.find_all('i', class_="auxgraytxt") + li.find_all('i', class_="verbtxt"))
						result[current_mood][tense][pronoun.replace(".", "")] = conj
		
		return benedict(result)
	except (AttributeError, TypeError):
		print("error")
		pass


def _shared_prefix_suffix(strings: list[str]) -> tuple[int, int]:
	"""Return (prefix_len, suffix_len) common to all strings in the list.
	If list is empty return (0,0).
	"""
	if not strings:
		return 0, 0
	strings = [s or '' for s in strings]
	pref = 0
	# diftong = ""
	for chars in zip(*strings):
		# print(chars, diftong, pref)
		if all(c == chars[0] for c in chars):
			pref += 1

		else:
			break

	rev = [s[pref:][::-1] for s in strings]
	suf = 0
	for chars in zip(*rev):
		if all(c == chars[0] for c in chars):
			suf += 1
		else:
			break
	return pref, suf


def highlight_conj(base: str, full_conj: str, shared_pref: int | None = None, shared_suf: int | None = None) -> Text:
	"""Return a Rich Text highlighting differences between base and conjugation.
	If `full_conj` contains an auxiliary, only compare the last token (the verb form).
	If `shared_pref`/`shared_suf` provided, use those bounds (computed for the whole mood).
	Otherwise compute prefix/suffix between `base` and the conjugation.
	"""
	parts = full_conj.strip().rsplit(' ', 1)
	if len(parts) == 2:
		aux, main = parts[0] + ' ', parts[1]
	else:
		aux, main = '', parts[0]

	b = base or ''
	text = Text()
	if aux:
		text.append(aux, style="dim")
		# else:
		# 	main = aux
		# 	aux = ""
			# print(full_conj)

	# If identical, no highlighting
	if b == main:
		text.append(main)
		return text

	# determine prefix/suffix to use
	if shared_pref is None or shared_suf is None:
		pref = 0
		for a, c in zip(b, main):
			if a == c:
				pref += 1
			else:
				break
		suf = 0
		for a, c in zip(b[pref:][::-1], main[pref:][::-1]):
			if a == c:
				suf += 1
			else:
				break
	else:
		pref = min(shared_pref, len(main))
		suf = min(shared_suf, max(0, len(main) - pref))

	start = pref
	end = len(main) - suf if suf > 0 else len(main)

	# Append common prefix
	if pref:
		text.append(main[:pref])

	# Append differing middle highlighted
	if start < end:
		text.append(main[start:end], style="bold blue")
	# Append trailing suffix
	if end < len(main):
		text.append(main[end:])

	return text


CONJUGATION_LIST = {
	"en": {
		"indicative.present.simple": "Indicative.Present",
		"indicative.present.continuous": "Indicative.Present continuous",
		"indicative.present.perfect.simple": "Indicative.Present perfect",
		"indicative.present.perfect.continuous": "Indicative.Present perfect continuous",

		"indicative.future.simple": "Indicative.Future",
		"indicative.future.continuous": "Indicative.Future continuous",
		"indicative.future.perfect.simple": "Indicative.Future perfect",
		"indicative.future.perfect.continuous": "Indicative.Future perfect continuous",

		"indicative.preterite": "Indicative.Preterite",
		"indicative.past.continuous": "Indicative.Past continuous",
		"indicative.past.perfect.simple": "Indicative.Past perfect",
		"indicative.past.perfect.continuous": "Indicative.Past perfect continuous",
	},
	"es": {
		"indicativo": {
			"presente": "Indicativo.Presente",
			"futuro.simple": "Indicativo.Futuro",
			"futuro.perfecto": "Indicativo.Futuro perfecto",
	
			"pretérito.imperfecto": "Indicativo.Pretérito imperfecto",
			"pretérito.perfecto": "Indicativo.Pretérito perfecto compuesto",
			"pretérito.pluscuamperfecto": "Indicativo.Pretérito pluscuamperfecto",
			"pretérito.anterior": "Indicativo.Pretérito anterior",
   
			"condicional.simple": "Indicativo.Condicional",
			"condicional.perfecto": "Indicativo.Condicional perfecto",
		},
		"Subjonctivo": {
			"presente": "Subjonctivo.Presente",
			"futuro.simple": "Subjonctivo.Futuro",
			"futuro.perfecto": "Subjonctivo.Futuro perfecto",

			"pretérito.imperfecto": [
				"Subjonctivo.Pretérito imperfecto",
				"Subjonctivo.Pretérito imperfecto (2)",
			],
			"pretérito.perfecto": "Subjonctivo.Pretérito perfecto simple",
			"pretérito.pluscuamperfecto": [
				"Subjonctivo.Pretérito pluscuamperfecto",
				"Subjonctivo.Pretérito pluscuamperfecto (2)",
			]
		}
	},
	"fr": {
		"indicatif": {
			"présent": "Indicatif.Présent",
			"futur.simple": "Indicatif.Futur",
			"futur.antérieur": "Indicatif.Futur antérieur",

			"imparfait": "Indicatif.Imparfait",
			"passé.simple": "Indicatif.Passé simple",
			"plus-que-parfait": "Indicatif.Plus-que-parfait",
			"passé.antérieur": "Indicatif.Passé antérieur",

			"conditionnel.présent": "Indicatif.Conditionnel présent",
			"conditionnel.passé": "Indicatif.Conditionnel passé",
		}
	}
}

__data = """<div id="ch_divSimple" class="word-wrap-simple"><div class="result-block-api"><div class="word-wrap-row"><div class="word-wrap-title"><h4>Indicativo</h4></div><div class="wrap-three-col"><div class="blue-box-wrap" mobile-title="Indicativo Presente"><p>Presente</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="verbtxt">tengo</i></li><li><i class="graytxt">tú </i><i class="verbtxt">tienes</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="verbtxt">tiene</i></li><li><i class="graytxt">nosotros </i><i class="verbtxt">tenemos</i></li><li><i class="graytxt">vosotros </i><i class="verbtxt">tenéis</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="verbtxt">tienen</i></li></ul></div></div><div class="wrap-three-col"><div class="blue-box-wrap" mobile-title="Indicativo Futuro"><p>Futuro</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="verbtxt">tendré</i></li><li><i class="graytxt">tú </i><i class="verbtxt">tendrás</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="verbtxt">tendrá</i></li><li><i class="graytxt">nosotros </i><i class="verbtxt">tendremos</i></li><li><i class="graytxt">vosotros </i><i class="verbtxt">tendréis</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="verbtxt">tendrán</i></li></ul></div></div><div class="wrap-three-col"><div class="blue-box-wrap" mobile-title="Indicativo Pretérito imperfecto"><p>Pretérito imperfecto</p><ul class="wrap-verbs-listing"><li><i class="graytxt" style="">yo </i><i class="verbtxt" style="">tenía</i></li><li><i class="graytxt" style="">tú </i><i class="verbtxt" style="">tenías</i></li><li><i class="graytxt" style="">él/ella/Ud. </i><i class="verbtxt" style="">tenía</i></li><li><i class="graytxt">nosotros </i><i class="verbtxt">teníamos</i></li><li><i class="graytxt">vosotros </i><i class="verbtxt">teníais</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="verbtxt">tenían</i></li></ul></div></div></div><div class="word-wrap-row"><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicativo Pretérito perfecto compuesto"><p>Pretérito perfecto compuesto</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="auxgraytxt">he </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">tú </i><i class="auxgraytxt">has </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="auxgraytxt">ha </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">nosotros </i><i class="auxgraytxt">hemos </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">vosotros </i><i class="auxgraytxt">habéis </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="auxgraytxt">han </i><i class="verbtxt">tenido</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicativo Pretérito pluscuamperfecto"><p>Pretérito pluscuamperfecto</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="auxgraytxt">había </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">tú </i><i class="auxgraytxt">habías </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="auxgraytxt">había </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">nosotros </i><i class="auxgraytxt">habíamos </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">vosotros </i><i class="auxgraytxt">habíais </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="auxgraytxt">habían </i><i class="verbtxt">tenido</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicativo Pretérito anterior"><p>Pretérito anterior</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="auxgraytxt">hube </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">tú </i><i class="auxgraytxt">hubiste </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="auxgraytxt">hubo </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">nosotros </i><i class="auxgraytxt">hubimos </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">vosotros </i><i class="auxgraytxt">hubisteis </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="auxgraytxt">hubieron </i><i class="verbtxt">tenido</i></li></ul></div></div></div><div class="word-wrap-row"><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicativo Futuro perfecto"><p>Futuro perfecto</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="auxgraytxt">habré </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">tú </i><i class="auxgraytxt">habrás </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="auxgraytxt">habrá </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">nosotros </i><i class="auxgraytxt">habremos </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">vosotros </i><i class="auxgraytxt">habréis </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="auxgraytxt">habrán </i><i class="verbtxt">tenido</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicativo Condicional perfecto"><p>Condicional perfecto</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="auxgraytxt">habría </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">tú </i><i class="auxgraytxt">habrías </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="auxgraytxt">habría </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">nosotros </i><i class="auxgraytxt">habríamos </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">vosotros </i><i class="auxgraytxt">habríais </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="auxgraytxt">habrían </i><i class="verbtxt">tenido</i></li></ul></div></div><div class="wrap-three-col"><div class="blue-box-wrap" mobile-title="Indicativo Condicional"><p>Condicional</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="verbtxt">tendría</i></li><li><i class="graytxt">tú </i><i class="verbtxt">tendrías</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="verbtxt">tendría</i></li><li><i class="graytxt">nosotros </i><i class="verbtxt">tendríamos</i></li><li><i class="graytxt">vosotros </i><i class="verbtxt">tendríais</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="verbtxt">tendrían</i></li></ul></div></div></div><div class="word-wrap-row"><div class="wrap-three-col" style="margin-top: 32px;"><div class="blue-box-wrap" mobile-title="Indicativo Pretérito perfecto simple"><p>Pretérito perfecto simple</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="verbtxt">tuve</i></li><li><i class="graytxt">tú </i><i class="verbtxt">tuviste</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="verbtxt">tuvo</i></li><li><i class="graytxt">nosotros </i><i class="verbtxt">tuvimos</i></li><li><i class="graytxt">vosotros </i><i class="verbtxt">tuvisteis</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="verbtxt">tuvieron</i></li></ul></div></div><div class="wrap-three-col" style="margin-top: 0px;"><div class="word-wrap-title"><h4>Imperativo </h4></div><div class="blue-box-wrap alt-tense" mobile-title="Imperativo "><ul class="wrap-verbs-listing"><li><i class="verbtxt">ten </i><i class="graytxt">tú</i></li><li><i class="verbtxt">tenga </i><i class="graytxt">él/ella/Ud.</i></li><li><i class="verbtxt">tengamos </i><i class="graytxt">nosotros</i></li><li><i class="verbtxt">tened </i><i class="graytxt">vosotros</i></li><li><i class="verbtxt">tengan </i><i class="graytxt">ellos/ellas/Uds.</i></li></ul></div></div><div class="wrap-three-col" style="margin-top: 0px;"><div class="word-wrap-title"><h4>Subjuntivo</h4></div><div class="blue-box-wrap" mobile-title="Subjuntivo Presente"><p>Presente</p><ul class="wrap-verbs-listing"><li><i class="graytxt" style="">yo </i><i class="verbtxt" style="">tenga</i></li><li><i class="graytxt" style="">tú </i><i class="verbtxt" style="">tengas</i></li><li><i class="graytxt" style="">él/ella/Ud. </i><i class="verbtxt" style="">tenga</i></li><li><i class="graytxt" style="">nosotros </i><i class="verbtxt" style="">tengamos</i></li><li><i class="graytxt" style="">vosotros </i><i class="verbtxt" style="">tengáis</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="verbtxt">tengan</i></li></ul></div></div></div><div class="word-wrap-row"><div class="wrap-three-col"><div class="blue-box-wrap" mobile-title="Subjuntivo Futuro"><p>Futuro</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="verbtxt">tuviere</i></li><li><i class="graytxt">tú </i><i class="verbtxt">tuvieres</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="verbtxt">tuviere</i></li><li><i class="graytxt">nosotros </i><i class="verbtxt">tuviéremos</i></li><li><i class="graytxt">vosotros </i><i class="verbtxt">tuviereis</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="verbtxt">tuvieren</i></li></ul></div></div><div class="wrap-three-col"><div class="blue-box-wrap" mobile-title="Subjuntivo Pretérito imperfecto"><p>Pretérito imperfecto</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="verbtxt">tuviera</i></li><li><i class="graytxt">tú </i><i class="verbtxt">tuvieras</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="verbtxt">tuviera</i></li><li><i class="graytxt">nosotros </i><i class="verbtxt">tuviéramos</i></li><li><i class="graytxt">vosotros </i><i class="verbtxt">tuvierais</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="verbtxt">tuvieran</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Subjuntivo Pretérito pluscuamperfecto"><p>Pretérito pluscuamperfecto</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="auxgraytxt">hubiera </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">tú </i><i class="auxgraytxt">hubieras </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="auxgraytxt">hubiera </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">nosotros </i><i class="auxgraytxt">hubiéramos </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">vosotros </i><i class="auxgraytxt">hubierais </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="auxgraytxt">hubieran </i><i class="verbtxt">tenido</i></li></ul></div></div></div><div class="word-wrap-row"><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Subjuntivo Futuro perfecto"><p>Futuro perfecto</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="auxgraytxt">hubiere </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">tú </i><i class="auxgraytxt">hubieres </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="auxgraytxt">hubiere </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">nosotros </i><i class="auxgraytxt">hubiéremos </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">vosotros </i><i class="auxgraytxt">hubiereis </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="auxgraytxt">hubieren </i><i class="verbtxt">tenido</i></li></ul></div></div><div class="wrap-three-col"><div class="blue-box-wrap" mobile-title="Subjuntivo Pretérito imperfecto (2)"><p>Pretérito imperfecto (2)</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="verbtxt">tuviese</i></li><li><i class="graytxt">tú </i><i class="verbtxt">tuvieses</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="verbtxt">tuviese</i></li><li><i class="graytxt">nosotros </i><i class="verbtxt">tuviésemos</i></li><li><i class="graytxt">vosotros </i><i class="verbtxt">tuvieseis</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="verbtxt">tuviesen</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Subjuntivo Pretérito pluscuamperfecto (2)"><p>Pretérito pluscuamperfecto (2)</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="auxgraytxt">hubiese </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">tú </i><i class="auxgraytxt">hubieses </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="auxgraytxt">hubiese </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">nosotros </i><i class="auxgraytxt">hubiésemos </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">vosotros </i><i class="auxgraytxt">hubieseis </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="auxgraytxt">hubiesen </i><i class="verbtxt">tenido</i></li></ul></div></div></div><div class="word-wrap-row"><div class="wrap-three-col" c="1" style="margin-top: 32px;"><div class="blue-box-wrap" mobile-title="Subjuntivo Pretérito perfecto"><p>Pretérito perfecto</p><ul class="wrap-verbs-listing"><li><i class="graytxt">yo </i><i class="auxgraytxt">haya </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">tú </i><i class="auxgraytxt">hayas </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">él/ella/Ud. </i><i class="auxgraytxt">haya </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">nosotros </i><i class="auxgraytxt">hayamos </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">vosotros </i><i class="auxgraytxt">hayáis </i><i class="verbtxt">tenido</i></li><li><i class="graytxt">ellos/ellas/Uds. </i><i class="auxgraytxt">hayan </i><i class="verbtxt">tenido</i></li></ul></div></div><div class="wrap-three-col" style="margin-top: 0px;"><div class="word-wrap-title"><h4>Gerundio </h4></div><div class="blue-box-wrap alt-tense" mobile-title="Gerundio "><ul class="wrap-verbs-listing top2"><li><i class="verbtxt">teniendo</i></li></ul></div></div><div class="wrap-three-col" c="1" style="margin-top: 0px;"><div class="word-wrap-title"><h4>Gerundio compuesto </h4></div><div class="blue-box-wrap" mobile-title="Gerundio compuesto "><ul class="wrap-verbs-listing"><li><i class="auxgraytxt">habiendo </i><i class="verbtxt">tenido</i></li></ul></div></div></div><div class="word-wrap-row"><div class="wrap-three-col"><div class="word-wrap-title"><h4>Infinitivo </h4></div><div class="blue-box-wrap alt-tense" mobile-title="Infinitivo "><ul class="wrap-verbs-listing top1"><li><i class="verbtxt">tener</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="word-wrap-title"><h4>Infinitivo compuesto </h4></div><div class="blue-box-wrap" mobile-title="Infinitivo compuesto "><ul class="wrap-verbs-listing"><li><i class="auxgraytxt">haber </i><i class="verbtxt">tenido</i></li></ul></div></div><div class="wrap-three-col"><div class="word-wrap-title"><h4>Participio Pasado</h4></div><div class="blue-box-wrap alt-tense" mobile-title="Participio Pasado"><ul class="wrap-verbs-listing top3"><li><i class="verbtxt">tenido</i></li></ul></div></div></div></div></div>
"""
# """
# <div id="ch_divSimple" class="word-wrap-simple"><div class="result-block-api"><div class="word-wrap-row"><div class="word-wrap-title"><h4>Indicative</h4></div><div class="wrap-three-col"><div class="blue-box-wrap" mobile-title="Indicative Present"><p>Present</p><ul class="wrap-verbs-listing"><li><i class="graytxt" style="">I </i><i class="verbtxt" style="">have</i></li><li><i class="graytxt" style="">you </i><i class="verbtxt" style="">have</i></li><li><i class="graytxt">he/she/it </i><i class="verbtxt">has</i></li><li><i class="graytxt">we </i><i class="verbtxt">have</i></li><li><i class="graytxt">you </i><i class="verbtxt">have</i></li><li><i class="graytxt" style="">they </i><i class="verbtxt" style="">have</i></li></ul></div></div><div class="wrap-three-col"><div class="blue-box-wrap" mobile-title="Indicative Preterite"><p>Preterite</p><ul class="wrap-verbs-listing top2"><li><i class="graytxt">I </i><i class="verbtxt">had</i></li><li><i class="graytxt" style="">you </i><i class="verbtxt" style="">had</i></li><li><i class="graytxt" style="">he/she/it </i><i class="verbtxt" style="">had</i></li><li><i class="graytxt">we </i><i class="verbtxt">had</i></li><li><i class="graytxt">you </i><i class="verbtxt">had</i></li><li><i class="graytxt" style="">they </i><i class="verbtxt" style="">had</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicative Present continuous"><p>Present continuous</p><ul class="wrap-verbs-listing"><li><i class="graytxt" style="">I </i><i class="auxgraytxt" style="">am </i><i class="verbtxt" style="">having</i></li><li><i class="graytxt">you </i><i class="auxgraytxt">are </i><i class="verbtxt">having</i></li><li><i class="graytxt" style="">he/she/it </i><i class="auxgraytxt" style="">is </i><i class="verbtxt" style="">having</i></li><li><i class="graytxt" style="">we </i><i class="auxgraytxt" style="">are </i><i class="verbtxt" style="">having</i></li><li><i class="graytxt" style="">you </i><i class="auxgraytxt" style="">are </i><i class="verbtxt" style="">having</i></li><li><i class="graytxt" style="">they </i><i class="auxgraytxt" style="">are </i><i class="verbtxt" style="">having</i></li></ul></div></div></div><div class="word-wrap-row"><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicative Present perfect"><p>Present perfect</p><ul class="wrap-verbs-listing"><li><i class="graytxt">I </i><i class="auxgraytxt">have </i><i class="verbtxt">had</i></li><li><i class="graytxt">you </i><i class="auxgraytxt">have </i><i class="verbtxt">had</i></li><li><i class="graytxt">he/she/it </i><i class="auxgraytxt">has </i><i class="verbtxt">had</i></li><li><i class="graytxt">we </i><i class="auxgraytxt">have </i><i class="verbtxt">had</i></li><li><i class="graytxt">you </i><i class="auxgraytxt">have </i><i class="verbtxt">had</i></li><li><i class="graytxt">they </i><i class="auxgraytxt">have </i><i class="verbtxt">had</i></li></ul></div></div><div class="wrap-three-col"><div class="blue-box-wrap" mobile-title="Indicative Future"><p>Future</p><ul class="wrap-verbs-listing"><li><i class="graytxt" style="">I </i><i class="particletxt" style="">will </i><i class="verbtxt" style="">have</i></li><li><i class="graytxt" style="">you </i><i class="particletxt" style="">will </i><i class="verbtxt" style="">have</i></li><li><i class="graytxt" style="">he/she/it </i><i class="particletxt" style="">will </i><i class="verbtxt" style="">have</i></li><li><i class="graytxt" style="">we </i><i class="particletxt" style="">will </i><i class="verbtxt" style="">have</i></li><li><i class="graytxt" style="">you </i><i class="particletxt" style="">will </i><i class="verbtxt" style="">have</i></li><li><i class="graytxt" style="">they </i><i class="particletxt" style="">will </i><i class="verbtxt" style="">have</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicative Future perfect"><p>Future perfect</p><ul class="wrap-verbs-listing"><li><i class="graytxt" style="">I </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">have </i><i class="verbtxt" style="">had</i></li><li><i class="graytxt" style="">you </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">have </i><i class="verbtxt" style="">had</i></li><li><i class="graytxt" style="">he/she/it </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">have </i><i class="verbtxt" style="">had</i></li><li><i class="graytxt" style="">we </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">have </i><i class="verbtxt" style="">had</i></li><li><i class="graytxt" style="">you </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">have </i><i class="verbtxt" style="">had</i></li><li><i class="graytxt" style="">they </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">have </i><i class="verbtxt" style="">had</i></li></ul></div></div></div><div class="word-wrap-row"><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicative Past continous"><p>Past continous</p><ul class="wrap-verbs-listing"><li><i class="graytxt">I </i><i class="auxgraytxt">was </i><i class="verbtxt">having</i></li><li><i class="graytxt">you </i><i class="auxgraytxt">were </i><i class="verbtxt">having</i></li><li><i class="graytxt">he/she/it </i><i class="auxgraytxt">was </i><i class="verbtxt">having</i></li><li><i class="graytxt">we </i><i class="auxgraytxt">were </i><i class="verbtxt">having</i></li><li><i class="graytxt">you </i><i class="auxgraytxt">were </i><i class="verbtxt">having</i></li><li><i class="graytxt">they </i><i class="auxgraytxt">were </i><i class="verbtxt">having</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicative Past perfect"><p>Past perfect</p><ul class="wrap-verbs-listing"><li><i class="graytxt" style="">I </i><i class="auxgraytxt" style="">had </i><i class="verbtxt" style="">had</i></li><li><i class="graytxt" style="">you </i><i class="auxgraytxt" style="">had </i><i class="verbtxt" style="">had</i></li><li><i class="graytxt" style="">he/she/it </i><i class="auxgraytxt" style="">had </i><i class="verbtxt" style="">had</i></li><li><i class="graytxt">we </i><i class="auxgraytxt">had </i><i class="verbtxt">had</i></li><li><i class="graytxt">you </i><i class="auxgraytxt">had </i><i class="verbtxt">had</i></li><li><i class="graytxt">they </i><i class="auxgraytxt">had </i><i class="verbtxt">had</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicative Future continuous"><p>Future continuous</p><ul class="wrap-verbs-listing"><li><i class="graytxt" style="">I </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">be </i><i class="verbtxt" style="">having</i></li><li><i class="graytxt" style="">you </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">be </i><i class="verbtxt" style="">having</i></li><li><i class="graytxt" style="">he/she/it </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">be </i><i class="verbtxt" style="">having</i></li><li><i class="graytxt" style="">we </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">be </i><i class="verbtxt" style="">having</i></li><li><i class="graytxt" style="">you </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">be </i><i class="verbtxt" style="">having</i></li><li><i class="graytxt" style="">they </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">be </i><i class="verbtxt" style="">having</i></li></ul></div></div></div><div class="word-wrap-row"><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicative Present perfect continuous"><p>Present perfect continuous</p><ul class="wrap-verbs-listing"><li><i class="graytxt">I </i><i class="auxgraytxt">have </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">you </i><i class="auxgraytxt">have </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">he/she/it </i><i class="auxgraytxt">has </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">we </i><i class="auxgraytxt">have </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">you </i><i class="auxgraytxt">have </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">they </i><i class="auxgraytxt">have </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicative Past perfect continuous"><p>Past perfect continuous</p><ul class="wrap-verbs-listing"><li><i class="graytxt">I </i><i class="auxgraytxt">had </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">you </i><i class="auxgraytxt">had </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">he/she/it </i><i class="auxgraytxt">had </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">we </i><i class="auxgraytxt">had </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">you </i><i class="auxgraytxt">had </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">they </i><i class="auxgraytxt">had </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="blue-box-wrap" mobile-title="Indicative Future perfect continuous"><p>Future perfect continuous</p><ul class="wrap-verbs-listing"><li><i class="graytxt">I </i><i class="particletxt">will </i><i class="auxgraytxt">have </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt" style="">you </i><i class="particletxt" style="">will </i><i class="auxgraytxt" style="">have </i><i class="auxgraytxt" style="">been </i><i class="verbtxt" style="">having</i></li><li><i class="graytxt">he/she/it </i><i class="particletxt">will </i><i class="auxgraytxt">have </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">we </i><i class="particletxt">will </i><i class="auxgraytxt">have </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">you </i><i class="particletxt">will </i><i class="auxgraytxt">have </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li><li><i class="graytxt">they </i><i class="particletxt">will </i><i class="auxgraytxt">have </i><i class="auxgraytxt">been </i><i class="verbtxt">having</i></li></ul></div></div></div><div class="word-wrap-row"><div class="word-wrap-title two-col-right"><h4>Participle</h4></div><div class="wrap-three-col" style="margin-top: -21px;"><div class="word-wrap-title"><h4>Imperative </h4></div><div class="blue-box-wrap alt-tense" mobile-title="Imperative "><ul class="wrap-verbs-listing"><li><i class="verbtxt">have</i></li><li><i class="particletxt">let's </i><i class="verbtxt">have</i></li><li><i class="verbtxt">have</i></li></ul></div></div><div class="wrap-three-col"><div class="blue-box-wrap" mobile-title="Participle Present"><p>Present</p><ul class="wrap-verbs-listing"><li><i class="verbtxt">having</i></li></ul></div></div><div class="wrap-three-col"><div class="blue-box-wrap" mobile-title="Participle Past"><p>Past</p><ul class="wrap-verbs-listing top3"><li><i class="verbtxt">had</i></li></ul></div></div></div><div class="word-wrap-row"><div class="wrap-three-col"><div class="word-wrap-title"><h4>Infinitive </h4></div><div class="blue-box-wrap alt-tense" mobile-title="Infinitive "><ul class="wrap-verbs-listing top1"><li><i class="particletxt">to </i><i class="verbtxt">have</i></li></ul></div></div><div class="wrap-three-col" c="1"><div class="word-wrap-title"><h4>Perfect participle </h4></div><div class="blue-box-wrap" mobile-title="Perfect participle "><ul class="wrap-verbs-listing"><li><i class="auxgraytxt">having </i><i class="verbtxt">had</i></li></ul></div></div></div></div></div>
# """

CONJUGATION_LINKS = {
	"enfr": {
		"Indicative.Present": "Indicatif.Présent",
		"Indicative.Present": "Indicatif.Présent"
	}
}


def conjugation_table(_from: str, _to: str, verb: str | None = None, time: str|None=None):
	if _to not in short_names and _to not in short_names.values():
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

		# print(data)

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
		# for t in data[mood]:
			title = None if len(data[mood]) == 1 else mood.upper()
			table = Table(title=title)
			# for submood, value in data[mood].items():
			# 	print(submood, value, bool(value), type(value))
			if all(
					all(k for k in subdict)
					for subdict in data[mood].values()
				):
				table.add_column("", justify="left", style="bold")
			conj_lists = []
			col0 = True
			# print(t)
			if data[mood]:
				for submood in data[mood]:
					# print(data[mood][submood].keys())
					table.add_column(submood.upper(), justify="left")
					i = 0
					# compute shared prefix/suffix for this submood (whole mood-aware highlighting)
					mains = []
					for conj_val in data[mood][submood].values():
						parts = conj_val.strip().rsplit(' ', 1)
						# print(parts)
						main = parts[-1] if parts else conj_val
						mains.append(main)
					# include base main (verb) in shared computation
					# print(parts, mains)
					base_main = verb.split()[-1] if verb else ''
					shared_pref, shared_suf = _shared_prefix_suffix([base_main] + mains)
					for conj in data[mood][submood]:
						# print("    "+conj)
						if i >= len(conj_lists):
							conj_lists.append([])
						if col0 and conj:
							conj_lists[i].append(Text(conj))
						highlighted = highlight_conj(verb, data[mood][submood][conj], shared_pref=shared_pref, shared_suf=shared_suf)
						conj_lists[i].append(highlighted)
						i += 1
					col0 = False
			# print(conj_lists)
				for r in conj_lists:
					table.add_row(*r)

				console = Console()
				console.print(table)
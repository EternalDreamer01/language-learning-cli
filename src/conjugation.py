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

from email.mime import base
import sys, re
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
		# print("error")
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

PRONOUNS = {
	"en": ["I", "you", "he/she/it", "we", "you", "they"],
	"fr": ["je", "tu", "il/elle/on", "nous", "vous", "ils/elles"],
	"es": ["yo", "tú", "él/ella/usted", "nosotros/as", "vosotros/as", "ellos/ellas/ustedes"],
}

CONJUGATION_LINKS = {
	"enfr": {
		"Indicative.Present": "Indicatif.Présent",
		"Indicative.Future": "Indicatif.Futur",
		# "Indicative.Present": "Indicatif.Présent"
	},
	"enes": {
		"Indicative.Present": "Indicativo.Presente",
		"Indicative.Future": "Indicativo.Futuro",
		# "Indicative.Present": "Indicatif.Présent"
	},
	"esfr": {
		"Indicativo.Presente": "Indicatif.Présent",
		"Indicativo.Futuro": "Indicatif.Futur",
		"Indicativo.Futuro perfecto": "Indicatif.Futur antérieur",

		"Indicativo.Pretérito perfecto simple": "Indicatif.Passé composé",
		"Indicativo.Pretérito perfecto compuesto": "Indicatif.Passé composé",
		"Indicativo.Pretérito imperfecto": "Indicatif.Imparfait",
		"Indicativo.Pretérito pluscuamperfecto": "Indicatif.Plus-que-parfait",
		"Indicativo.Pretérito anterior": "Indicatif.Passé antérieur",

		"Indicativo.Condicional": "Conditionnel.Présent",
		"Indicativo.Condicional perfecto": "Conditionnel.Passé première forme",

		"Subjuntivo.Presente": "Subjonctif.Présent",
		# "Subjuntivo.Futuro": "Subjonctif.Futur",
		# "Subjuntivo.Futuro perfecto": "Subjonctif.Futur antérieur",

		"Subjuntivo.Pretérito perfecto simple": "Subjonctif.Passé",
		"Subjuntivo.Pretérito imperfecto": "Subjonctif.Imparfait",
		"Subjuntivo.Pretérito imperfecto (2)": "Subjonctif.Imparfait",
		"Subjuntivo.Pretérito pluscuamperfecto": "Subjonctif.Plus-que-parfait",
		"Subjuntivo.Pretérito anterior": "Subjonctif.Passé antérieur",

		"Infinitivo": "Infinitif.Présent",
		"Infinitivo compuesto": "Infinitif.Passé",

	}
}


# CONJUGATION_LINKS = {
# 	"Indicative.Present": {
# 		"fr": "Indicatif.Présent",
# 		"es": "Indicativo.Presente",
# 	},
# 	"Indicative.Future": {
# 		"fr": "Indicatif.Futur",
# 		"es": "Indicativo.Futuro",
# 	},
# 	"Indicative.Preterite": {
# 		"fr": "Indicatif.Passé Composé",
# 		"es": "Indicativo.Pretérito imperfecto",
# 	},
# }


def link_pronouns(pronoun: str, from_code: str, to_code: str) -> str:
	if pronoun.startswith("qu'"):
		pronoun = pronoun[3:]
	pronoun = pronoun.strip().split(' ')[-1]
	# print("Linking pronoun:", pronoun, from_code, "->", to_code)
	from_pronouns = PRONOUNS.get(from_code, [])
	to_pronouns = PRONOUNS.get(to_code, [])
	if pronoun in from_pronouns:
		# print("Found pronoun:", pronoun)
		index = from_pronouns.index(pronoun)
		if index < len(to_pronouns):
			return to_pronouns[index]
		return ""
	base = pronoun.split('/')[0]
	# print("Base pronoun:", base)
	for i, p in enumerate(from_pronouns):
		if base == p.split('/')[0]:
			if i < len(to_pronouns):
				return to_pronouns[i]
	return ""

def reverse_link_pronouns(data_from: dict, path: str, pronoun_from: str) -> str:
	def __pronoun_replace(match: re.Match) -> str:
		pronoun_from = match.group(0)
		# print("group:", pronoun_from)
		if pronoun_from == "/usted":
			return "/Ud"
		elif pronoun_from == "/ustedes":
			return "/Uds"
		return ""
	# print(data_from)
	return data_from.get(f"{path}.{re.sub(r"qu(?:e\s+|')|/(on|as|usted(es)?)$", __pronoun_replace, pronoun_from)} ")


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
	verb_from = translate_word(_to, _from, verb, get_first_string=True)
	language = short_names[_from] or _from

	# print(verb_from)

	d = requests.get(
		f"https://conjugator.reverso.net/conjugation-{language}-verb-{verb_from}.html",
		headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"}
	).text

	data_from = parse_conjugation_data(d) #{"": None, "": None, "": None, "": None, "": None, "": None, "": None, "": None, "": None, "": None, "": None, "": None} # parse_conjugation_data(d)
	if data_from is None:
		print(f"Error: Unable to fetch conjugation data for verb '{verb}' in language '{_to}'.", file=sys.stderr)
		sys.exit(1)


	# print(data_from["Subjonctif"], data["Subjuntivo"].keys())
	conj_lnk_lang = _from+_to if _from+_to in CONJUGATION_LINKS else _to+_from


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
						
						pronoun_from = link_pronouns(conj, _to, _from)
						if col0 and conj:
							pronoun = Text()
							pronoun.append(conj.strip(), style="bold")
							pronoun.append("; ", style="normal")
							pronoun.append(pronoun_from, style="italic green")
							conj_lists[i].append(pronoun)
						highlighted = highlight_conj(verb, data[mood][submood][conj], shared_pref=shared_pref, shared_suf=shared_suf)
						# print(f"{_from+_to}.'{mood}.{submood}'", _from+_to in CONJUGATION_LINKS, CONJUGATION_LINKS.get(_from+_to), )
						conj_lnk_key = CONJUGATION_LINKS[conj_lnk_lang].get(f"{mood}.{submood}") or \
							next((key for key, val in CONJUGATION_LINKS[conj_lnk_lang].items() if val == f"{mood}.{submood}"), None) or \
							CONJUGATION_LINKS[conj_lnk_lang].get(mood)
						# if conj_lnk_key:
						# 	print(len(data[mood][submood]), data_from.get(conj_lnk_key+"."), data_from.get(conj_lnk_key))
						if conj_lnk_key:
							# there is data in the from language
							# print("Indicative" in data_from, "Present" in data_from["Indicative"], type(data_from), data_from[f"{conj_lnk_key}"], "'"+pronoun_from+"'")
							if pronoun and pronoun_from:
								# print("Warning: Unable to link pronoun", conj, "from", _to, "to", _from, file=sys.stderr)
								conj_from = reverse_link_pronouns(data_from, conj_lnk_key, pronoun_from)
								# print(conj_from)
								if conj_from:
									highlighted.append(Text(", "))
									# highlighted.append(link_pronouns(conj, _to, _from), style="italic green")
									highlighted.append(Text(conj_from, style="italic green"))
							elif len(data[mood][submood]) == 1:
								# print("OK")
								if data_from.get(conj_lnk_key+".") is not None:
									highlighted.append(Text(", "))
									highlighted.append(Text(data_from.get(conj_lnk_key+"."), style="italic green"))
								elif data_from.get(conj_lnk_key) is not None:
									# print(data_from.get(conj_lnk_key))
									val = next(iter(data_from.get(conj_lnk_key).values()))
									val = next(iter(val.values()))
									highlighted.append(Text(", "))
									highlighted.append(Text(val, style="italic green"))
								# print(len(data[mood][submood]))
						conj_lists[i].append(highlighted)
						i += 1
					col0 = False
			# print(conj_lists)
				for r in conj_lists:
					table.add_row(*r)

				console = Console()
				console.print(table)
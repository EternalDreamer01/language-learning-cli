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
from src import *

if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog="language-learning-cli", description="A CLI tool for language learning.")
	parser.add_argument('FROM', nargs="?")
	parser.add_argument('TO', nargs="?")
	parser.add_argument('WORD', metavar="WORD | TEXT", nargs="?")
	parser.add_argument('-c', '--conjugation', action='store_true', help='Conjugate verbs')
	parser.add_argument('-w', '--translate-word', action='store_true', help='Translate word')
	parser.add_argument('-t', '--translate-text', action='store_true', help='Translate text')

	parser_translate_word = parser.add_argument_group("Translate Word")
	parser_translate_word.add_argument('-f', '--compound-forms', dest="COMPOUND", action='store_true', help='Include compound forms')
	parser_translate_word.add_argument('-o', '--compact', dest="COMPACT", action='store_true', help='Compact translate word output (without examples)')
	parser_translate_word.add_argument('-m', '--main', dest="MAIN", action='store_true', help='Main translation only (first results)')
	args = parser.parse_args()

	# print(args)

	load_dotenv()

	_from = (os.getenv("DEFAULT_LANGUAGE_FROM", "en") if args.FROM is None else args.FROM).strip().lower()
	_to = (os.getenv("DEFAULT_LANGUAGE_TO", "es") if args.TO is None else args.TO).strip().lower()

	if args.conjugation:
		conjugation_table(_from, _to, args.WORD)

	elif _from == _to:
		print("FROM and TO are the same language", file=sys.stderr)
		sys.exit(1)

	elif args.translate_word:
		translate_word(_from, _to, args.WORD, args.COMPOUND, args.COMPACT, args.MAIN)
		# print(json.dumps(WordReference(_from, _to).translate(args.translate_word)))

	elif args.translate_text:
		translate_text(_from, _to, args.WORD)
		# print(json.dumps(WordReference(_from, _to).translate(args.translate_word)))

	else:
		train_vocabulary(_from, _to)


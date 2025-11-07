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
	parser.add_argument('-c', '--conjugation', action='store_true', help='Conjugate verbs')
	parser.add_argument('-w', '--translate-word', type=str, help='Translate word')
	parser.add_argument('-f', '--compound-forms', action='store_true', help='Include compound forms')
	parser.add_argument('-t', '--translate-text', type=str, help='Translate text')
	args = parser.parse_args()

	# print(args)

	load_dotenv()

	_from = (os.getenv("DEFAULT_LANGUAGE_FROM", "en") if args.FROM is None else args.FROM).strip().lower()
	_to = (os.getenv("DEFAULT_LANGUAGE_TO", "es") if args.TO is None else args.TO).strip().lower()
	# wr

	if _from == _to:
		print("FROM and TO are the same language", file=sys.stderr)
		sys.exit(1)

	if args.conjugation:
		# conjugation_table(_from, _to)
		pass
	elif args.translate_word:
		translate_word(_from, _to, args.translate_word, args.compound_forms)
		# print(json.dumps(WordReference(_from, _to).translate(args.translate_word)))
	else:
		train_vocabulary(_from, _to)


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


def conjugation_table(_from: str, _to: str, time: str|None=None):
	try:
		with open(os.path.join(os.path.dirname(__file__), "time", f"{_from}-{_to}.md"), "r") as f:
			def highlight(match):
				return f"\x1b[1;36m{match.group(0)}\x1b[0m"
			print(re.sub(r"#(.*)", highlight, f.read()))
	except FileNotFoundError:
		print(f"Error: No conjugation table found for '{_from}' to '{_to}'.", file=sys.stderr)
		sys.exit(1)


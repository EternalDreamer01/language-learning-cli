#!/usr/bin/python3
################################################################################
# @file      translate copy.py
# @brief     
# @date      Tu Dec 2025
# @author    Dimitri Simon
# 
# PROJECT:   src
# 
# MODIFIED:  Tue Dec 23 2025
# BY:        Dimitri Simon
# 
# Copyright (c) 2025 Dimitri Simon
# 
################################################################################

import os, json
from pathlib import Path


def translate_text(from_code: str, to_code: str, text: str) -> str:

	# path_cache_translated = os.path.join(str(Path.home()), ".cache/language-learning", "translate-text.json")
	# cache_data = {}
	# if os.path.exists(path_cache_translated):
	# 	with open(path_cache_translated, "r", encoding="utf-8") as f:
	# 		cache_data = json.load(f)

	# 	if text in cache_data:
	# 		cached_entry = cache_data[text]
	# 		if cached_entry["from"] == from_code and cached_entry["to"] == to_code:
	# 			print(cached_entry["translation"])
	# 			return
	# 	key = next(
	# 		(k for k, o in cache_data.items()
	# 		if
	# 			o["translation"] == text and ((
	# 			o["to"] == to_code and o["from"] == from_code) or (
	# 			o["to"] == from_code and o["from"] == to_code))
	# 		),
	# 		None
	# 	)
	# 	if key is not None:
	# 		print(key)
	# 		return

	import argostranslate.package
	import argostranslate.translate
 
	# Download and install Argos Translate package
	argostranslate.package.update_package_index()
	available_packages = argostranslate.package.get_available_packages()

	package_to_install = next(
		filter(
			lambda x: (x.from_code == from_code and x.to_code == to_code),
			available_packages
		)
	)
	argostranslate.package.install_from_path(package_to_install.download())

	translation = argostranslate.translate.translate(text, from_code, to_code)
	print(translation)

	# if text != translation and len(text) < 200000000:
	# 	cache_data[text] = {
	# 		"from": from_code,
	# 		"to": to_code,
	# 		"translation": translation
	# 	}
	# 	with open(path_cache_translated, "w", encoding="utf-8") as f:
	# 		json.dump(cache_data, f, ensure_ascii=False)

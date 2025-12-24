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


def translate_text(from_code: str, to_code: str, text: str) -> str:
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

	print(argostranslate.translate.translate(text, from_code, to_code))
#!/usr/bin/python3
################################################################################
# @file      llm.py
# @brief     
# @date      Su Jul 2025
# @author    Dimitri Simon
# 
# PROJECT:   CVE checker
# 
# MODIFIED:  Tue Jul 08 2025
# BY:        Dimitri Simon
# 
# Copyright (c) 2025 Dimitri Simon
# 
################################################################################


import ollama
import unittest
import os, json, random
# from .constants import CVELIST_DIRECTORY

CVE_SUBMODULE_PATH = os.getenv("CVE_SUBMODULE_PATH", "./cvelistV5")


USER_PROMPT_TEMPLATE = """
You are a helpful assistant.
You are given a list of translated words in different languages.

Task: Infer the shared context or theme that connects all of the given words.

Output format:
* Respond in valid JSON.
* Use the language code as the key (e.g., "fr", "es").
* Provide one short hint (1-3 words) as the value, written in that language.
* The hint must describe the same common meaning or domain for all languages.
* Do not include explanations or extra text — only the JSON.

Example:
{
  "fr": "sport",
  "es": "deporte"
}

Words:
"""


def get_wordlist(lang: str) -> list:
	with open(os.path.join(os.path.dirname(__file__), "most-common-words-multilingual/data/wordfrequency.info", lang+".txt"), "r") as f:
		return f.read().splitlines()

wordlist = {
    "fr": get_wordlist("fr"),
    "en":get_wordlist("en"),
    "es":get_wordlist("es"),
    "de":get_wordlist("de"),
    "ru":get_wordlist("ru"),
    "zh":get_wordlist("zh-CN"),
    "ko":get_wordlist("ko"),
}


pos = random.randint(50, len(wordlist["fr"]))

words = "\n".join([f"[{k}] {v[pos]}" for k, v in wordlist.items()])

print(words)

response = ollama.generate(
	model="gemma3:1b",
	# system=SYSTEM_PROMPT,
	prompt=USER_PROMPT_TEMPLATE + words,
	# options={
	# 	"temperature": 0.0,
	# 	"num_predict": 3,
	# 	"seed": 16,
	# 	"top_p": 0.9
	# }
).response.strip()
print("LLM response:", response)
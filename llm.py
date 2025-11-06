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
import re, random, math, json
from pathlib import Path
from unidecode import unidecode
from wrpy import WordReference
import ollama


response = ollama.generate(
    model="qwen3:1.7b",
    prompt="Write 1 or 2 casual French sentences (≤110 characters) about daily life, as a casual reply or message to someone. No greetings at the start or end."
).response

# response = re.sub(r". \(\d+\s.+\)", ".", response)

print(response)

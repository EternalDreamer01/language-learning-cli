#!/usr/bin/env python3

from wrpy import WordReference
from json import dumps
from sys import argv

if len(argv) < 2:
    print({})
else:
	print(dumps(WordReference("fren" if len(argv) == 2 else argv[2]).translate(argv[1])))
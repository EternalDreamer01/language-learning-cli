#!/usr/bin/python3
################################################################################
# @file      input.py
# @brief     
# @date      Fr Nov 2025
# @author    Dimitri Simon
# 
# PROJECT:   language-learning-cli
# 
# MODIFIED:  Fri Nov 07 2025
# BY:        Dimitri Simon
# 
# Copyright (c) 2025 Dimitri Simon
# 
################################################################################

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.keys import Keys


ALWAYS_VISIBLE = [" ", "-", "'"]

# Grave, Acute, ^, ~, °
ACCENT = {
	"a": ("à", "á", "â", "ã", "ä", "å"),
	"e": ("è", "é", "ê", "" "ë"),
	"i": ("ì", "í", "î", "", "ï"),
	"o": ("ò", "ó", "ô", "õ", "ö"),
	"u": ("ù", "ú", "û", "", "ü"),
	"y": ("ỳ", "ý", "ŷ", "", "ÿ"),
	"n": ("", "", "", "ñ"),
}
TRANSCRIPT_CHAR = "<>&~:°"
TRANSCRIPT_LAYOUT = {
    "a": "а",
    "b": "б",
    "v": "в",
    "g": "г",
    "d": "д",
    # "e": ("e", "ye"),
	# ":": ("ё", "yo"),
	"j": "ж",
	"z": "з",
	"i": "и",
	"k": "к",
	"l": "л",
	"m": "м",
	"n": "н",
	"p": "п",
	"r": "р",
	"s": "с",
	"u": "у",
	"f": "ф",
	"x": "х",
	"\"": "ъ",
	"'": "ь",
	"e": "э",

	"h": {
		"c": ("ч", "ch"),
		"s": ("ш", "sh"),
		"h": ("щ", "sch")
	},
	"t": {
		"t": "т",
		"s": "ц"
	},
	"y": {
		"e": "е",
		"o": "ё",
		"i": ("й", "yi"),
		"y": ("ы", "y"),
		"u": "ю",
		"a": "я"
	}
}
def transcript_get_char(d: str | tuple) -> str:
	if isinstance(d, tuple):
		return d[0]
	return d

def transcript_latin(s: str) -> str:
    result = ""
    for c in s:
        found = False

        # Check top-level mappings
        for k, v in TRANSCRIPT_LAYOUT.items():
            if isinstance(v, str) and v == c:
                result += k
                found = True
                break
            elif isinstance(v, dict):
                # Check nested mappings
                for sub_k, sub_v in v.items():
                    if isinstance(sub_v, str) and sub_v == c:
                        result += k + sub_k
                        found = True
                        break
                    elif isinstance(sub_v, tuple):
                        if sub_v[0] == c:  # Cyrillic letter match
                            result += sub_v[1]  # Use the 2nd element (Latin)
                            found = True
                            break
                if found:
                    break

        if not found:
            result += c  # Keep unknown characters as-is

    return result

TRANSCRIPT_LAYOUT_COUNTRY_CODE = ["UK", "RU"]
DEFAULT_CHAR = -1


def slot_input(from_colour: str, to_colour: str, from_text: str, to_text: str, prompt_text: str, length: int, filled_slots: dict = {}, newline: bool = True, expect_full_input: bool = False) -> str:
	entered = ""
	special_char = DEFAULT_CHAR

	def autofill(res: str):
		curr_len = len(res)
		if curr_len in filled_slots:
			res += filled_slots[curr_len]
			return autofill(res)
		return res

	entered = autofill(entered)
	min_len = len(entered)

	def autodelete(res: str):
		nonlocal min_len
		curr_len = len(res)
		if curr_len > min_len and curr_len in filled_slots:
			return autodelete(res[:-1])
		return res


	style = Style.from_dict({
		"from": from_colour,
		"to": to_colour,
		# "prompt": "#00ffff bold",
		# "filled": "#00ff00",
		# "empty": "#ffffff",
        "highlight": "bold #00dd00",
        "note": "italic",
        
	})

	# dynamic content
	def get_display():
		fragments = [
      		("class:prompt", "["),
        	("class:from", from_text),
			("class:prompt", f"] {prompt_text}  ["),
			("class:to", to_text),
			("class:prompt", "]> ")
		]
  
		for i in range(length):
			# char = entered[i]
			if i in filled_slots:
				fragments.append(("class:highlight", filled_slots[i]))
			elif i < len(entered):
				fragments.append(("class:filled", entered[i]))
			else:
				fragments.append(("class:empty", "▉"))
		if entered and to_text in TRANSCRIPT_LAYOUT_COUNTRY_CODE:
			fragments.append(("class:normal", ", "))
			fragments.append(("class:note", transcript_latin(entered)))
		return fragments

	control = FormattedTextControl(get_display, show_cursor=False)
	window = Window(content=control)
	layout = Layout(container=window)

	kb = KeyBindings()

	@kb.add("c-c")
	def _(event):
		event.app.exit(exception=KeyboardInterrupt)
		
	@kb.add("c-d")
	def _(event):
		event.app.exit()

	@kb.add("c-x")
	def _(event):
		event.app.exit(result="")
  
	@kb.add("enter")
	def _(event):
		if expect_full_input:
			if len(entered) == length:
				event.app.exit(result=entered)
		else:
			event.app.exit(result=entered)

	@kb.add("backspace")
	def _(event):
		nonlocal entered
		nonlocal min_len

		if len(entered) > min_len:
			entered = entered[:-1]
			event.app.invalidate()
			entered = autodelete(entered)

	@kb.add(Keys.Any)
	def _(event):
		nonlocal entered
		nonlocal special_char
		if event.data not in ALWAYS_VISIBLE and len(entered) < length and event.data.isprintable():
			# print(to_text.upper(), TRANSCRIPT_LAYOUT_COUNTRY_CODE)
			if to_text in TRANSCRIPT_LAYOUT_COUNTRY_CODE:
				# print("Transcripting")
				if special_char != DEFAULT_CHAR:
					if event.data in TRANSCRIPT_LAYOUT[special_char]:
						entered += transcript_get_char(TRANSCRIPT_LAYOUT[special_char][event.data.lower()])
					special_char = DEFAULT_CHAR

				elif event.data.lower() in TRANSCRIPT_LAYOUT:
					if isinstance(TRANSCRIPT_LAYOUT[event.data.lower()], dict):
						special_char = event.data.lower()
					else:
						entered += transcript_get_char(TRANSCRIPT_LAYOUT[event.data.lower()])
				else:
					entered += event.data

			elif event.data in TRANSCRIPT_CHAR:
				special_char = TRANSCRIPT_CHAR.index(event.data)
				return

			elif special_char != DEFAULT_CHAR:
				# print(special_char)
				if event.data in ACCENT and special_char < len(ACCENT[event.data]) and ACCENT[event.data][special_char]:
					entered += ACCENT[event.data][special_char]
				special_char = DEFAULT_CHAR
			else:
				entered += event.data
			event.app.invalidate()
			entered = autofill(entered)


	app = Application(layout=layout, key_bindings=kb, style=style, full_screen=False)
	result = app.run()
	# if newline:
	# 	print()
	return result

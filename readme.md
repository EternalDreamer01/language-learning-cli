
# Language Learning CLI

Learn language vocabulary through CLI.

## Features

| Feature | Works offline |
|:-       |:-             |
| Train vocabulary | ✅ |
| Translation | ❌ |
| Conjugation table | ❌ |

## Setup

```sh
git clone https://github.com/EternalDreamer01/language-learning-cli.git
cd language-learning-cli
pip3 install -r requirements.txt
```

## Train Vocabulary - Characters management

### Accents

| Accent | Substitute || Accent | Substitute |
|-:|:-|-|-:|:-|
| ` (grave) | `<` || ~ (tilde) | `~` |
| ´ (acute) | `>` || ¨ (diaeresis) | `:` |
| ^ (circumflex) | `&` || ° (overring) | `°` |

#### Example
* Press `<` then `a` to get `à`.
* Press `:` then `i` to get `ï`.

### Cyrillic: Ukrainian and Russian

Each letter has a keyboard substitute :

| Target character | Letter substitute/combination || Target character | Letter substitute/combination |
|-:|:-|-|-:|:-|
| а | A || ф | F |
| б | B || х | X |
| в | V || ъ | " |
| г | G || ь | ' |
| д | D || э | E |
| ж | J || ч | HC |
| з | Z || ш | HS |
| и | I || щ | HH |
| к | K || т | TT |
| л | L || ц | TS |
| м | M || е | YE |
| н | N || ё | YO |
| о | O || й | YI |
| п | P || ы | YY |
| р | R || ю | YU |
| с | S *or* C || я | YA |
| у | U |


#### Example
Press `Y` then `A` to get `я`.

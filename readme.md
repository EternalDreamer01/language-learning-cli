
# Language Learning CLI

Learn languages through CLI.

| Feature           | Languages | Offline | Powered by |
|:-                 |:-         |:-       |:-          |
| Train vocabulary  | 9  : Romance languages $^1$, Slavic languages $^2$  | ✅ 10MB  | [frekwencja/most-common-words-multilingual](https://github.com/frekwencja/most-common-words-multilingual) |
| Conjugation table | 10 : English, French, Spanish, German, Italian, Portuguese, Hebrew, Russian, Arabic, Japanese          | ❌  | [Reverso](https://conjugator.reverso.net/) |
| Translate Word    | 43 : Romance languages $^1$, Russian, Languages of Asia $^3$ | ❌  | [`wrpy`](https://github.com/sdelquin/wrpy) (WordReference) |
| Translate Text    | 49 : Romance languages $^1$, Slavic languages $^2$, Languages of Asia $^3$ | ✅ 9GB  | [argos-translate](https://github.com/argosopentech/argos-translate) |

- 1: English, French, Italian, Spanish, Portuguese, Romanian, Catalan
- 2: Ukrainian, Russian
- 3: Chinese, Japanese, Korean

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

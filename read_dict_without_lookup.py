import os
import regex as re
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup

PATSKAŅI = "([aeȩiouîêâûôìèàùòĩẽãũõ]|[êèẽ]̹|ì)|î[ìĩ]|ûũ|i̭|j̭|ṷ"
DIVSKAŅI = ("[eauo][îìĩ]|[êâûôẽãũõèàùò](i|i̯|j̯)"
            "|[eao][ûùũ]|[êâôẽãõèàò][iṷ]"
            "|i[êèẽ]|[uûùũ][oôõò]|"
            "[ìèàùò][lnņŋmr]")
LĪDZSKAŅI = r"([bdfgģhjkķlļmnņŋprsštvzž])[\1:]?|[lnņŋmr][̃̂]|ñ"
FONĒMAS = re.compile("^(%s|%s|%s)$" % (PATSKAŅI, DIVSKAŅI, LĪDZSKAŅI))
OUTPUT_FILE = "target/LVPPV_lexemes.txt"
FREQ_FILE = "wordlist_LVK2022_20250714130321.csv"




def get_freq_sort():
    df = pd.read_csv(FREQ_FILE, skiprows=2)
    return df


def read_dict_line(line: str):
    if line:
        pattern = r'^(?!vai .*$)([\p{Ll}/]+(?:\d)?) \[(.*?)\].*'  # Matches if the string starts with "abc"

        match = re.match(pattern, line)
        if match:
            ortho = match.group(1).replace("/", "")
            return ortho, convert_lvsampa(match.group(2))


def convert_lvsampa(phonetic):
    # Sadalām pa skaņām, [v â r c], [a c:], [c iẽ m s]
    # Šis ir nepieciešams lai varētu nošķirt īsos/garos patskaņus, kas atzīmēti ar intonācijām
    seperated = []
    curr_sound = ""
    for char in phonetic:
        if FONĒMAS.search(curr_sound + char):
            curr_sound += char
        else:
            seperated.append(curr_sound)
            curr_sound = char
    seperated.append(curr_sound)

    for x in range(len(seperated)):
        # i^/u^
        seperated[x] = re.sub("i̯|j̭", "i^", seperated[x])
        seperated[x] = re.sub("ṷ", "u^", seperated[x])
        # c/č
        seperated[x] = re.sub("c", "c", seperated[x])
        seperated[x] = re.sub("č", "č", seperated[x])

        # Lauztā intonācija
        seperated[x] = re.sub("^î$", "īq", seperated[x])
        seperated[x] = re.sub("^ê̹$", "Ēq", seperated[x])
        seperated[x] = re.sub("^ê$", "ēq", seperated[x])
        seperated[x] = re.sub("^â$", "āq", seperated[x])
        seperated[x] = re.sub("^û$", "ūq", seperated[x])
        seperated[x] = re.sub("^ô$", "ōq", seperated[x])
        # Krītošā intonācija
        seperated[x] = re.sub("^(ì|ì)$", "i", seperated[x])
        seperated[x] = re.sub("^è̹$", "æ", seperated[x])
        seperated[x] = re.sub("^è$", "e", seperated[x])
        seperated[x] = re.sub("^à$", "a", seperated[x])
        seperated[x] = re.sub("^ù$", "u", seperated[x])
        seperated[x] = re.sub("^ò$", "o", seperated[x])
        # Stieptā intonācija
        seperated[x] = re.sub("^ĩ$", "ī=", seperated[x])
        seperated[x] = re.sub("^ẽ̹$", "Ē=", seperated[x])
        seperated[x] = re.sub("^ẽ$", "ē=", seperated[x])
        seperated[x] = re.sub("^ã$", "ā=", seperated[x])
        seperated[x] = re.sub("^ũ$", "ū=", seperated[x])
        seperated[x] = re.sub("^õ$", "ō=", seperated[x])

        # Divskaņi
        if re.match("[îêâûô]", seperated[x]):
            seperated[x] += "q"
        elif re.match("[ĩẽãũõ]", seperated[x]):
            seperated[x] += "="
        seperated[x] = re.sub("[âàã]", "a", seperated[x])
        seperated[x] = re.sub("[êèẽ]", "e", seperated[x])
        seperated[x] = re.sub("[îìĩ]", "i", seperated[x])
        seperated[x] = re.sub("(?<![uûùũ])[oôòõ]", "o", seperated[x])
        seperated[x] = re.sub("(?<=[uûùũ])[oôòõ]", "o", seperated[x])
        seperated[x] = re.sub("[ûùũ]", "u", seperated[x])

        match = re.match(r"([aeiou])([aeiou])|d[zž]", seperated[x])
        if match:
            seperated[x] = match.group(1)+"_"+match.group(2)

        # Intonācijas simboli uz slīdeņiem
        seperated[x] = re.sub("^ñ$", "n=", seperated[x])
        seperated[x] = re.sub("̂", "q", seperated[x])
        seperated[x] = re.sub("̃", "=", seperated[x])

    # Kā pēdējo darbību padarām īsos patskaņus galotnes zilbēs pārīsus.
    # Tikai, ja zilbe satur īso patskani galotnē, un ir bez sekojoša līdzskaņa izņemot -s
    word = ''.join(seperated)
    word = re.sub(r"[-*]", "", word)
    word = re.sub(r"(?<![aeEoiu_])([aeEiuo])(?=s?$)", r"\1x", word)
    return word


def get_filepaths(directory):
    file_paths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths


# directory: satur mapi ar LVPPV vārdnīcas caurskatītajiem teksta failiem.
def find_files(directory):
    found_files = {}
    file_dir = directory
    # files = ["./LVPPV/162.txt"]
    files = get_filepaths(file_dir)

    phono_dict = {}

    for file in files:
        if not file.endswith(".txt"):
            continue
        print(file)
        f = open(file, "r", encoding="utf-8")
        for line in f:
            if not (line.isspace() or line.strip().isnumeric() or not read_dict_line(line)):
                ortho, phono = read_dict_line(line)
                phono_dict[ortho] = phono
    return pd.DataFrame(list(phono_dict.items()), columns=['key', 'value'])



def main():
    directory = os.path.join(".", "LVPPV")
    a = find_files(directory)
    print(a.head())

    b = get_freq_sort()
    print(b.head())

    # Merge on 'key', keeping only matching rows (inner join)
    merged = pd.merge(a, b, left_on='key', right_on='Item', how='inner')
    merged = merged.drop(columns='Item')
    merged = merged.sort_values(by='Frequency', ascending=False)
    print(merged.head())

    merged.to_csv('LVPPV_lexemes.csv', index=False, encoding="utf-8")

main()
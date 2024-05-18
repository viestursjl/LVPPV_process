import os
import regex as re
import json
import requests
from bs4 import BeautifulSoup

id = 0
PATSKAŅI = "([aeȩiouîêâûôìèàùòĩẽãũõ]|[êèẽ]̹|ì)|î[ìĩ]|ûũ"
DIVSKAŅI = ("[eauo]î|[êâûôẽãũõ](i|i̯)"
            "|[eao]û|[êâôẽãõ][iṷ]"
            "|i[êèẽ]|[uù][oôõ]")
LĪDZSKAŅI = r"([bdfgģhjkķlļmnņŋprsštvzž])[\1:]?|[lnņŋmr][̃̂]|ñ"
FONĒMAS = re.compile("^(%s|%s|%s)$" % (PATSKAŅI, DIVSKAŅI, LĪDZSKAŅI))
ANALYZE_URL = "http://api.tezaurs.lv:8182/analyze/"
LEXICON = "Lexicon_v2.xml"
OUTPUT_FILE = "target/LVPPV_lexemes.json"


def api_call(url):
    response = requests.get(url)
    # print(f"{response.status_code}: '{response.reason}'")
    payload = response.json()
    return payload


def analyze_word(word, extra_info=""):
    vārdšķira = ""
    options = api_call(ANALYZE_URL + word)
    for opt in options:
        # TODO: Pievienot apstrādi extra_info, lai daudznozīmigiem šķirkļiem atrastu atbilstošo paradigmu.
        # t.i. absurds - var būt lietv. vai īpaš. v.

        if opt["Pamatforma"] == word:
            vārdšķira = get_paradigm_name(opt["Vārdgrupas nr"])
    return vārdšķira


def get_paradigm_name(num):
    with open(LEXICON, 'r', encoding="utf-8") as f:
        data = f.read()
    bs_data = BeautifulSoup(data, "xml")
    for p in bs_data.find_all("Paradigm"):
        if p["ID"] == num:
            return p["Name"]+"-phono"
    print("Nya! No paradigm? (´。＿。｀)")


def convert_phono(phonetic):
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
        seperated[x] = re.sub("i̯", "i^", seperated[x])
        seperated[x] = re.sub("ṷ", "u^", seperated[x])
        # c/č
        seperated[x] = re.sub("c", "ts", seperated[x])
        seperated[x] = re.sub("č", "tš", seperated[x])

        # Lauztā intonācija
        seperated[x] = re.sub("^î$", "iiq", seperated[x])
        seperated[x] = re.sub("^ê̹$", "ææq", seperated[x])
        seperated[x] = re.sub("^ê$", "eeq", seperated[x])
        seperated[x] = re.sub("^â$", "aaq", seperated[x])
        seperated[x] = re.sub("^û$", "uuq", seperated[x])
        seperated[x] = re.sub("^ô$", "ɔɔq", seperated[x])
        # Krītošā intonācija
        seperated[x] = re.sub("^(ì|ì)$", "i", seperated[x])
        seperated[x] = re.sub("^è̹$", "æ", seperated[x])
        seperated[x] = re.sub("^è$", "e", seperated[x])
        seperated[x] = re.sub("^à$", "a", seperated[x])
        seperated[x] = re.sub("^ù$", "u", seperated[x])
        seperated[x] = re.sub("^ò$", "ɔ", seperated[x])
        # Stieptā intonācija
        seperated[x] = re.sub("^ĩ$", "ii=", seperated[x])
        seperated[x] = re.sub("^ẽ̹$", "ææ=", seperated[x])
        seperated[x] = re.sub("^ẽ$", "ee=", seperated[x])
        seperated[x] = re.sub("^ã$", "aa=", seperated[x])
        seperated[x] = re.sub("^ũ$", "uu=", seperated[x])
        seperated[x] = re.sub("^õ$", "ɔɔ=", seperated[x])

        # Divskaņi
        if re.match("[îêâûô]", seperated[x]):
            seperated[x] += "q"
        elif re.match("[ĩẽãũõ]", seperated[x]):
            seperated[x] += "="
        seperated[x] = re.sub("[âàã]", "a", seperated[x])
        seperated[x] = re.sub("[êèẽ]", "e", seperated[x])
        seperated[x] = re.sub("[îìĩ]", "i", seperated[x])
        seperated[x] = re.sub("(?<![uûùũ])[oôòõ]", "ɔ", seperated[x])
        seperated[x] = re.sub("(?<=[uûùũ])[ôòõ]", "o", seperated[x])
        seperated[x] = re.sub("[ûùũ]", "u", seperated[x])

        # Intonācijas simboli uz slīdeņiem
        seperated[x] = re.sub("^ñ$", "n=", seperated[x])
        seperated[x] = re.sub("̂", "q", seperated[x])
        seperated[x] = re.sub("̃", "=", seperated[x])

    # Kā pēdējo darbību padarām īsos patskaņus galotnes zilbēs pārīsus.
    # Tikai, ja zilbe satur īso patskani galotnē, un ir bez sekojoša līdzskaņa izņemot -s
    word = ''.join(seperated)
    word = re.sub(r"(?<![aeæoiuɔ])([aeæiuɔ])(?=s?$)", r"\1x", word)
    return word


def create_lexeme(line):
    global id
    id += 1
    # Pieņemam, ka nenotiek speciāl gadījums, t.i. vārdu norāda sekojošā formā:
    # vārds [vârts], vai arī bez [], ja pieraksts un izruna sakrīt
    lex_info = line.split(" ")
    orthography = re.sub("[,;/]", "", lex_info[0])
    diffs = re.compile(r"\d+$")
    lemma_id = 1
    if diffs.search(orthography):
        lemma_id = re.findall(diffs, orthography)[-1]
        orthography = re.sub("[0-9]", "", orthography)

    phonetic = ""
    if len(lex_info) > 1:
        for info in lex_info[1:]:
            info = info.strip(",").strip(";")
            if info.startswith("[") and info.endswith("]"):
                phonetic = info[1:-1]
                break
        if not phonetic:
            phonetic = orthography
    else:
        phonetic = orthography

    paradigm = analyze_word(orthography)
    lexeme = {
        "lexeme_id": id,
        "entry_id": id,
        "human_id": orthography + ":" + str(lemma_id),
        "paradigm_name": paradigm,
        "lemma": convert_phono(phonetic),
        "ortho": orthography,
    }
    json_string = json.dumps(lexeme, ensure_ascii=False).encode('utf8')
    return json_string.decode()


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
    files = get_filepaths(file_dir)
    outfile = open(OUTPUT_FILE, "w", encoding="utf-8")
    for file in files:
        if not file.endswith(".txt"):
            continue
        print(file)
        f = open(file, "r", encoding="utf-8")
        for line in f:
            if not (line.isspace() or line.strip().isnumeric()):
                outfile.write(create_lexeme(line.strip())+"\n")


def main():
    find_files()


main()

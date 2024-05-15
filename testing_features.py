# import lzma
import json
# from bs4 import BeautifulSoup
# import requests
import os
# import pandas as pd
# import ass
import requests
from bs4 import BeautifulSoup
# from sqlalchemy import create_engine
# from sqlite3 import connect
# from utils.helpers import clean_ass_text

# url = "https://animetosho.org/series/mashle.17478"
# res = requests.get(url=url, timeout=60)
# soup = BeautifulSoup(res.text, 'html.parser')
# mal_div = soup.select("table > tbody > tr > td > div", limit=2)[-1]
# mal_id = int(mal_div.find("a", string="MAL").get("href").split("/")[-1])
# print(mal_id)
# data = ""
# with open("csvjson.json", "r+", encoding="utf-8") as f:
#     data = json.load(f)

# data = {int(item["id"]): item["members"] for item in data}
# with open("mal_id_member_count.json", "w+", encoding="utf-8") as f:
#     json.dump(data, f, indent=4)
import re


def find_numbers(input_string):
    # Regex para encontrar números conforme as condições especificadas
    regex = r'[0-9]{2,4}(?=\s)'
    matches = re.finditer(regex, input_string)
    results = [(match.group(), match.start()) for match in matches]
    return results


s_teste = "[ToonsHub] The Vexations of a Shut-In Vampire Princess S01E05 1080p HIDIVE \
WEB-DL AAC2.0 x264 (Dual-Audio, Multi-Subs)"
result = find_numbers(s_teste)
for res in result:
    text, idx = res
    print(text, s_teste[idx - 1])

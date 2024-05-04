# import lzma
# import json
# from bs4 import BeautifulSoup
# import requests
# import os
# import pandas as pd
# import ass
import requests
from bs4 import BeautifulSoup
# from sqlalchemy import create_engine
# from sqlite3 import connect
# from utils.helpers import clean_ass_text

url = "https://animetosho.org/series/mashle.17478"
res = requests.get(url=url, timeout=60)
soup = BeautifulSoup(res.text, 'html.parser')
mal_div = soup.select("table > tbody > tr > td > div", limit=2)[-1]
mal_id = int(mal_div.find("a", string="MAL").get("href").split("/")[-1])
print(mal_id)

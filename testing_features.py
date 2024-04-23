import lzma
import json
# from bs4 import BeautifulSoup
import requests

url = "https://animetosho.org/storage/attach/0017e6f3/%5BErai-raws%5D%20Bocchi%20the%20Rock%21%20-%2001%20%5B1080p%5D%5BMultiple%20Subtitle%5D%5BCBD345E3%5D_track3.eng.ass.xz"
response = requests.get(url=url, timeout=60)
# write into .xz file
with open("bocchi_test.xz", "wb") as f:
    f.write(response.content)

# testing reading lines from .xz file
with lzma.open("bocchi_test.xz", "rt", encoding="utf-8") as f:
    cont = 0
    for line in f:
        print(line)
        cont += 1
        if cont > 10:
            break


# getting all subtitle links from .json file
data = ""
with open("examples/bocchi_the_rock.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data["Bocchi the Rock!"]:
    print(item["sub_link"])

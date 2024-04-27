# import lzma
# import json
# from bs4 import BeautifulSoup
# import requests
import os
import pandas as pd
import ass
from sqlalchemy import create_engine
from sqlite3 import connect
from utils.helpers import clean_ass_text

# url = "https://animetosho.org/storage/attach/0017e6f3/%5BErai-raws%5D%20Bocchi%20the%20Rock%21%20-%2001%20%5B1080p%5D%5BMultiple%20Subtitle%5D%5BCBD345E3%5D_track3.eng.ass.xz"
# response = requests.get(url=url, timeout=60)


db_path = os.path.realpath('database/testing_quotes.db')
engine = create_engine(f'sqlite:///{db_path}', echo=False)
# this will not be viable for anime with large number of episodes
# since dataframe will have lots of rows, thus running out of memory
# let's change to chunks later
animes = os.listdir('data')  # get every anime folder
for anime in animes:  # iterate over every anime in data folder
    folder_path = 'data/' + anime + '/processed'
    # list of every .ass file in anime folder
    episodes = os.listdir(folder_path)

    table = []
    for episode in episodes:  # iterate over every episode
        path = folder_path + '/' + episode
        # get episode number (episode title is always anime_name_{episode_num}.ass)
        episode_number = episode.split('.')[0].split('_')[-1]

        try:
            with open(path, encoding='utf_8_sig') as f:
                doc = ass.parse(f)  # read .ass file
                events = doc.events  # get every dialogue line
                print(f'reading {path}')
                for event in events:
                    # we do not care about signs
                    if event.style.lower() == "signs" or \
                            event.name.lower() == "sign" or not event.name:
                        continue
                    # save every line with whoever said the line
                    cleaned_text = clean_ass_text(event.text)
                    table.append([episode_number, event.name, cleaned_text])
                    # and the episode number
        except Exception:
            print(f'error reading {path}')

    df = pd.DataFrame(table, columns=['Episode', 'Name', 'Quote'])
    # here, we will have duplicate OP and ED text, lets get the unique entries
    songs = df[(df["Name"] == "ED") | (df["Name"] == "OP")]
    # drop every row with op or ed
    df = df.drop(songs.index)
    # now just concat the unique texts from cleaned ops and eds
    songs = songs.drop_duplicates(subset=["Name", "Quote"])
    df = pd.concat([df, songs])
    df.to_sql("bocchi_quotes", con=engine, if_exists='replace', index=False)

# import lzma
import json
# from bs4 import BeautifulSoup
# import requests
import os
import pandas as pd
import ass
import requests
from bs4 import BeautifulSoup
# from sqlalchemy import create_engine
from sqlite3 import connect
# from utils.helpers import clean_ass_text
import time
from tqdm import tqdm

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
BRACKETS_REGEX = r'\{[^{}]*\}|\([^\[\]]*\)'

# def find_numbers(input_string):
#     # Regex para encontrar números conforme as condições especificadas
#     regex = r'[0-9]{2,4}(?=\s)'
#     matches = re.finditer(regex, input_string)
#     results = [(match.group(), match.start()) for match in matches]
#     return results


# s_teste = "[Erai-raws] Spy x Family Season 2 - 02 [1080p][Multiple Subtitle] \
# [ENG][POR-BR][SPA-LA][SPA][ARA][FRE][GER][ITA][RUS]"
# res = list(map(lambda x: x.lower(), s_teste.split(" ")))
# if "season" in res:
#     print(res[res.index("season") + 1])
def remove_special_characters(input_string: str) -> str:
    pattern = r'[\\\"\',.;:?-]'
    clean_text = re.sub(pattern, '', input_string)
    print(clean_text)
    return clean_text


def prepare_text_for_insertion(input_string: str) -> str:
    """
    This is used before writing dataframe to database. This is the last processing step.
    """
    regex = BRACKETS_REGEX
    clean_text = re.sub(regex, '', input_string)
    clean_text = clean_text.replace("\\N", " ").replace("  ", " ")
    return clean_text


st = "\"Oshi no- Ko-\""
# remove_special_characters(st)
# with open("data/ore_dake_level_up_na_ken/processed/ep_01.ass", encoding='utf_8_sig') as f:
#     doc = ass.parse(f)
#     # get every dialogue line
#     events = doc.events
#     for i, event in enumerate(events):
#         print(prepare_text_for_insertion(event.text))
#         if i > 5:
#             break


def quote_merge(db_path: str, table_name: str) -> pd.DataFrame:
    """
    Merges consecutive rows with the same NAME and EPISODE into a single row
    and updates the specified SQLite table with the merged data.

    Parameters:
    - db_path (str): Path to the SQLite database file.
    - table_name (str): Name of the table in the database to read from and update.

    Returns:
    - pd.DataFrame: DataFrame containing the merged data.

    Example:
    merged_df = quote_merge('path/to/database.db', 'quotes_table')
    """

    # Connect to the SQLite database
    conn = connect(db_path)

    # Read data from the specified table into a DataFrame
    df = pd.read_sql(f'SELECT * FROM {table_name}', conn)

    # Initialize variables
    new_df = []
    newquote = True

    # Iterate through rows with progress bar
    for i in tqdm(range(df.shape[0])):
        # Initialize variables for a new quote sequence at the start of iteration or when a new quote is encountered
        if newquote:
            if i == 0:  # For the first row, initialize variables
                start_time = df.loc[i]['START_TIME']
                quote = ""
                mal_id = df.loc[i]['MAL_ID']
                episode = df.loc[i]['EPISODE']
                end_time = df.loc[i]['END_TIME']
                name = df.loc[i]['NAME']

        newquote = False  # Reset newquote flag to False after initialization

        current_name = df.loc[i]['NAME']
        current_episode = df.loc[i]['EPISODE']

        # Append to existing quote if the current row belongs to the same quote sequence
        if current_name == name and current_episode == episode and name != 'Unknown':
            quote += ' ' + df.loc[i]['QUOTE']
            end_time = df.loc[i]['END_TIME']
        else:
            # If a new quote sequence starts, append the completed quote to new_df
            if len(quote) != 0:
                new_df.append([mal_id, episode, start_time, end_time, name, quote])
            newquote = True  # Set newquote flag to True to indicate the start of a new quote sequence
            start_time = df.loc[i]['START_TIME']  # Initialize variables for the new quote sequence
            quote = df.loc[i]['QUOTE']
            mal_id = df.loc[i]['MAL_ID']
            episode = df.loc[i]['EPISODE']
            end_time = df.loc[i]['END_TIME']
            name = df.loc[i]['NAME']


    # Convert merged data into a new DataFrame
    new_df = pd.DataFrame(new_df, columns=[
                          'MAL_ID', 'EPISODE', 'START_TIME', 'END_TIME', 'NAME', 'QUOTE'])

    # Update the SQLite table with merged data
    new_df.to_sql(table_name, con=conn,
                  if_exists='replace', index=False)

    # Close the database connection
    conn.close()

    return new_df


df = quote_merge('database/testing_quotes.db', 'natsume_yuujinchou_go_quotes')

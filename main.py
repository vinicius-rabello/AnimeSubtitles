import json
import logging
import time
import datetime
import os
# temporario até mudar o lugar da função
import pandas as pd
import sqlite3
from sqlite3 import connect
from tqdm import tqdm
# from typing import Dict, List
from utils.parsers import (
    download_subtitles,
)
from utils.helpers import (
    generate_ass_files,
    build_df_from_ass_files,
)
from utils.routines import build_json_with_links
from utils.writers import write_data
from utils.connectors import sqlite_connector
from utils.constants import FORMAT, DESIRED_SUBS

# setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    format=FORMAT,
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# Specify parameters
start = time.time()
page_count = 1
page_limit = 99
filter_links = None
desired_subs = DESIRED_SUBS

# getting links for subtitle files
# for page in range(1, page_count + 1):
#     data = build_json_with_links(
#         page=page,
#         limit_per_page=page_limit,
#         desired_subs=desired_subs,
#         filter_links=filter_links,
#     )
#     with open(f"examples/page_{page}.json", "w+", encoding="utf-8") as f:
#         json.dump(data, f, indent=4)
#
# end = time.time()
# logger.info(f"Finished getting links in {round(end - start)}s")

# downloading data from website and generating ass files
# file_path = "examples/page_1.json"
# anime_list = download_subtitles(
#     file_path=file_path,
# )
# created = generate_ass_files()

# # writing data to db for each anime
# if not created:
#     created = os.listdir("data")
# for anime in created:
#     logger.info(f"---------- Processing anime: {anime} ----------")
#     df = build_df_from_ass_files(file_path=file_path, anime_name=anime)
#     con = sqlite_connector(db_name="testing_quotes")
#     result = write_data(table_name=anime + "_quotes",
#                         con=con, df=df, if_exists="replace")
#     logger.info(f"Inserted {result} rows into database!")

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
                new_df.append(
                    [mal_id, episode, start_time, end_time, name, quote])
            newquote = True  # Set newquote flag to True to indicate the start of a new quote sequence
            # Initialize variables for the new quote sequence
            start_time = df.loc[i]['START_TIME']
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

conn = sqlite3.connect('database/testing_quotes.db') # connecting to the database
cursor = conn.cursor()
tables = cursor.execute("SELECT name FROM sqlite_master where type='table';").fetchall() # getting every table name
for table in tables:
    quote_merge('database/testing_quotes.db', table[0])
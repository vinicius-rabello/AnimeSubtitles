import logging
import pandas as pd
from typing import Literal, Optional
from sqlalchemy.engine.base import Engine
from .constants import FORMAT
from tqdm import tqdm
from sqlite3 import connect

# setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    format=FORMAT,
    level=logging.INFO,
    handlers=[logging.StreamHandler()])


def write_data(
    table_name: str, con: Engine, df: pd.DataFrame,
    if_exists: Literal["fail", "replace", "append"] = "fail",
    clear_songs: bool = True
) -> Optional[int]:
    # empty df
    if df.empty:
        logger.info("Nothing to be done, empty dataframe.")
        return 0

    if clear_songs:
        # TODO: this could use some work (maybe change to isin (op, opening, etc.))
        songs = df[(df["NAME"] == "ED") | (df["NAME"] == "OP")]
        if len(songs) > 0:
            # drop every row with op or ed
            df = df.drop(songs.index)
            # now just concat the unique texts from cleaned ops and eds
            songs = songs.drop_duplicates(subset=["NAME", "QUOTE"])
            df = pd.concat([df, songs])

    logger.info(f"Preparing to write {len(df)} rows into dataframe...")

    try:
        num_rows = df.to_sql(
            name=table_name, con=con, if_exists=if_exists, index=False
        )
    except Exception as e:
        logger.error(str(e))
        num_rows = 0

    return num_rows

def merge_quotes(db_path: str, table_name: str) -> pd.DataFrame:
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
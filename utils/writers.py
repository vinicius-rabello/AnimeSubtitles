import pandas as pd
from typing import Literal, Optional
from base_logger import logger
from sqlalchemy.engine.base import Engine


def write_data(
    table_name: str, con: Engine, df: pd.DataFrame,
    if_exists: Literal["fail", "replace", "append"] = "fail",
    clear_songs: bool = True
) -> Optional[int]:
    if clear_songs:
        songs = df[(df["Name"] == "ED") | (df["Name"] == "OP")]
        if len(songs) > 0:
            # drop every row with op or ed
            df = df.drop(songs.index)
            # now just concat the unique texts from cleaned ops and eds
            songs = songs.drop_duplicates(subset=["Name", "Quote"])
            df = pd.concat([df, songs])

    logger.info(f"Preparing to write {len(df)} rows into dataframe...")
    try:
        num_rows = df.to_sql(name=table_name, con=con,
                             if_exists=if_exists, index=False)
    except Exception as e:
        logger.error(str(e))
        num_rows = 0

    return num_rows

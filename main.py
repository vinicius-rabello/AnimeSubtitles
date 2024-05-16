import json
import logging
import time
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
page_limit = 2
filter_anime = ""
desired_subs = DESIRED_SUBS
test_file = True

# getting links for subtitle files
for page in range(1, page_count + 1):
    data = build_json_with_links(
        page=page,
        limit_per_page=page_limit,
        filter_anime=filter_anime,
        desired_subs=desired_subs
    )
    with open(f"examples/page_{page}.json", "w+", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

end = time.time()
logger.info(f"Finished getting links in {round(end - start)}s")

# downloading data from website and generating ass files
# TODO: rewrite whole file naming logic (rn we can lose data)
# for example: since we do not include seasons, we may overwrite files
# maybe go back to using enumerate and passing anime_list to rest of functions
anime_list = download_subtitles(
    file_path="examples/page_1.json",
    filter_anime=filter_anime
)
# TODO: need to change file name logic (too long, not needed)
created = generate_ass_files(filter_anime=filter_anime)

# writing data to db for each anime
for anime, eps_list in anime_list.items():
    logger.info(f"---------- Processing anime: {anime} ----------")
    df = build_df_from_ass_files(anime_name=anime)
    con = sqlite_connector(db_name="testing_quotes")
    result = write_data(table_name=anime + "_quotes",
                        con=con, df=df, if_exists="replace")
    logger.info(f"Inserted {result} rows into database!")

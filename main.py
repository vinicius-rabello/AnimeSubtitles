import json
import logging
# from typing import Dict, List
# from utils.parsers import (
#     download_subtitles,
# )
# from utils.helpers import (
#     generate_ass_files,
#     build_df_from_ass_files,
# )
from utils.routines import build_json_with_links
# from utils.writers import write_data
# from utils.connectors import sqlite_connector
from utils.constants import FORMAT, DESIRED_SUBS

# setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    format=FORMAT,
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# Specify parameters
page_count = 1
page_limit = 99
filter_anime = ""
desired_subs = DESIRED_SUBS
for page in range(1, page_count + 1):
    data = build_json_with_links(
        page=page,
        limit_per_page=page_limit,
        filter_anime=filter_anime,
        desired_subs=desired_subs
    )
    with open(f"examples/page_{page}.json", "w+", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# anime_list = download_subtitles("examples/page_1.json")
# for test_anime in anime_list[:1]:
# test_anime = "Helck"
# logger.info(f"---------- Processing anime: {test_anime} ----------")
# created = generate_ass_files(filter_anime=test_anime)
# df = build_df_from_ass_files(anime_name=test_anime, logs="minimal")
# con = sqlite_connector(db_name="testing_quotes")
# result = write_data(table_name=test_anime + "_quotes",
#                     con=con, df=df, if_exists="replace")
# logger.info(f"Inserted {result} rows into database!")

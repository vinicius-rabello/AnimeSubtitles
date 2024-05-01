import json
import logging
from utils.parsers import (
    get_animes_finished_from_page,
    get_batch_options_and_episode_count,
    get_subtitle_links,
    get_all_links_from_provider,
    get_all_subtitles_info,
    download_subtitles,
)
from utils.helpers import (
    extract_titles_and_anime_links,
    filter_links_from_provider,
    sort_options_by_priority,
    generate_ass_files,
    build_df_from_ass_files,
)
from utils.writers import write_data
from utils.connectors import sqlite_connector
from utils.constants import FORMAT

# setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    format=FORMAT,
    level=logging.INFO,
    handlers=[logging.StreamHandler()])


def routine(page: int = 1, limit_per_page: int = 1):
    data = {}
    animes = get_animes_finished_from_page(page=page)
    titles, links = extract_titles_and_anime_links(animes)
    logger.info(f"Will process {limit_per_page} entries from page {page}.")
    for title, link in zip(titles[:limit_per_page], links[:limit_per_page]):
        logger.info(f"Processing link: {link}")
        logger.info(f"Processing anime: {title}")
        data[title] = []

        providers_info, provider_names, episode_count = \
            get_batch_options_and_episode_count(title, link)
        logger.info(f"Batch Providers: {provider_names}")

        provider_selected = ""
        # sort provider_names by priority
        provider_names = sort_options_by_priority(provider_names)
        # search for a functional provider
        for provider_option in provider_names:
            subs = get_subtitle_links(providers_info[provider_option])
            if len(subs) > 1:
                provider_selected = provider_option
                logger.info(
                    f"Selected {provider_selected} provider for anime {title}.")
                break

        processing = True
        page = 1
        while processing:
            logger.info(f"Parsing page {page}")
            page_links = get_all_links_from_provider(
                provider_selected, page, link)
            data[title] += page_links
            processing = bool(page_links)
            page += 1
        data[title] = filter_links_from_provider(
            data[title], provider_selected, episode_count)

    for anime_title, anime_info in data.items():
        all_subs_info = get_all_subtitles_info(anime_title, anime_info)
        data[anime_title] = all_subs_info

    return data


# low limit for testing
page_count = 1
# amount of entries to get from each page (put 9999 to get all)
page_limit = 1
# for page in range(1, page_count + 1):
#     data = routine(page=page, limit_per_page=page_limit)
#     with open(f"examples/page_{page}.json", "w+", encoding="utf-8") as f:
#         json.dump(data, f, indent=4)

# f = open('examples/page_1.json')
# data = json.load(f)
# f.close()

# anime_list = download_subtitles("examples/page_1.json")
# for test_anime in anime_list[:1]:
test_anime = "Helck"
logger.info(f"---------- Processing anime: {test_anime} ----------")
created = generate_ass_files(filter_anime=test_anime)
df = build_df_from_ass_files(anime_name=test_anime, logs="minimal")
con = sqlite_connector(db_name="testing_quotes")
result = write_data(table_name=test_anime + "_quotes",
                    con=con, df=df, if_exists="replace")
logger.info(f"Inserted {result} rows into database!")

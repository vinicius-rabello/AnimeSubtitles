import json
from typing import List
from base_logger.base_logger import logger
from utils.parsers import (
    get_animes_finished_from_page,
    get_batch_options_and_episode_count,
    get_subtitle_links,
    get_all_links_from_provider,
    get_all_subtitles_info,
)
from utils.helpers import (
    extract_titles_and_anime_links,
    filter_links_from_provider,
    sort_options_by_priority,
)


def write_to_csv(links: List[str], titles: List[str],
                 sizes: List[float], file_name="data", sep=";,") -> None:
    if "." in file_name:
        file_name.split(".")[0]
    logger.info("Writing data to csv file...")
    with open(f"{file_name}.csv", "w+", encoding="utf-8") as f:
        f.write(f"link{sep} title{sep} count\n")
        for b, t, s in zip(links, titles, sizes):
            f.write(b + sep + t + sep + str(s) + "\n")
    logger.info("Done!")
    return


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
page_limit = 1  # amount of entries to get from each page (put 9999 to get all)
for page in range(1, page_count + 1):
    data = routine(page=page, limit_per_page=page_limit)
    with open(f"examples_{page}/test.json", "w+", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

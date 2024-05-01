import logging
from typing import Dict, List
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
from utils.constants import FORMAT, DESIRED_SUBS

logger = logging.getLogger(__name__)
level = logging.INFO
logging.basicConfig(
    format=FORMAT,
    level=level,
    handlers=[logging.StreamHandler()])


def build_json_with_links(
    page: int = 1,
    limit_per_page: int = 1,
    filter_anime: str = "",
    desired_subs: str = DESIRED_SUBS
) -> Dict[str, List[Dict[str, str]]]:
    """
    Constructs a dictionary containing anime titles and corresponding lists
    of dictionaries with subtitle and torrent link information.

    This function fetches a list of animes entries and its subtitles information (
    download link and language) from animethosho website. Supports filtering
    per anime name. For each title, it attempts to find a subtitle 
    provider that matches the desired subtitle language or style (if specified). 
    It collects and returns all relevant links to subtitles for each anime title 
    processed.

    Parameters:
    - page (int): The page number from which to fetch data. Default is 1.
    - limit_per_page (int): The maximum number of anime titles to process from 
    the fetched page. If you want all from the page, set to a high value like 999.
    Default is 1.
    - filter_anime (str): A specific anime title to search for within the page.
    If empty, all titles from the page are processed. Best used with large
    limit_per_page, to make sure it will search the entire page.
    Default is an empty string.
    - desired_subs (str): The desired subtitle language (e.g. "eng"). 
    Default is "eng".

    Returns:
    - Dict[str, List[Dict[str, str]]]: A dictionary where each key is an anime title 
    and each value is a list of dictionaries. Each dictionary in the list contains 
    details about available subtitle links for that anime.

    The function logs various information and errors throughout the processing, 
    including issues with data fetching, provider selection, and subtitle retrieval. 
    It continues processing next titles or pages until the specified limit is 
    reached or there are no more entries.
    """
    data = {}
    animes = get_animes_finished_from_page(page=page)

    if not animes:
        logger.error(f"Bad response from page {page}. Skipping...")
        return {}

    if filter_anime:
        logger.info(f"Searching only for anime {filter_anime}.")

    titles, links = extract_titles_and_anime_links(
        animes=animes, filter_anime=filter_anime
    )

    logger.info(
        f"Will process a maximum of {limit_per_page} entries from page {page}."
    )
    for title, link in zip(titles[:limit_per_page], links[:limit_per_page]):
        logger.info(f"Processing link: {link}")
        logger.info(f"Processing anime: {title}")
        data[title] = []

        providers_info, provider_names, episode_count = \
            get_batch_options_and_episode_count(title=title, link=link)
        logger.debug(f"Batch Providers: {provider_names}")

        if len(provider_names) == 0:
            # nothing we can do
            logger.warning(
                f"No available provider for anime {title}. Skipping..."
            )
            continue

        provider_selected = ""
        # sort provider_names by priority
        provider_names = sort_options_by_priority(provider_names)

        # search for a functional provider
        for provider_option in provider_names:
            # link to test provider
            trial_link = providers_info[provider_option]
            sub_info, sub_link = get_subtitle_links(
                trial_link, desired_subs
            )
            if sub_info and sub_link:
                provider_selected = provider_option
                logger.info(
                    f"Selected {provider_selected} provider for anime {title}.")
                break

        if not provider_selected:
            # nothing to be done
            logger.warning(
                f"No available provider with subtitles for anime {title}. Skipping..."
            )
            continue

        processing = True
        page = 1

        while processing:
            logger.info(f"Parsing page {page}")
            page_links, has_entries = get_all_links_from_provider(
                provider_selected, page, link)
            data[title] += page_links
            processing = has_entries
            page += 1

        data[title] = filter_links_from_provider(
            data[title], provider_selected, episode_count)

    for anime_title, anime_info in data.items():
        all_subs_info = get_all_subtitles_info(
            anime_title, anime_info, desired_subs
        )
        data[anime_title] = all_subs_info

    return data

import requests
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from bs4.element import Tag
from .constants import MAIN_URL, REMOVE_REPACK
from .helpers import get_provider, convert_title_to_size, filter_subs
from base_logger import logger


def get_animes_finished_from_page(page: int = 1) -> List[Optional[Tag]]:
    url = MAIN_URL + f"?page={page}"
    finished_entries = []
    try:
        response = requests.get(url=url, timeout=60)
        data = response.text
        soup = BeautifulSoup(data, 'html.parser')
        for div in soup.find_all('div', class_='home_list_entry'):
            if '(finished)' in div.text:
                finished_entries.append(div)
        logger.info(f"Processed page {page} request.")

    except TimeoutError:
        logger.error(f"Timeout when during page {page} request.")

    return finished_entries


def get_batch_options_and_episode_count(title: str, link: str) \
        -> Tuple[Dict[str, str], List[str], int]:
    batch_options = {}
    url = link + REMOVE_REPACK
    res = requests.get(url, timeout=60)
    soup = BeautifulSoup(res.text, 'html.parser')

    # get all candidates
    parent_divs = soup.find_all("div", class_="home_list_entry")
    # the entry may not have any options, so we have to skip it
    current_choice = 0
    fonts_set = set()
    for candidate in parent_divs:
        # skip all batches
        is_batch = candidate.find("div", class_="links").find("em")
        if is_batch:
            continue

        # skip options > 16 GB
        size_str = candidate.find("div", class_="size").get("title")
        size_in_gb = convert_title_to_size(size_str)
        if size_in_gb > 16.0:
            continue

        batch_obj = candidate.find("div", class_="link").find("a")
        provider = get_provider(batch_obj.text)
        if not provider or provider in fonts_set:
            # just one example per provider is enough
            continue

        batch_options[provider] = batch_obj.get("href")
        fonts_set.add(provider)
        current_choice += 1
    # not a single option below 16gb for this anime
    if not current_choice:
        logger.warning(
            f"No available file below 16GB for anime {title}."
        )
    # get episode count
    episode_div = soup.select_one("table > tbody > tr > td > div > div")
    try:
        episode_count = episode_div.text.split(
            " episode(s)")[0].split(", ")[-1]
        logger.info(f"Got episode count of {episode_count}.")
    except Exception:
        episode_count = 0
        pass

    return batch_options, list(fonts_set), int(episode_count)


def get_subtitle_links(link: str) -> Optional[Tag]:
    target_row = ""
    # print(link)

    res = requests.get(url=link, timeout=60)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = soup.find("div", id="content")
    tables = content.find_all("table", recursive=False)
    for table in tables:
        # if last row has Subtitles as header, then page may have download links
        last_row = table.find_all("tr", recursive=False)[-1]
        if last_row.find("th").text == "Subtitles":
            target_row = last_row
            # print("Target Row:", target_row)
            break

    if not target_row:
        # no available subtitles
        return ""

    subs_links = target_row.find("td")
    return subs_links


def get_all_links_from_provider(provider: str, page: str, link: str) \
        -> List[Dict[str, str]]:
    episode_links = []
    url = link + REMOVE_REPACK + f"&page={page}"
    res = requests.get(url, timeout=60)
    soup = BeautifulSoup(res.text, 'html.parser')

    parent_divs = soup.find_all("div", class_="home_list_entry")
    if parent_divs:
        for candidate in parent_divs:
            # skip all batches
            is_batch = candidate.find("div", class_="links").find("em")
            if is_batch:
                continue

            # skip options > 16 GB
            size_str = candidate.find("div", class_="size").get("title")
            size_in_gb = convert_title_to_size(size_str)
            if size_in_gb > 16.0:
                continue

            curr_link = candidate.find("div", class_="link").find("a")
            if provider in curr_link.text:
                episode_links.append({
                    "link_title": curr_link.text,
                    "link_url": curr_link.get("href")
                })
    return episode_links


def parse_subtitles(subs: Optional[Tag]) -> Dict[str, str]:
    if not subs:
        return dict()

    subs_links = dict()
    attachments = subs.find_all("a")
    for sub in attachments:
        subs_links[sub.text] = sub.get("href")
    return subs_links


def get_all_subtitles_info(title: str, items: List[Dict[str, str]]) \
        -> List[Dict[str, str]]:

    final_object = []
    already_obtained_links = set()
    total_to_gather = len(items)
    logger.info("Preparing to gather subtitles links...")
    for idx, item in enumerate(items):
        sub_tag = get_subtitle_links(item["link_url"])
        sub_links_info = parse_subtitles(sub_tag)
        if ((idx+1) % 10) == 0 or (idx + 1) == total_to_gather:
            logger.info(f"[Progress|Total]: [{idx+1}|{total_to_gather}]")

        # filter for eng subs
        sub_link, sub_info = filter_subs(sub_links_info, title)
        if sub_link in already_obtained_links:
            continue

        item["sub_link"] = sub_link
        item["sub_info"] = sub_info
        final_object.append(item)
        already_obtained_links.add(sub_link)

    return items

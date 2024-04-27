import re
from typing import Dict, List, Tuple
# from ass.line import Dialogue
from bs4.element import Tag
from base_logger import logger
from .constants import (
    SEQUENCE_REGEX,
    QUALITY_REGEX,
    PREFERENCE_RAWS,
    DESIRED_SUBS,
)


def get_provider(text: str) -> str:
    # provider is at the end
    if text.find("]") == (len(text) - 1):
        return "[" + text.split("[")[-1]

    # provider is at the start
    elif text.find("[") == 0:
        return text.split("]")[0] + "]"

    # weird provider
    else:
        return ""


def extract_titles_and_anime_links(animes: List[Tag]) \
        -> Tuple[List[str], List[str]]:
    titles, links = [], []
    for entry in animes:
        link = entry.find('a').get('href')
        title = entry.find('strong').text
        links.append(link)
        titles.append(title)
    return titles, links


def convert_title_to_size(title: str) -> float:
    size_in_bytes = float(title.split(" ")[-2].replace(",", ""))
    size_in_gb = size_in_bytes / (1024 ** 3)
    return size_in_gb


def sort_options_by_priority(provider_names: List[str]) -> List[str]:
    provider_names += PREFERENCE_RAWS
    for pref in PREFERENCE_RAWS:
        provider_names.remove(pref)
    provider_names = provider_names[::-1]
    return provider_names


def filter_links_from_provider(
        entries: List[Dict[str, str]], batch_provider: str, ep_count: int) \
        -> List[Dict[str, str]]:
    # maybe return length of the list
    already_selected = []
    filtered_entries = []
    for entry in entries:
        title = entry["link_title"]
        quality_match = re.search(QUALITY_REGEX, title)
        sequence_match = re.search(SEQUENCE_REGEX, title)
        quality = quality_match.group(1) if quality_match else ""
        sequence = sequence_match.group(1) if sequence_match else ""
        cleaned_title = clean_title_string(
            title, quality, sequence, batch_provider)
        if cleaned_title in already_selected:
            continue

        already_selected.append(cleaned_title)
        filtered_entries.append(entry)

    if ep_count:
        excess = len(filtered_entries) - ep_count
        if excess:
            logger.info(
                f"Title has {excess} subs more than number of episodes.")

    logger.info(
        f"{len(filtered_entries)} subs remained after regex filtering.")
    return filtered_entries


def clean_title_string(
    title: str, quality: str, sequence: str, batch_provider: str
) -> str:
    # base cleaning
    title = title.replace(quality, "").replace(sequence, "")

    # try specific filter for current batch provider
    match batch_provider:
        case "[Erai-raws]":
            title = title.replace("[HEVC]", "")
            # needs more testing, may remove too much
            title = title.split("[Multiple Subtitle]")[0]
        case _:
            pass
    return title


def filter_subs(subs: Dict[str, str], title: str,
                target_lang: str = DESIRED_SUBS) -> Tuple[str, str]:
    target_sub, target_sub_info = "", ""
    for sub_info, sub_link in subs.items():
        if target_lang in sub_info:
            target_sub, target_sub_info = sub_link, sub_info
            break
    if not target_sub and len(subs) > 1:
        logger.info(f"Did not found {target_lang} subs for link {title}.")

    return target_sub, target_sub_info


def clean_ass_text(line: str) -> str:
    # remove breakline
    line = line.replace("\\N", "")

    # remove italics
    line = line.replace("{\\i0}", "").replace("{\\i1}", "")

    # dont know what {bg} means yet
    line = line.replace("{bg}", "")

    return line

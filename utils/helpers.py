import ass
import logging
import lzma
import re
import os
import pandas as pd
from typing import Dict, Literal, List, Tuple
# from ass.line import Dialogue
from bs4.element import Tag
from .constants import (
    SEQUENCE_REGEX,
    QUALITY_REGEX,
    PREFERENCE_RAWS,
    DESIRED_SUBS,
    FORMAT,
)

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    format=FORMAT,
    level=logging.INFO,
    handlers=[logging.StreamHandler()])


def get_provider(text: str) -> str:
    # provider is (probably) at the start
    provider = ""
    if text.find("[") == 0:
        possible_provider = text.split("]")[0] + "]"
        matched = re.search(SEQUENCE_REGEX, possible_provider)
        if not matched:
            # then we know it is the provider
            provider = possible_provider

    if text.find("(") == 0:
        # regex not needed here since torrent sequence do not appear inside ()
        provider = text.split(")")[0] + ")"

    # provider is (probably) at the end
    if text.find("]") == (len(text) - 1) and not provider:
        possible_provider = "[" + text.split("[")[-1]
        matched = re.search(SEQUENCE_REGEX, possible_provider)
        if not matched:
            provider = possible_provider

    if text.find(")") == (len(text) - 1) and not provider:
        provider = "(" + text.split(")")[-1]

    return provider


def extract_titles_and_anime_links(animes: List[Tag], filter_anime: str = "") \
        -> Tuple[List[str], List[str]]:
    titles, links = [], []
    filter_anime = format_title_for_filter(filter_anime)

    for entry in animes:
        link = entry.find('a').get('href')
        title = entry.find('strong').text
        title_for_comparison = format_title_for_filter(title)

        if filter_anime:
            if title_for_comparison == filter_anime:
                links.append(link)
                titles.append(title)
            continue

        links.append(link)
        titles.append(title)

    return titles, links


def format_title_for_filter(title: str) -> str:
    return title.replace(" ", "").lower()


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
                f"Title has {excess} subs compared to number of episodes.")

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
            title = title.replace("HEVC", "")
            # needs more testing, may remove too much
            title = title.split("[Multiple Subtitle]")[0]
        case _:
            pass
    return title


def filter_subs(
        link: str,
        subs: Dict[str, str],
        target_lang: str = DESIRED_SUBS
) -> Tuple[str, str]:
    sub_info, sub_link = "", ""

    for lang, link in subs.items():
        matched = re.search(
            target_lang, lang, re.IGNORECASE
        )
        link_type = link[-6:]
        correct_format = (link_type == "ass.xz")

        if matched and correct_format:
            # this one is good to go
            sub_info = lang
            sub_link = link
            break

    if not sub_info:
        logger.debug(f"Did not found {target_lang} subs for link {link}.")

    return sub_info, sub_link


def clean_ass_text(line: str) -> str:
    # remove breakline
    line = line.replace("\\N", "")

    # remove italics
    line = line.replace("{\\i0}", "").replace("{\\i1}", "")

    # dont know what {bg} means yet
    line = line.replace("{bg}", "")

    return line


def create_folders_for_anime(
        anime_name: str, logs: Literal["minimal", "debug"] = "minimal") -> bool:
    logger.info("Creating folders...")
    completed = True
    # check if data folder already exists
    if not os.path.exists('data'):
        try:
            os.mkdir('data')
            logger.info('General data folder created!')
        except Exception:
            logger.error('Error while creating general data folder.')
            completed = False
    else:
        logger.info('General data folder already exists!')

    anime = anime_name.replace(' ', '_')
    path = f'data/{anime}'
    # check if folder for specific anime already exists
    if not os.path.exists(path):
        try:
            os.mkdir(path)
            os.mkdir(path + '/raw')
            os.mkdir(path + '/processed')
            if logs == "debug":
                logger.info(f"Folder {path} created!")
        except Exception:
            logger.error(f'Error creating folder for {anime}')
            completed = False
    else:
        logger.info(f'Folder for anime {anime} already exists!')
    logger.info(f"Finished creating folders for anime {anime_name}.")

    return completed


def generate_ass_files(filter_anime: str = "") -> List[str]:
    created = []
    filter_anime = filter_anime.replace(" ", "_")
    animes = os.listdir('data')
    for anime in animes:
        # for testing purposes
        if filter_anime and anime.lower() != filter_anime.lower():
            continue

        logger.info(f'Generating .ass files for anime: {anime}')
        folder_path = 'data/' + anime + '/raw'
        episodes = os.listdir(folder_path)
        success = 0
        fails = 0

        for idx, episode in enumerate(episodes):
            path = folder_path + '/' + episode
            # read .xz file
            try:
                with lzma.open(path, mode='rb') as file:
                    content = file.read()

                # removing .xz
                path = path[:-3]
                # we want to save .ass files into processed folder, not raw
                path = path.replace('raw', 'processed')

                with open(path + '.ass', 'wb') as file:  # write content into .ass file
                    file.write(content)
                    success += 1
            except Exception:
                continue
            # just to know that script is running
            if ((idx + 1) % 10) == 0 or (idx + 1) == len(episodes):
                logger.info(f"[Progress|Total]: [{idx+1}|{len(episodes)}]")

        if success > 0:
            created.append(anime)
            logger.info(
                f'Successfully created {success} .ass files for anime {anime}!')
        if fails > 0:
            logger.warning(
                f"Failed to create {fails} .ass files for anime {anime}.")
    return created


def build_df_from_ass_files(
    anime_name: str = "", logs: Literal["minimal", "debug"] = "minimal") \
        -> pd.DataFrame:
    # this will not be viable for anime with large number of episodes
    # since dataframe will have lots of rows, thus running out of memory
    # let's change to chunks later
    no_character_name = 0
    folder_path = 'data/' + anime_name.replace(" ", "_") + '/processed'
    # list of every .ass file in anime folder
    episodes = os.listdir(folder_path)
    table = []
    for episode in episodes:  # iterate over every episode
        path = folder_path + '/' + episode
        # get episode number (episode title is always anime_name_{episode_num}.ass)
        episode_number = episode.split('.')[0].split('_')[-1]
        try:
            with open(path, encoding='utf_8_sig') as f:
                doc = ass.parse(f)  # read .ass file
                events = doc.events  # get every dialogue line
                if logs == "debug":
                    logger.debug(f'Reading {path.split("/")[-1]}...')
                for event in events:
                    # we do not care about signs
                    if event.style.lower() == "signs" or \
                            event.name.lower() == "sign":
                        continue
                    # we will probably not have the character names
                    elif not event.name:
                        event.name = "Unknown"
                        no_character_name += 1
                    # save every line with whoever said the line
                    cleaned_text = clean_ass_text(event.text)
                    table.append(
                        [episode_number, event.name, cleaned_text])
        except Exception:
            logger.info(f'Error reading {path.split("/")[-1]}.')
    df = pd.DataFrame(
        table, columns=['Episode', 'Name', 'Quote'])
    df = df.astype({'Episode': 'int32'})
    logger.info(
        f"{len(df) - no_character_name}/{len(df)} quotes with character name.")

    return df

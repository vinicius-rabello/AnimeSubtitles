import ass
import json
import logging
import lzma
import re
import os
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
# from ass.line import Dialogue
from bs4.element import Tag
from .constants import (
    SEQUENCE_REGEX,
    QUALITY_REGEX,
    EPISODE_REGEX,
    SEASON_REGEX,
    REMOVE_DELIMITERS_REGEX,
    PREFERENCE_RAWS,
    DESIRED_SUBS,
    FORMAT,
    PATH_ID_MEMBER_MAP,
    NOT_ALLOWED_CHARACTERS
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
    # CURRENTLY IGNORING PROVIDERS AT THE END
    # if text.find("]") == (len(text) - 1) and not provider:
    #     possible_provider = "[" + text.split("[")[-1]
    #     matched = re.search(SEQUENCE_REGEX, possible_provider)
    #     if not matched:
    #         provider = possible_provider

    # if text.find(")") == (len(text) - 1) and not provider:
    #     provider = "(" + text.split(")")[-1]

    return provider


def extract_titles_and_anime_links(
    animes: List[Tag],
    filter_anime: str = "",
    filter_link: str = "") \
        -> Tuple[List[str], List[str]]:
    # only bad case is providing both, so true and true
    invalid = filter_anime and filter_link
    if invalid:
        raise ValueError(
            "You can filter for either anime or link or neither, but not both."
        )
    titles, links = [], []
    filter_anime = format_title_for_filter(filter_anime)

    for entry in animes:
        link = entry.find('a').get('href')
        title = entry.find('strong').text
        title_for_comparison = format_title_for_filter(title)

        if filter_anime:
            # if we are filtering for a specific entry, skip the rest
            # TODO: Better logic here (regex?)
            if filter_anime in title_for_comparison:
                links.append(link)
                titles.append(title)
                break
            continue

        elif filter_link:
            if filter_link == link:
                links.append(link)
                titles.append(title)
                break
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
    # base cleaning (remove quality and torrent sequence)
    title = title.replace(quality, "").replace(sequence, "")
    # hevc changes nothing subtitle-wise
    title = title.replace("[HEVC]", "").replace(" HEVC", "")

    # try specific filter for current batch provider
    match batch_provider:
        case "[Erai-raws]":
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


def create_data_folder() -> None:
    # check if data folder already exists
    if not os.path.exists('data'):
        try:
            os.mkdir('data')
            logger.info('General data folder created!')
        except Exception:
            logger.error(
                'Error while creating general data folder. Cannot procede.')
            raise RuntimeError

    return


def create_folders_for_anime(
    anime_name: str,
    # logs: Literal["minimal", "debug"] = "minimal"
) -> bool:
    logger.info("Trying to create necessary folders...")
    completed = True

    anime = anime_name.replace(' ', '_').replace(":", "_")
    path = f'data/{anime}'
    # check if folder for specific anime already exists
    if not os.path.exists(path):
        try:
            os.mkdir(path)
            os.mkdir(path + '/raw')
            os.mkdir(path + '/processed')
            logger.debug(f"Folder {path} created!")
        except Exception:
            # log on the parent function
            completed = False

    if completed:
        logger.info(
            f"Successfully created folders for anime {anime_name}.")

    return completed


def generate_ass_files(filter_anime: str = "") -> List[str]:
    created = []
    filter_anime = filter_anime.replace(" ", "_")
    animes = os.listdir('data')
    if filter_anime:
        logger.info(f"Searching only for anime {filter_anime}.")
    for anime in animes:
        # for testing purposes
        if filter_anime and anime.lower() != filter_anime.lower():
            logger.info(f"Anime {anime} ignore due to filtering.")
            continue

        logger.info(f'Generating .ass files for anime: {anime}')
        folder_path = 'data/' + anime + '/raw'
        episodes = os.listdir(folder_path)
        success = 0
        fails = 0

        # check if already generated all .ass for this entry
        proc_path = folder_path.replace("raw", "processed")
        if os.path.exists(proc_path):
            if len(os.listdir(proc_path)) >= len(episodes):
                logger.info(f"Already generated .ass files for {anime}.")
                continue

        # TODO: make this better (having full name here is useless)
        for idx, episode in enumerate(episodes):
            path = folder_path + '/' + episode
            # read .xz file
            try:
                with lzma.open(path, mode='rb') as file:
                    content = file.read()

                # removing .xz
                path = path[:-3]
                # we want to save .ass files into processed folder, not raw
                # TODO: can be problematic if anime name contains "raw"
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


def process_episode_data(path: str, episode: int) -> Tuple[List[List[str]], int]:
    data = []
    no_character_name = 0

    with open(path, encoding='utf_8_sig') as f:
        doc = ass.parse(f)
        # get every dialogue line
        events = doc.events
        logger.debug(f'Reading {path.split("/")[-1]}...')
        for event in events:
            # we do not care about signs
            if event.style.lower() in "signs" or \
                    event.name.lower() == "sign":
                continue

            # we will probably not have the character names
            elif not event.name:
                event.name = "Unknown"
                no_character_name += 1

            # save every line with whoever said the line
            cleaned_text = clean_ass_text(event.text)

            data.append([episode, event.name, cleaned_text])

    return data, no_character_name


def build_df_from_ass_files(
    anime_name: str = ""
) -> pd.DataFrame:
    # this will not be viable for anime with large number of episodes
    # since dataframe will have lots of rows, thus running out of memory
    # let's change to chunks later
    no_character_name = 0
    folder_path = 'data/' + anime_name + '/processed'
    # list of every .ass file in anime folder
    episodes = os.listdir(folder_path)
    table = []
    for episode in episodes:  # iterate over every episode
        path = folder_path + '/' + episode
        # get episode number (episode title is always anime_name_{episode_num}.ass)
        episode_number = episode.split('.')[-2].split('_')[-1]
        try:
            episode_data, no_character = process_episode_data(
                path, episode_number)
            table += episode_data
            no_character_name += no_character
        except Exception:
            logger.info(f'Error reading {path.split("/")[-1]}.')

    df = pd.DataFrame(
        table, columns=['Episode', 'Name', 'Quote'])
    df = df.astype({'Episode': 'float32'})
    logger.info(
        f"{len(df) - no_character_name}/{len(df)} quotes with character name.")

    return df


def get_mal_id(div: Optional[Tag], title: str) -> int:
    mal_div = div[-1] if div else None

    if mal_div is None:
        return 0

    # getting id via url
    try:
        mal_id = mal_div.find("a", string="MAL").get(
            "href").split("/")[-1]
    except Exception as e:
        logger.warning(f"Failed to get MAL id for anime {title}")
        logger.debug(str(e))
        mal_id = 0

    return int(mal_id)


def process_data_input(file_path: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(file_path, (str, dict)):
        logger.error(f"Object provided is of type {type(file_path)}. Expected"
                     f" either str or dict.")
        raise TypeError

    # we accept either a path for the json or the actual json
    elif isinstance(file_path, str):
        try:
            f = open(file_path)
            data = json.load(f)
        except Exception:
            data = {}
        finally:
            f.close()

    return data


def check_for_id(mal_id: int, members_cut: int) -> bool:
    file = PATH_ID_MEMBER_MAP
    data = ""
    with open(file, "r+", encoding="utf-8") as f:
        data = json.load(f)
    members = data.get(str(mal_id), 0)
    return int(members) > members_cut


def remove_text_inside_delimiters(input_string: str) -> str:
    # remove text inside de parenthesis or brackets
    cleaned_string = re.sub(REMOVE_DELIMITERS_REGEX, '', input_string)
    # clean extra spaces
    return re.sub(r'\s{2,}', ' ', cleaned_string)


def find_episode_number(input_string: str) -> str:
    # this method for episode seems to work fine for most cases
    if not input_string:
        return ""

    text = remove_text_inside_delimiters(input_string)
    # match any sequence of 2 to 4 numbers followed by space
    regex = EPISODE_REGEX
    matches = re.finditer(regex, text)
    results = [(match.group(), match.start()) for match in matches]
    number = ""
    for res in results:
        if text[res[1] - 1] in NOT_ALLOWED_CHARACTERS:
            # the number is probably not an episode number
            continue
        else:
            number = res[0]
            break

    # should not happen, but just to make sure
    if "." in number:
        # .5 episodes, ignore
        number = ""

    return number


def find_season(input_string: str, provider: str) -> str:
    if not input_string:
        return ""
    # try most common first. If not found, try more specifics
    # first we try "SXYE", where X, Y are 0-9. Ex: "S01E10" should match
    regex = SEASON_REGEX
    match = re.search(regex, input_string)
    if match:
        return match.group(1)

    # try same logic, but without need to have "E" after number
    # "S3 bla bla" should match now
    regex = r'S([0-9]{1,2})'
    match = re.search(regex, input_string)
    if match:
        return match.group(1)

    # the whole above logic can be one for loop, but this is better to explain

    # try specifics for famous providers
    match provider:
        case "[Erai-raws]":
            # try searching for word season
            res = list(map(lambda x: x.lower(), input_string.split(" ")))
            if "season" in res:
                return res[res.index("season") + 1]
        case _:
            # can expand
            return ""
    # no luck
    return ""

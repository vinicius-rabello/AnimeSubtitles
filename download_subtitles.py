import json
import os
import requests

# this file downloads subtitles from every link on a .json file generated by main.py

# opening JSON file
f = open('examples/bocchi_the_rock.json')
data = json.load(f)

animes = data.keys()  # list of animes in json file
print(animes)

# creating data folder


def create_folders(animes):

    if not os.path.exists('data'):  # check if data folder already exists
        try:
            os.mkdir('data')
            print('Data folder created!')
        except Exception:
            print('Error creating data folder.')
    else:
        print('Data folder already exists!')

    for anime in animes:
        anime = anime.replace(' ', '_')
        path = f'data/{anime}'
        # check if folder for specific anime already exists
        if not os.path.exists(path):
            try:
                os.mkdir(path)
                os.mkdir(path+'/raw')
                os.mkdir(path+'/processed')
                print(f"Folder {path} created!")
            except Exception:
                print(f'Error creating folder for {anime}')
        else:
            print(f'Folder for {anime} already exists!')


def download_subtitles(animes):

    for anime in animes:  # iterate over every anime on .json file

        episodes = data[anime]  # list of episodes

        anime = anime.replace(' ', '_')
        folder_path = f'data/{anime}/raw'

        for i, episode in enumerate(episodes):

            filename = anime + f'_{i+1}.xz'
            link = episode['sub_link']  # get link from json file
            # a = os.listdir(folder_path)

            # check if file is already downloaded
            if filename not in os.listdir(folder_path):
                response = requests.get(link)
                # path like data/anime_name/anime_name_episode_number
                file_path = os.path.join(folder_path, filename)
                if response.status_code == 200:  # if request is successful proceed
                    with open(file_path, 'wb') as file:
                        # write response object to file
                        file.write(response.content)
                        print(f'{filename} downloaded successfully.')
                else:
                    print(
                        f'Failed to download {filename}. Status code:', response.status_code)
            else:
                print(f'{filename} is already downloaded')
                continue


create_folders(animes)
download_subtitles(animes)

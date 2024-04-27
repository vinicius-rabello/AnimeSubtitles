import lzma
import os

animes = os.listdir('data')  # get every anime folder
for anime in animes:

    print(f'\nExcracting subtitles from {anime}\n')

    folder_path = 'data/'+anime+'/raw'
    episodes = os.listdir(folder_path)

    for episode in episodes:  # iterate over every file in anime folder

        path = folder_path + '/' + episode

        with lzma.open(path, mode='rb') as file:  # read .xz file
            content = file.read()

        path = path[:-3]
        # we want to save .txt files into processed folder, not raw
        path = path.replace('raw', 'processed')

        with open(path+'.ass', 'wb') as file:  # write content into .txt file
            file.write(content)
            print(f'{path}.ass successfuly created!')

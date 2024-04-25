import os
import pandas as pd
import ass

animes=os.listdir('data') # get every anime folder
for anime in animes: # iterate over every anime in data folder
    folder_path='data/'+anime+'/processed' 
    episodes=os.listdir(folder_path) # list of every .ass file in anime folder
    
    if f'{anime}.xlsx' in os.listdir(f'data/{anime}'):
        print(f'{anime}.xlsx already exists!' )
        continue

    table=[]
    for episode in episodes: # iterate over every episode
        path=folder_path+'/'+episode
        episode_number=episode.split('.')[0].split('_')[-1] # get episode number (episode title is always anime_name_{episode_num}.ass)

        try:
            with open(path, encoding='utf_8_sig') as f:
                doc = ass.parse(f) # read .ass file
                events=doc.events # get every dialogue line
                print(f'reading {path}')
                for event in events:
                    table.append([episode_number,event.name,event.text]) # save every line with whoever said the line 
                                                                        # and the episode number 
        except:
            print(f'error reading {path}')
                                                            
    df=pd.DataFrame(table,columns=['episode_number','name','text'])
    df.to_excel(f'data/{anime}/{anime}.xlsx',index=False)
    print(f'{anime}.xlsx created successfuly!')
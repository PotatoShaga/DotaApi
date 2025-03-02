import sqlite3
import json
import requests
import pandas as pd
from DotaApi import api_handler

pd.set_option("display.max_columns", None)


def grab_steam_ids(df_raw):
    columnlabels=["ID1","WR1","ID2","WR2","ID3","WR3","ID4","WR4","ID5","WR5","ID6","WR6","ID7","WR7","ID8","WR8","ID9","WR9","ID10","WR10"]
    df_winrate = pd.DataFrame(columns=columnlabels)

    for indices, match_id in enumerate(df_raw["id"].unique()): 
        for label in columnlabels[0::2]:
            positionnumber = int(label[2:]) # gets everything except last 2 chars (so will get 1 and 10 fine)
            isOnMyTeam = True
            if positionnumber > 5:
                isOnMyTeam = False
                positionnumber = positionnumber - 5 # pos6 should actually be enemy pos1
            steam_id = df_raw.loc[(df_raw["position"] == f"POSITION_{positionnumber}") & (df_raw["isOnMyTeam"] ==  isOnMyTeam) & (df_raw["id"] == match_id), "steamAccountId"].values[0]
            #print(indices,label,positionnumber,isOnMyTeam)
            df_winrate.loc[indices,label]= steam_id

    return df_winrate

def grab_winrates(df_winrate, oldest_match_id, number_of_matches):
    response_json_batch = winrate_query(df_winrate, oldest_match_id, number_of_matches)
    for index, batch in enumerate(response_json_batch): # each batch should be the winlosses of 10 players for a match id
        df_isVictory_placeholder = pd.DataFrame([ #this placeholder df contains rows of key ("WR_x") and the bool of isVictory, its in long format
        {"key": key, "isVictory": match["players"][0]["isVictory"]}
        for key, value in batch.items()
        for match in value["matches"]])
        #print(df_isVictory_placeholder)
        #print(oldest_match_id)
        winrates = df_isVictory_placeholder.groupby("key")["isVictory"].mean()
        for col in winrates.keys():
            df_winrate.loc[index, col] = winrates[col]
    # DO THE CALCULATIONS HERE TO GRAB WINRATE FROM THE QUERY. aliases are even identical to where in df_winrate it'll be inserted!! but currently this is assuming a "skip" of 10 per query (so no doing 20 players per query right now)
    pass

def winrate_query(df_winrate, oldest_match_id, number_of_matches):
    response_json_batch = []
    for i in df_winrate.index:
        steamAccountIdList = []
        steamAccountIdList += [df_winrate.iloc[i][f"ID{j}"] for j in range(1,11)] # adds all 10 steamids to their respective jID
        # Problem: boilerplate query can only have take of 100, unless I want to implement skips. probably just leave it at 100 
        # Bigger problem: this only takes matches past your oldest match. what if you played 2 games back to back and want to complain? take can be 100, but for side characters only like 1-3 games will appear. does not capture adequete depth when your match_id bracket is small
        # Solution: arbitrarily increase bracket size by subtracting oldest_match_id -= 100,000 or something? 
        boilerplate_querys = [f"""WR{pos+1}: player(steamAccountId:{steamid}) {{
                                matches(request: {{
                                    isParsed: true, lobbyTypeIds:7
                                    positionIds: POSITION_{pos+1 if pos<5 else pos-5+1}
                                    take: {100} 
                                    after: {oldest_match_id}
                                    playerList: SINGLE
                                }} ) {{
                                    players {{
                                        isVictory
                                    }}
                                }}
            }}
        """for pos,steamid in enumerate(steamAccountIdList)] #pos is index, and since order of storing is pos1-10, index can be used to get pos

        query = f"""{{
            {' '.join(boilerplate_querys)}
        }}
        """

        response = api_handler.intializes_call(query) #response consists of json and header
        response_json = response.json()
        response_json = response_json["data"]
        response_json_batch.append(response_json)

    return response_json_batch

def convert_df_to_dict(df_winrate):
    keylist = ["WR1", "WR2", "WR3", "WR4", "WR5", "WR6", "WR7", "WR8", "WR9", "WR10"]
    winrate_dict = {(key[2:]):round(df_winrate.mean()[key],5) for key in keylist} # key is pos, value is winrate of that pos
    return winrate_dict

def create_df_winrate(df_raw):

    oldest_match_id = df_raw.iloc[-1]["id"]
    oldest_match_id -= 1
    number_of_matches = df_raw.shape[0]/10
    
    print(f"oldest match id is {oldest_match_id+1}")

    df_winrate = grab_steam_ids(df_raw) # adds steam_ids into df_winrate
    grab_winrates(df_winrate, oldest_match_id, number_of_matches) #adds winrates into df_winrate
    winrate_dict = convert_df_to_dict(df_winrate)
    #print(df_winrate)
    #print(winrate_dict)
    
    return winrate_dict

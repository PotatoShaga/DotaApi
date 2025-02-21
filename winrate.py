import sqlite3
import json
import requests
import pandas as pd
from DotaApi import api_handler

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 0)  # THIS ALLOWS ALL COLUMNS TO BE DISPLAYED, WITHOUT COLUMNS WILL BE "/" AND NEW LINED


def grab_steam_ids(df_raw):
    columnlabels=["1ID","1WR","2ID","2WR","3ID","3WR","4ID","4WR","5ID","5WR","6ID","6WR","7ID","7WR","8ID","8WR","9ID","9WR","10ID","10WR"]
    df_winrate = pd.DataFrame(columns=columnlabels)

    for indices, match_id in enumerate(df_raw["id"].unique()): #agnostically gets raw data for everyone (except in winrate). more specific specification happens in player_calculations
        for label in columnlabels[0::2]:
            positionnumber = int(label[:-2]) # gets everything except last 2 chars (so will get 1 and 10 fine)
            isOnMyTeam = True
            if positionnumber > 5:
                isOnMyTeam = False
                positionnumber = positionnumber - 5 # pos6 should actually be enemy pos1
            steam_id = df_raw.loc[(df_raw["position"] == f"POSITION_{positionnumber}") & (df_raw["isOnMyTeam"] ==  isOnMyTeam) & (df_raw["id"] == match_id), "steamAccountId"].values[0]
            #print(indices,label,positionnumber,isOnMyTeam)
            df_winrate.loc[indices,label]= steam_id

    print(df_winrate)
    return df_winrate

def grab_winrates(df_winrate):
    winrate_query(df_winrate)
    pass

def winrate_query(df_winrate):
    for i in df_winrate.index:
        steamAccountIdList = []
        steamAccountIdList += [df_winrate.iloc[i][f"{j}ID"] for j in range(1,11)] # adds all 10 steamids to their respective jID

        print(steamAccountIdList)

        boilerplate_query = [f"""{{steamAccountId_{steamid}

        }}
        """for pos,steamid in enumerate(steamAccountIdList)]

        query = f"""{{
        {boilerplate_query}
        }}
        """

def create_df_winrate(df_raw):

    oldest_match_id = df_raw.iloc[-1]["id"]
    print(oldest_match_id)

    df_winrate = grab_steam_ids(df_raw)

    grab_winrates(df_winrate)

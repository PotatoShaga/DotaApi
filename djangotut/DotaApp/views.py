
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, FileResponse
from django.template import loader
from DotaApi import script
import os
import pandas as pd

import sys
sys.path.append('../') 

def index(request): #gets request from urls which send data to index, which currently is root url, which index.html sends to

    if request.method == "GET":
        print("Request GET data:", request.GET)

        steam_id = request.GET.get("steam_id")
        position = request.GET.get("position")
        #isOnMyTeam = request.GET.get("isOnMyTeam") #simplifying options, these have little functionality right now anyways
        isOnMyTeam = True
        minute = request.GET.get("minute") 
        #skip_interval = request.GET.get("skip_interval")
        skip_interval = 100
        num_matches = request.GET.get("num_matches")

    player_dict_list = None
    parameters_dict = None
    if num_matches:
        steam_id = int(steam_id) #entire code breaks if input is not as int, as it cannot comprehend a string input!
        position = f"POSITION_{position}"
        isOnMyTeam = bool(isOnMyTeam)
        minute = int(minute)+1 # +1 so input 10 turns to 11, and minute=11 is exactly 10:01
        skip_interval = int(skip_interval)
        num_matches = int(num_matches)
        
        player_dict_list = []
        player_name_list = ["AllyPos1", "AllyPos2", "AllyPos3", "AllyPos4", "AllyPos5", "EnemyPos1", "EnemyPos2", "EnemyPos3", "EnemyPos4", "EnemyPos5"]
        df_player_calculations, parameters_dict = script.main_script(steam_id, position, isOnMyTeam, minute, skip_interval, num_matches)

        for index in range(1,11):
            player_name = player_name_list[index-1]
            if (index) == int(position[9:]):
                player_name = "You"
                
            player_dict  = {
                "Name": player_name,
                "lastHitsAverage": float(round(df_player_calculations["lastHitsAverage"].iloc[index-1],5)),
                "deniesAverage": float(round(df_player_calculations["deniesAverage"].iloc[index-1],5)),
                "levelAverage": float(round(df_player_calculations["levelAverage"].iloc[index-1],5)),
                "kdaAverage": df_player_calculations["kdaAverage"].iloc[index-1],
                "winrate": float(round(df_player_calculations["winrate"].iloc[index-1],5)*100),
            }
            player_dict_list.append(player_dict)
        print(parameters_dict)
        print(player_dict_list)

    return render(request, "index.html", {"players":player_dict_list, "parameters":parameters_dict})

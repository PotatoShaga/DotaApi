from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, FileResponse
from django.template import loader
from DotaApi import script
import os

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

        download = request.GET.get("download")

    file_path = None
    if "file_path" in request.session:
        file_path = request.session["file_path"]

    if steam_id:
        steam_id = int(steam_id) #entire code breaks if input is not as int, as it cannot comprehend a string input!
        position = f"POSITION_{position}"
        isOnMyTeam = bool(isOnMyTeam)
        minute = int(minute)+1 # +1 so input 10 turns to 11, and minute=11 is exactly 10:01
        skip_interval = int(skip_interval)
        num_matches = int(num_matches)
        
        file_path = script.main_script(steam_id, position, isOnMyTeam, minute, skip_interval, num_matches) # runs entire script here
        request.session["file_path"] = file_path

    if download and file_path:
        print("Download Complete!")
        return FileResponse(open(file_path, "rb"), as_attachment=True, filename=os.path.basename(file_path))

    return render(request, "index.html", {"excelsheet":file_path})
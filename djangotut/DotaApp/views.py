from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, FileResponse
from django.template import loader
from DotaApi.test import testfunction
from DotaApi import script
import os

from .models import Question

import sys
sys.path.append('../') 
#405788540

"""
def index(request):
    latest_question_list = Question.objects.order_by("-pub_date")[:5]
    #output = ",".join(q.question_text for q in latest_question_list)
    template = loader.get_template("DotaApp/index.html")
    context = {
        "latest_question_list": latest_question_list,
    }
    return HttpResponse(template.render(context, request))
"""


def index(request): #gets request from urls which send data to index, which currently is root url, which index.html sends to
    if request.method == "GET":
        print("Request GET data:", request.GET)

        steam_id = request.GET.get("steam_id")
        position = request.GET.get("position")
        isOnMyTeam = request.GET.get("isOnMyTeam")
        minute = request.GET.get("minute")
        skip_interval = request.GET.get("skip_interval")
        num_matches = request.GET.get("num_matches")

        download = request.GET.get("download")

    file_path = None
    if "file_path" in request.session:
        file_path = request.session["file_path"]

    if steam_id:
        steam_id = int(steam_id) #entire code breaks if input is not as int, as it cannot comprehend a string input!
        position = f"POSITION_{position}"
        isOnMyTeam = bool(isOnMyTeam)
        minute = int(minute)
        skip_interval = int(skip_interval)
        num_matches = int(num_matches)
        
        file_path = script.main_script(steam_id, position, isOnMyTeam, minute, skip_interval, num_matches)
        request.session["file_path"] = file_path

    if download and file_path:
        print("Download Complete!")
        return FileResponse(open(file_path, "rb"), as_attachment=True, filename=os.path.basename(file_path))

    return render(request, "index.html", {"excelsheet":file_path})
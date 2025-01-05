from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from DotaApi.test import testfunction
#from DotaApi.script import script
from DotaApi import script

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

    response = "last return"
    if steam_id:
        response = script.main_script(steam_id)

    return render(request, "index.html", {"excelsheet":response})#e
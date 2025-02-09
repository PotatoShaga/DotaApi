import requests
import pandas as pd
import time
import sys
import os
from dotenv import load_dotenv

load_dotenv()


#This file should take return a bunch of print statements (skip/take, if rate limiters catch error, time for query..) and ONE list (batch) of all the data. Input parameters should be specified in the script.py file

pd.options.display.max_columns = None

Api_Stratz_Url = "https://api.stratz.com/graphql"
token = os.getenv("TOKEN")

Headers = {
    "content-type": "application/json",
    "Authorization": f"Bearer {token}",
    "User-Agent": "STRATZ_API",
}




def intializes_call(query):
    query_start_time = time.time()
    response = requests.post(Api_Stratz_Url, json={"query":query}, headers = Headers)
    query_end_time = time.time()
    time_for_api_query = query_end_time - query_start_time
    print(f"time for api query was {time_for_api_query}") 
    if response.status_code == 200: #catches errors and ratelimits calculations
        rate_limiter(response)
        return (response)
    else:
        raise Exception(f"SOMETHING WENT WRONG: status code is {response.status_code} and text returned is {response.text}")


def rate_limiter(response):
    response_headers = response.headers #response.headers give the full info
    if int(response_headers["ratelimit-reset"]) == 0:
        print(f"RATELIMIT-RESET == 0")
        time.sleep(1)
    if int(response_headers["x-ratelimit-remaining-second"]) <= 1:
        print(f"RATELIMIT REMAINING PER SECOND  <= 1 (out of {response_headers["x-ratelimit-limit-second"]}/s), SLEEPING FOR 1 S")
        time.sleep(1)
    if int(response_headers["x-ratelimit-remaining-minute"]) <= 1:
        print(f"RATELIMIT REMAINING PER MINUTE  <= 1 (out of {response_headers["x-ratelimit-limit-minute"]}/s), SLEEPING FOR 60 S")
        time.sleep(60)
    if int(response_headers["x-ratelimit-remaining-hour"]) <= 50:
        print(f"RATELIMIT REMAINING PER HOUR  <= 50 (out of {response_headers["x-ratelimit-limit-hour"]}/s), EXITING")
        sys.exit()
    if int(response_headers["x-ratelimit-remaining-day"]) <= 800:
        print(f"RATELIMIT REMAINING PER HOUR  <= 800 (out of {response_headers["x-ratelimit-limit-day"]}/s), EXITING")
        sys.exit()

#matchIds: [7929996674,7900186009] add this to request: to test on specific matches, just include as a list


def query_call(take,skips,steam_id,position):
#double {{ is to allow using { for f string, print({{steam_id}}) results in {steam_id}; curly brackets for graphQL syntax preserved
    query = f"""{{
    player(steamAccountId:{steam_id}){{
        matches(request: {{
        isParsed: true, lobbyTypeIds: 7
        positionIds: {position}
        take: {take}
        skip: {skips}

        }}) {{
        id
        players {{
            steamAccountId
            isRadiant
            isVictory
            position
            heroId
            playbackData {{
                playerUpdateLevelEvents {{
                    time
                    level
                }}
                killEvents {{
                time
                }}
                deathEvents {{
                time
                }}
            }}
            stats {{
                networthPerMinute
                lastHitsPerMinute
                deniesPerMinute
            }}

        }}
        }}
    }}
    }}
    """

    response = intializes_call(query) #response consists of json and header
    response_json = response.json()
    response_json = response_json["data"]["player"]["matches"]
    return (response_json)


def skip_calculator(number_of_matches_to_parse,skip_interval): 
    if number_of_matches_to_parse <= skip_interval:
        take = number_of_matches_to_parse
        skips = [0]
    else:
        take = skip_interval
        skips = []
        intervals = number_of_matches_to_parse / skip_interval
        for x in range(int(intervals)):
            skips.append(x*skip_interval)
    return (take, skips)


def queries_to_batches_main(steam_id, position="POSITION_1", skip_interval=10, number_of_matches_to_parse=1):
    responses = []
    responses_batch = []
    take, skips = skip_calculator(number_of_matches_to_parse,skip_interval)
    ###print(f"SKIP INTERVAL IS {take}, SKIP INCREMENTS ARE {skips}")
    for skip in skips: #does the querying each time for skip

        try:
            query_data = query_call(take,skip,steam_id,position) #gets the query_data and time_taken as a tuple
            responses_batch.append(query_data)
            print(f"Current Increment: {skip}")
        except Exception as error:
            ###print("API GAVE UP")
            ###print(f"Error:{error}")
            ####print(f"Current Increment: {skip}")
            pass

    for batch in responses_batch:
        responses.extend(batch)
    df_raw = pd.json_normalize(responses,"players",["id"])

    return df_raw

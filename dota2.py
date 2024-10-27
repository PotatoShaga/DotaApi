import requests
import numpy as np
import pandas as pd
import openpyxl
import time
import sys

#GOAL: START SIMPLE. SIMPLY PULL AVERAGE DATA FROM MY PROFILE.
# MAYBE CALCULATE MY LANING SKILL ISSUE, GOLD AT 10MIN AND STOP BLAMING TEAM


Api_Stratz_Url = "https://api.stratz.com/graphql"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiZmRmNjcwYjEtYThhOS00NjM1LTk0ZjktZjBmYTVjZDkzZjU5IiwiU3RlYW1JZCI6IjQwNTc4ODU0MCIsIm5iZiI6MTcwMDM2ODc1NCwiZXhwIjoxNzMxOTA0NzU0LCJpYXQiOjE3MDAzNjg3NTQsImlzcyI6Imh0dHBzOi8vYXBpLnN0cmF0ei5jb20ifQ.RRtK4zwNqnp7EPda-BkBNI08hAlAw5OqqbY9RrzkFNs"

Headers = {
    "content-type": "application/json",
    "Authorization": f"Bearer {token}",
    "User-Agent": "STRATZ_API",
}
def stratz_query(query):
    query_start_time = time.time()
    response = requests.post(Api_Stratz_Url, json={"query":query}, headers = Headers)
    query_end_time = time.time()
    time_for_api_query = query_end_time - query_start_time
    print(f"time for api query was {time_for_api_query}")
    print(response.headers)
    if response.status_code == 200: #catches errors and ratelimits calculations
        rate_limiter(response)
        return (response)
    else:
        raise Exception(f"SOMETHING WENT WRONG: status code is {response.status_code} and text returned is {response.text}")

def rate_limiter(response):
    response_headers = response.headers
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

def query_matches(take,skips,steam_id,position):
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
            playerSlot
            playbackData {{
                playerUpdateLevelEvents {{
                    time
                    level
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

    response = stratz_query(query) #response consists of json and header
    response_json = response.json()
    response_json = response_json["data"]["player"]["matches"]
    return (response_json)


def adding_columns(df_raw,steam_id,minute):
    important_raw_columns = ["id","playerSlot","position","heroId"]
    df_calculated = df_raw[important_raw_columns].copy()
    df_calculated["networthDifference"] = 0

    for match_id in df_raw["id"].unique():
        
        def is_on_my_team_column(df_raw,match_id,steam_id): #for some reason these parameters arent needed inside this adding_columns function? like code works perfectly fine if u delete the parameters, ig cus parameters already gotten
            radiant = df_raw.loc[(df_raw["steamAccountId"]==steam_id) & (df_raw["id"]==match_id),"isRadiant"].values[0]
            if radiant == True:
                df_raw.loc[df_raw["id"] == match_id,"isOnMyTeam"] = df_raw["isRadiant"]
            else:
                df_raw.loc[df_raw["id"] == match_id,"isOnMyTeam"] = ~df_raw["isRadiant"]

        is_on_my_team_column(df_raw,match_id,steam_id)

        #first df is df_raw, second df is df_calculated 
        def networth_difference_column(df_raw,df_calculated,match_id,minute): #for each position, finds the difference of MyPosNW - TheirPosNW and then adds it the column in the order of pos1,pos2,po3,pos4,pos5. Will ALWAYS be perspective of ally - enemy.
            position_ally = ["POSITION_1","POSITION_2","POSITION_3","POSITION_4","POSITION_5",        "POSITION_1","POSITION_2","POSITION_3","POSITION_4","POSITION_5"]
            position_enemy = ["POSITION_1","POSITION_2","POSITION_3","POSITION_4","POSITION_5",       "POSITION_3","POSITION_2","POSITION_1","POSITION_5","POSITION_4"]
            for i,pos in enumerate(position_ally):
                my_pos_net_worth = df_raw.loc[(df_raw["position"] == position_ally[i]) & (df_raw["isOnMyTeam"] ==  True) & (df_raw["id"] == match_id), "stats.networthPerMinute"].values[0]
                their_pos_net_worth = df_raw.loc[(df_raw["position"] == position_enemy[i]) & (df_raw["isOnMyTeam"] ==  False) & (df_raw["id"] == match_id), "stats.networthPerMinute"].values[0]
                if (my_pos_net_worth is not None) and (their_pos_net_worth is not None) and (len(my_pos_net_worth) > minute): #does all the finding and math in df_raw and variables, then slaps it into df_calculated
                    pos_diff = my_pos_net_worth[minute] - their_pos_net_worth[minute]
                    df_calculated.loc[(df_calculated["id"] == match_id) & (df_calculated.index % 10 == i), "networthDifference"] += pos_diff #able to put it order of pos1,pos2 cus it matches to the index%10=i

        networth_difference_column(df_raw,df_calculated,match_id,minute) 

        def stats_sum_column(df_raw,df_calculated,match_id,minute,column_label): #stats, can be used for lasthits and denies. returns total sum of stats list at [minute]
            for i,row in df_raw[df_raw["id"] == match_id].iterrows(): #like enumerate, i=index and row=data (cell in this case)
                stat_row = row["stats." + column_label]
                if (stat_row is not None) and (len(stat_row) > (minute-1)): #minute-1 cus unlike networthPerMinute list, lasthit list starts from min 1 
                    stat_sum = sum(stat_row[:(minute-1)])
                    df_calculated.loc[i,column_label + "Sum"] = stat_sum
        
        stats_sum_column(df_raw,df_calculated,match_id,minute,"lastHitsPerMinute")
        stats_sum_column(df_raw,df_calculated,match_id,minute,"deniesPerMinute")
        
        def levels_column(df_raw,df_calculated,match_id,minute):
            seconds = (minute-1) * 60
            for i,row in df_raw[df_raw["id"] == match_id].iterrows(): #this function similar to stats_sum_column, this itterates over each batch of id=match_id (which is unique 10 rows (10players per unique match))
                levelup_row = row["playbackData.playerUpdateLevelEvents"] #gets the specific cell data by the name, "playbackdata.."
                print(levelup_row)
                print(match_id)
                levelup_df = pd.DataFrame(levelup_row) #turns the cell data, a list of dicts, into df for easier computation
                df_filtered = levelup_df[levelup_df["time"]<=seconds]
                level = df_filtered.iloc[-1]["level"] #gets last level event, aka most recent level up. data distilled from df --> int
                df_calculated.loc[i,"level"] = level #adds this int to df_calculated by the row its on

        ###levels_column(df_raw,df_calculated,match_id,minute)

    df_calculated["isOnMyTeam"] = df_raw["isOnMyTeam"]

    return df_calculated #finishes for loop

def player_calculations(df_calculated):
    player_calculations_list = [{}] #final output is list of one dict, so df is all on row 0. add by expanding list[0]["key"]=value
    def networth_difference(df_calculated):
        nw_dict = {
            1:"" ,
            2:"" ,
            3:"" ,
            4:"" ,
            5:"" ,

            6:"" , #6 is 1-3
            7:"" , #7 is 2-2
            8:"" , #8 is 3-1
            9:"" , #9 is 4-5
            10:"" ,#10 is 5-4
        }
        for x in range(1,11):
            every_networth_comparison = df_calculated["networthDifference"].iloc[x-1::10]
            networth_comparison_average = every_networth_comparison.mean()
            nw_dict[x] = (networth_comparison_average).item() #.item() turns np.float64() into native float
        player_calculations_list[0]["networth_difference"] = nw_dict
    
    def averages(df_calculated,position,isOnMyTeam,sum_label,dict_key):
        row_data = df_calculated.loc[(df_calculated["position"] == position) & (df_calculated["isOnMyTeam"] == isOnMyTeam)]
        df_sum = row_data[sum_label]
        sum = df_sum.mean() #takes the df of every match's sum and averages all the matches
        player_calculations_list[0][dict_key] = sum 

        
    networth_difference(df_calculated)
    averages(df_calculated,position,True,"lastHitsPerMinuteSum","lastHitsAverage")
    averages(df_calculated,position,True,"deniesPerMinuteSum","deniesAverage")
    ###averages(df_calculated,position,True,"level","levelAverage")


    df_player_calculations = pd.DataFrame(player_calculations_list)
    return df_player_calculations

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
    

steam_id = 405788540

#steam_id = 171262902 #watson
#steam_id = 108203659 #Rusy's steam ID
#steam_id = 898455820 #malrine
#steam_id = 183719386 #atf
#holy fuck nisha and malrine both have +750g and +650g respectively, all other team members are statistically insignificant (+/- 100) or BURDENSOME (-200 pos1 for malrine), probably due to malrine's high rank.
position = "POSITION_1"
"========================================================"
duration = 20
minute = 11 #MINUTE 11 BY DEFAULT. minute 11 is exactly 10:01
skip_interval = 20
number_of_matches_to_parse = 2 #accepts numbers 0-{skip_interval}, for numbers above it needs to be intervals of {skip_interval}
"========================================================"

responses = []
responses_batch = []
take, skips = skip_calculator(number_of_matches_to_parse,skip_interval)
print(take,skips)
for skip in skips: #does the querying each time for skip

    try:
        query_data = query_matches(take,skip,steam_id,position) #gets the query_data and time_taken as a tuple
        responses_batch.append(query_data)
        
        #with open("api_call_count.txt") as api_call_count:
        #    api_call_count += 

        print(f"skip is {skip}")
    except Exception as error:
        print("API GAVE UP")
        print(f"Error:{error}")
        print(f"skip is {skip}")

for batch in responses_batch:
    responses.extend(batch)

df_raw = pd.json_normalize(responses,"players",["id"])

def make_excel_sheets(df,sheet_name):
    file_name = sheet_name + ".xlsx"
    with open(file_name,"w") as df_file:
        df.to_excel(file_name)


print(df_raw)

df_calculated = (adding_columns(df_raw,steam_id,minute)) #this function turns df_raw into df_calculated
#print(df_calculated)

df_player_calculations = player_calculations(df_calculated)
#print(df_player_calculations)
print(f"Number of matches parsed: {(df_calculated.shape[0])/10}")

make_excel_sheets(df_raw,"raw_data")
make_excel_sheets(df_player_calculations,"player_calculations")

#look at how the reddit guy used skips (for loop to query multiple times) and use that to get larger sample size
#future implementatons: query usage counter and limit, added columns for xp, wins, cs, denies..., graph the data and wins/winrate, and calculate average numbers for live/highmmr games

#there is a nan in levels list, fix. its cus random matches like 7900186009 have playbackdata = null for all, even though it passes isParsed and has a parsedDateTime? (matches 0-100)
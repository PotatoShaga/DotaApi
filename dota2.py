import requests
import numpy as np
import pandas as pd
import openpyxl
import time
import sys

pd.options.display.max_columns = None

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

    response = stratz_query(query) #response consists of json and header
    response_json = response.json()
    response_json = response_json["data"]["player"]["matches"]
    return (response_json)


def adding_columns(df_raw,steam_id,minute):
    important_raw_columns = ["id","playerSlot","position","heroId"]
    df_calculated = df_raw[important_raw_columns].copy()
    df_calculated["networthDifference"] = 0

    for match_id in df_raw["id"].unique(): #agnostically gets raw data for everyone. specific person specification happens in player_calculations
        

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
        

        def levels_column(df_raw,df_calculated,match_id,minute,column_label,df_calculated_name):
            seconds = (minute-1) * 60
            for i,row in df_raw[df_raw["id"] == match_id].iterrows(): #this function similar to stats_sum_column, this itterates over each batch of id=match_id (which is unique 10 rows (10players per unique match))
                levelup_row = row[column_label] #gets the specific cell data by the name, "playbackdata.."

                if isinstance(levelup_row, list): #kind of disgusting fix, if the column entry (aka row) is normal its a list, if its not normal (aka empty, None or NaN) then its not a list
                    levelup_df = pd.DataFrame(levelup_row) #turns the cell data, a list of dicts, into df for easier computation
                    df_filtered = levelup_df[levelup_df["time"]<=seconds]
                    level = df_filtered.iloc[-1][df_calculated_name] #gets last level event, aka most recent level up. data distilled from df --> int
                    df_calculated.loc[i,df_calculated_name] = level #adds this int to df_calculated by the row its on
                else:
                    continue
        
        levels_column(df_raw,df_calculated,match_id,minute,"playbackData.playerUpdateLevelEvents","level")


        def kills_deaths_column(df_raw,df_calculated,match_id,minute,column_label,df_calculated_name): #ALMOST IDENTICAL TO LEVELS_COLUMN
            seconds = (minute-1) * 60
            for i,row in df_raw[df_raw["id"] == match_id].iterrows(): 
                levelup_row = row[column_label] 

                if (isinstance(levelup_row, list)):
                    if (levelup_row): #suffering from success: 0 deaths games (or 0 kills xd) returns empty list, so pythonically if [list] which results in True if its non-empty (and false if empty, so it fails if check if empty) 
                        levelup_df = pd.DataFrame(levelup_row) 
                        df_filtered = levelup_df[levelup_df["time"]<=seconds]
                        value = len(df_filtered) #gets len(df) instead of last entry
                        df_calculated.loc[i,df_calculated_name] = value 
                    else:
                        df_calculated.loc[i,df_calculated_name] = 0 #if levelup_row is empty, that means its value = 0
                else:
                    continue

        kills_deaths_column(df_raw,df_calculated,match_id,minute,"playbackData.killEvents","kills")
        kills_deaths_column(df_raw,df_calculated,match_id,minute,"playbackData.deathEvents","deaths")

    df_calculated["isOnMyTeam"] = df_raw["isOnMyTeam"] #has to be at the end because the master for loop creates the df_raw["isOnMyTeam"]

    return df_calculated #finishes for loop


def player_calculations(df_calculated):
    player_calculations_list = [{}] #final output is list of one dict, so df is all on row 0. add by expanding list[0]["key"]=value


    def networth_difference(df_calculated):
        nw_dict = { 
            1:"" , #1 is 1-1
            2:"" , #2 is 2-2
            3:"" , #3 is 3-3
            4:"" , #4 is 4-4
            5:"" , #5 is 5-5

            6:"" , #6 is 1-3
            7:"" , #7 is 2-2
            8:"" , #8 is 3-1
            9:"" , #9 is 4-5
            10:"" ,#10 is 5-4
        }
        for x in range(1,11): #on first one, x=1, takes all rows of pos1 and calculates mean
            every_networth_comparison = df_calculated["networthDifference"].iloc[x-1::10] #start=x-1, stop=None, step=10
            networth_comparison_average = every_networth_comparison.mean()
            nw_dict[x] = (networth_comparison_average).item() #.item() turns np.float64() into native float
            nw_dict[x] = round(nw_dict[x],5)
        player_calculations_list[0]["networth_difference"] = nw_dict
    

    networth_difference(df_calculated)

    def averages(df_calculated,position,isOnMyTeam,sum_label,dict_key):
        row_data = df_calculated.loc[(df_calculated["position"] == position) & (df_calculated["isOnMyTeam"] == isOnMyTeam)]
        df_sum = row_data[sum_label]
        sum = df_sum.mean() #takes the df of every match's sum and averages all the matches
        sum = round(sum,5)
        player_calculations_list[0][dict_key] = sum 
    
    def average_of_each_players_stat(df_calculated, stat_label, dict_key, mode="Append"): #this takes the average of each of the 10 unique players stats` and gives it back in a dict 1-10 listed in order of your team then their team
        average_dict = {}
        average_dict[1] = round((df_calculated.loc[(df_calculated["position"] == "POSITION_1") & (df_calculated["isOnMyTeam"] == True)][stat_label]).mean(),5)  #gets all your pos and team row, gets all these rows at [stat_label], means and rounds to dict[key:1]
        average_dict[2] = round((df_calculated.loc[(df_calculated["position"] == "POSITION_2") & (df_calculated["isOnMyTeam"] == True)][stat_label]).mean(),5) 
        average_dict[3] = round((df_calculated.loc[(df_calculated["position"] == "POSITION_3") & (df_calculated["isOnMyTeam"] == True)][stat_label]).mean(),5) 
        average_dict[4] = round((df_calculated.loc[(df_calculated["position"] == "POSITION_4") & (df_calculated["isOnMyTeam"] == True)][stat_label]).mean(),5) 
        average_dict[5] = round((df_calculated.loc[(df_calculated["position"] == "POSITION_5") & (df_calculated["isOnMyTeam"] == True)][stat_label]).mean(),5) 

        average_dict[6] = round((df_calculated.loc[(df_calculated["position"] == "POSITION_1") & (df_calculated["isOnMyTeam"] == False)][stat_label]).mean(),5) 
        average_dict[7] = round((df_calculated.loc[(df_calculated["position"] == "POSITION_2") & (df_calculated["isOnMyTeam"] == False)][stat_label]).mean(),5) 
        average_dict[8] = round((df_calculated.loc[(df_calculated["position"] == "POSITION_3") & (df_calculated["isOnMyTeam"] == False)][stat_label]).mean(),5) 
        average_dict[9] = round((df_calculated.loc[(df_calculated["position"] == "POSITION_4") & (df_calculated["isOnMyTeam"] == False)][stat_label]).mean(),5) 
        average_dict[10]= round((df_calculated.loc[(df_calculated["position"] == "POSITION_5") & (df_calculated["isOnMyTeam"] == False)][stat_label]).mean(),5) 

        if mode == "Append": #by default will append value to the output dict with key:value
            player_calculations_list[0][dict_key] = average_dict

        elif mode == "Value": #if instead you want only value
            return average_dict

    average_of_each_players_stat(df_calculated,"lastHitsPerMinuteSum","lastHitsAverage")
    average_of_each_players_stat(df_calculated,"deniesPerMinuteSum","deniesAverage")
    average_of_each_players_stat(df_calculated,"level","levelAverage")

    def quick_kda_zip():
        kills_dict = average_of_each_players_stat(df_calculated,"kills","kdaAverage", mode="Value")
        deaths_dict = average_of_each_players_stat(df_calculated,"deaths","kdaAverage", mode="Value")
        kda_dict = {key: f"{kills_dict[key]}/{deaths_dict[key]}" for key in kills_dict}
        player_calculations_list[0]["kdaAverage"] = kda_dict

    quick_kda_zip()

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
    

#steam_id = 405788540

steam_id = 171262902 #watson
#steam_id = 108203659 #Rusy's steam ID
#steam_id = 898455820 #malrine
#steam_id = 183719386 #atf
#holy fuck nisha and malrine both have +750g and +650g respectively, all other team members are statistically insignificant (+/- 100) or BURDENSOME (-200 pos1 for malrine), probably due to malrine's high rank.
position = "POSITION_1"
"========================================================"
duration = 20
minute = 11 #MINUTE 11 BY DEFAULT. minute 11 is exactly 10:01
skip_interval = 10
number_of_matches_to_parse = 200 #accepts numbers 0-{skip_interval}, for numbers above it needs to be intervals of {skip_interval}
"========================================================"

responses = []
responses_batch = []
take, skips = skip_calculator(number_of_matches_to_parse,skip_interval)
print(f"SKIP INTERVAL IS {take}, SKIP INCREMENTS ARE {skips}")
for skip in skips: #does the querying each time for skip

    try:
        query_data = query_matches(take,skip,steam_id,position) #gets the query_data and time_taken as a tuple
        responses_batch.append(query_data)
        print(f"Current Increment: {skip}")
    except Exception as error:
        print("API GAVE UP")
        print(f"Error:{error}")
        print(f"Current Increment: {skip}")

for batch in responses_batch:
    responses.extend(batch)


df_raw = pd.json_normalize(responses,"players",["id"])

def make_all_excel_sheets(): #just for ease of use, so i dont have to call every one seperately
    def excel_sheets_maker(df,sheet_name):
        file_name = sheet_name + ".xlsx"
        with open(file_name,"w") as df_file:
            df.to_excel(file_name)

    excel_sheets_maker(df_raw,"raw_data")
    excel_sheets_maker(df_player_calculations,"player_calculations")

print(df_raw)

df_calculated = (adding_columns(df_raw,steam_id,minute)) #this function turns df_raw into df_calculated
print("--------------------")
print(df_calculated)

df_player_calculations = player_calculations(df_calculated)
print(df_player_calculations)

make_all_excel_sheets()
print(f"Number of matches parsed: {(df_calculated.shape[0])/10}")

#look at how the reddit guy used skips (for loop to query multiple times) and use that to get larger sample size
#future implementatons: query usage counter and limit, added columns for xp, wins, cs, denies..., graph the data and wins/winrate, and calculate average numbers for live/highmmr games

#there is a nan in levels list, fix. its cus random matches like 7900186009 have playbackdata = null for all, even though it passes isParsed and has a parsedDateTime? (matches 0-100)
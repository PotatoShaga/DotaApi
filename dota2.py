import requests
import numpy as np
import pandas as pd
import openpyxl

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
    response = requests.post(Api_Stratz_Url, json={"query":query}, headers = Headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"SOMETHING WENT WRONG: status code is {response.status_code} and text returned is {response.text}")


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

    response = stratz_query(query)["data"]["player"]["matches"]
    return response


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
                levelup_df = pd.DataFrame(levelup_row) #turns the cell data, a list of dicts, into df for easier computation
                df_filtered = levelup_df[levelup_df["time"]<=seconds]
                level = df_filtered.iloc[-1]["level"] #gets last level event, aka most recent level up. data distilled from df --> int
                df_calculated.loc[i,"level"] = level #adds this int to df_calculated by the row its on

        
        levels_column(df_raw,df_calculated,match_id,minute) #this is broken, probably not enough specificiers on where to put data. itterows would just use i, but im tryna use vectorization

    return df_calculated #finishes for loop

def player_calculations(df_calculated):
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

    return nw_dict

def skip_calculator(number_of_matches_to_parse): #given input as an interval of 100 (like 300), outputs the skips list [0,100,200] for the api functions to iterate over. WHAT IF I WANT <100 for TESTING??
    if number_of_matches_to_parse <= 100:
        take = number_of_matches_to_parse
        skips = [0]
    else:
        take = 100
        skips = []
        intervals = number_of_matches_to_parse / 100
        for x in range(int(intervals)):
            skips.append(x*100)
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
minute = 11 #minute 11 is exactly 10:01
number_of_matches_to_parse = 10 #accepts numbers 0-100, for numbers above it needs to be intervals of 100
"========================================================"

responses = []
take, skips = skip_calculator(number_of_matches_to_parse)
for skip in skips: #does the querying each time for skip
    response = query_matches(take,skip,steam_id,position)
    responses.extend(response)
    df_raw = pd.json_normalize(responses,"players",["id"])


print(df_raw)
def make_excel_sheets(df_raw):
    with open("df_raw.xlsx","w") as df_raw_file:
        df_raw.to_excel("df_raw.xlsx")

#make_excel_sheets(df_raw)

df_calculated = (adding_columns(df_raw,steam_id,minute)) #this function turns df_raw into df_calculated
print(df_calculated)

personal_calculations = player_calculations(df_calculated)
print(personal_calculations)

#look at how the reddit guy used skips (for loop to query multiple times) and use that to get larger sample size
#future implementatons: query usage counter and limit, added columns for xp, wins, cs, denies..., graph the data and wins/winrate, and calculate average numbers for live/highmmr games

#function and variable naming: snake_case for everything except column labels which are in pascalCase, as the stratz api uses pascalCase for theirs
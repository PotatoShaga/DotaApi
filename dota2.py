import requests
import numpy as np
import pandas as pd

#GOAL: START SIMPLE. SIMPLY PULL AVERAGE DATA FROM MY PROFILE.
# MAYBE CALCULATE MY LANING SKILL ISSUE, GOLD AT 10MIN AND STOP BLAMING TEAM

Api_Stratz_Url = "https://api.stratz.com/graphql"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJTdWJqZWN0IjoiZmRmNjcwYjEtYThhOS00NjM1LTk0ZjktZjBmYTVjZDkzZjU5IiwiU3RlYW1JZCI6IjQwNTc4ODU0MCIsIm5iZiI6MTcwMDM2ODc1NCwiZXhwIjoxNzMxOTA0NzU0LCJpYXQiOjE3MDAzNjg3NTQsImlzcyI6Imh0dHBzOi8vYXBpLnN0cmF0ei5jb20ifQ.RRtK4zwNqnp7EPda-BkBNI08hAlAw5OqqbY9RrzkFNs"

Headers = {
    "content-type": "application/json",
    "Authorization": f"Bearer {token}",
}
def stratz_query(query):
    response = requests.post(Api_Stratz_Url, json={"query":query}, headers = Headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"SOMETHING WENT WRONG: status code is {response.status_code} and text returned is {response.text}")


def query_matches(take,skips,steamID,position):
#double {{ is to allow using { for f string, print({{steamID}}) results in {steamID}; curly brackets for graphQL syntax preserved
    query = f"""{{
    player(steamAccountId:{steamID}){{
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


def adding_columns(df_raw,steamID,minute):
    df_calculated_data = [df_raw["id"],df_raw["playerSlot"],df_raw["position"],df_raw["heroId"]] #adds important raw data to calculated
    df_calculated = pd.DataFrame(df_calculated_data)
    df_calculated["networthDifference"] = 0
    df_calculated["lasthitAverage"] = 0
    print(df_calculated)

    for match_id in df_raw["id"].unique():
        
        def isOnMyTeamColumn(df,match_id,steamID): #for some reason these parameters arent needed inside this adding_columns function? like code works perfectly fine if u delete the parameters, ig cus parameters already gotten
            radiant = df.loc[(df["steamAccountId"]==steamID) & (df["id"]==match_id),"isRadiant"].values[0]
            if radiant == True:
                df.loc[df["id"] == match_id,"isOnMyTeam"] = df["isRadiant"]
            else:
                df.loc[df["id"] == match_id,"isOnMyTeam"] = ~df["isRadiant"]

        isOnMyTeamColumn(df_raw,match_id,steamID)

        #first df is df_raw, second df is df_calculated 
        def networthDifferenceColumn(df,df_calculated,match_id,minute): #for each position, finds the difference of MyPosNW - TheirPosNW and then adds it the column in the order of pos1,pos2,po3,pos4,pos5. Will ALWAYS be perspective of ally - enemy.
            position_ally = ["POSITION_1","POSITION_2","POSITION_3","POSITION_4","POSITION_5",        "POSITION_1","POSITION_2","POSITION_3","POSITION_4","POSITION_5"]
            position_enemy = ["POSITION_1","POSITION_2","POSITION_3","POSITION_4","POSITION_5",       "POSITION_3","POSITION_2","POSITION_1","POSITION_5","POSITION_4"]
            for i,pos in enumerate(position_ally):
                MyPosNetWorth = df.loc[(df["position"] == position_ally[i]) & (df["isOnMyTeam"] ==  True) & (df["id"] == match_id), "stats.networthPerMinute"].values[0]
                TheirPosNetWorth = df.loc[(df["position"] == position_enemy[i]) & (df["isOnMyTeam"] ==  False) & (df["id"] == match_id), "stats.networthPerMinute"].values[0]
                if (MyPosNetWorth is not None) and (TheirPosNetWorth is not None) and (len(MyPosNetWorth) > minute):
                    PosDiff = MyPosNetWorth[minute] - TheirPosNetWorth[minute]
                    df_calculated.loc[(df_calculated["id"] == match_id) & (df_calculated.index % 10 == i), "networthDifference"] += PosDiff #able to put it order of pos1,pos2 cus it matches to the index%10=i
            return df

        networthDifferenceColumn(df_raw,df_calculated,match_id,minute) 

        def statsSumColumn(df,df_calculated,match_id,minute,columnLabel): #stats, can be used for lasthits and denies. returns total sum of stats list at [minute]
            for i,row in df[df["id"] == match_id].iterrows():
                statRow = row["stats." + columnLabel]
                if (statRow is not None) and (len(statRow) > (minute-1)): #minute-1 cus unlike networthPerMinute list, lasthit list starts from min 1 
                    statSum = sum(statRow[:(minute-1)])
                    df_calculated.loc[i,columnLabel + "Sum"] = statSum
        
        statsSumColumn(df_raw,df_calculated,match_id,minute,"lastHitsPerMinute")
        statsSumColumn(df_raw,df_calculated,match_id,minute,"deniesPerMinute")

    return df_calculated #finishes for loop

def calculate(df):
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
        every_networth_comparison = df["networthDifference"].iloc[x-1::10]
        networth_comparison_average = every_networth_comparison.mean()
        nw_dict[x] = networth_comparison_average

    return nw_dict

def skip_calculator(numberOfMatchesToParse): #given input as an interval of 100 (like 300), outputs the skips list [0,100,200] for the api functions to iterate over. WHAT IF I WANT <100 for TESTING??
    if numberOfMatchesToParse <= 100:
        take = numberOfMatchesToParse
        skips = [0]
    else:
        take = 100
        skips = []
        intervals = numberOfMatchesToParse / 100
        for x in range(int(intervals)):
            skips.append(x*100)
    return (take, skips)
    

steamID = 405788540
#steamID = 171262902 #watson
#steamID = 108203659 #Rusy's steam ID
#steamID = 898455820 #malrine
#steamID = 183719386 #atf
#holy fuck nisha and malrine both have +750g and +650g respectively, all other team members are statistically insignificant (+/- 100) or BURDENSOME (-200 pos1 for malrine), probably due to malrine's high rank.
position = "POSITION_1"

minute = 11 #minute 11 is exactly 10:01
numberOfMatchesToParse = 2 #accepts numbers 0-100, for numbers above it needs to be intervals of 100

responses = []
take, skips = skip_calculator(numberOfMatchesToParse)
for skip in skips: #does the querying each time for skip
    response = query_matches(take,skip,steamID,position)
    responses.extend(response)
    df_raw = pd.json_normalize(responses,"players",["id"])


print(df_raw)
df_calculated = (adding_columns(df_raw,steamID,minute)) #this function turns df_raw into df_calculated
print(df_calculated)

#final_calculations = calculate(df_calculated)
#print(final_calculations)

#look at how the reddit guy used skips (for loop to query multiple times) and use that to get larger sample size
#future implementatons: query usage counter and limit, added columns for xp, wins, cs, denies..., graph the data and wins/winrate, and calculate average numbers for live/highmmr games
import pandas as pd
import matplotlib.pyplot as plt

pd.options.display.max_columns = None


#This file contains the functions which construct df_calculated/df_player_calculated from df_raw, and generate the matlab graphs

def adding_columns(df_raw, steam_id, minute, isOnMyTeam, number_of_matches_to_parse, position):
    important_raw_columns = ["id","steamAccountId","position","heroId", "isVictory"]
    df_calculated = df_raw[important_raw_columns].copy()
    df_calculated["networthDifference"] = 0
    df_raw["wins"] = 0
    df_raw["totalmatches"] = 0
    for indices, match_id in enumerate(df_raw["id"].unique()): #agnostically gets raw data for everyone (except in winrate). more specific specification happens in player_calculations
        #print(indices)
        

        def is_on_my_team_column(df_raw, match_id, steam_id, isOnMyTeam): #isOnMyTeam is variable in script to see if you actually want correct or inverted results
            radiant = df_raw.loc[(df_raw["steamAccountId"]==steam_id) & (df_raw["id"]==match_id),"isRadiant"].values[0]

            if isOnMyTeam == True:
                if radiant == True:
                    df_raw.loc[df_raw["id"]==match_id,"isOnMyTeam"] = df_raw["isRadiant"]
                else:
                    df_raw.loc[df_raw["id"]==match_id,"isOnMyTeam"] = ~df_raw["isRadiant"]

            elif isOnMyTeam == False:
                if radiant == True:
                    df_raw.loc[df_raw["id"]==match_id,"isOnMyTeam"] = ~df_raw["isRadiant"] #not operator gets swapped if ==false (so everything gets inverted)
                else:
                    df_raw.loc[df_raw["id"]==match_id,"isOnMyTeam"] = df_raw["isRadiant"]
        is_on_my_team_column(df_raw,match_id,steam_id, isOnMyTeam)

        def winrate_column(df_raw, df_calculated, match_id, steam_id, number_of_matches_to_parse):
            victory_bool = df_raw.loc[(df_raw["id"]==match_id) & (df_raw["steamAccountId"]==steam_id), "isVictory"].values[0]
            if indices == 0:

                denominator = number_of_matches_to_parse*0 + 1
                if victory_bool == True:
                    numerator = number_of_matches_to_parse*0 + 1
                if victory_bool == False:
                    numerator = number_of_matches_to_parse*0 #dampening looks work then just starting at 0 or 100, need database implementation here. number_of matches should be # past week matches

            elif indices != 0:
                numerator = df_raw.loc[(df_raw["id"]==previous_match_id) & (df_raw["steamAccountId"]==steam_id), "wins"].values[0] #pulls num and denom from df_raw's previous data
                denominator = df_raw.loc[(df_raw["id"]==previous_match_id) & (df_raw["steamAccountId"]==steam_id), "totalmatches"].values[0] # I NEED PREVIOUS MATCHID
                denominator += 1
                if victory_bool == True:
                    numerator += 1
            #print(f"THIS IS NUMERATOR AND DENOMINATOR: {numerator}, {denominator}")
            df_raw.loc[(df_raw["id"]==match_id) & (df_raw["steamAccountId"]==steam_id), "wins"] = numerator #assigns num and denom to df_raw
            df_raw.loc[(df_raw["id"]==match_id) & (df_raw["steamAccountId"]==steam_id), "totalmatches"] = denominator

            winrate = numerator / denominator
            df_calculated.loc[(df_calculated["id"]==match_id) & (df_calculated["steamAccountId"]==steam_id), "winrate"] = winrate
        winrate_column(df_raw, df_calculated, match_id, steam_id, number_of_matches_to_parse)
        previous_match_id = match_id

        #first df is df_raw, second df is df_calculated 
        def networth_difference_column(df_raw, df_calculated, match_id, minute): #for each position, finds the difference of MyPosNW - TheirPosNW and then adds it the column in the order of pos1,pos2,po3,pos4,pos5. Will ALWAYS be perspective of ally - enemy.
            position_ally = ["POSITION_1","POSITION_2","POSITION_3","POSITION_4","POSITION_5",        "POSITION_1","POSITION_2","POSITION_3","POSITION_4","POSITION_5"]
            position_enemy = ["POSITION_1","POSITION_2","POSITION_3","POSITION_4","POSITION_5",       "POSITION_3","POSITION_2","POSITION_1","POSITION_5","POSITION_4"]
            for i,pos in enumerate(position_ally):
                my_pos_net_worth = df_raw.loc[(df_raw["position"] == position_ally[i]) & (df_raw["isOnMyTeam"] ==  True) & (df_raw["id"] == match_id), "stats.networthPerMinute"].values[0] # this searching for multiple conditions for every operation is probably slow? if df_raw were listed by pos1,pos2.. it wouldn't need condition searching
                their_pos_net_worth = df_raw.loc[(df_raw["position"] == position_enemy[i]) & (df_raw["isOnMyTeam"] ==  False) & (df_raw["id"] == match_id), "stats.networthPerMinute"].values[0]
                if (my_pos_net_worth is not None) and (their_pos_net_worth is not None) and (len(my_pos_net_worth) > minute): #does all the finding and math in df_raw and variables, then slaps it into df_calculated
                    pos_diff = my_pos_net_worth[minute-1] - their_pos_net_worth[minute-1]
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
        

        def levels_column(df_raw, df_calculated, match_id, minute, column_label, df_calculated_name):
            seconds = (minute-1) * 60
            #if the playbackData.playerUpdateLevelEvents column doesnt exist, fuck it set all values to 0. Since I know stratz stores playback data only for 1-3 months, if theres no recent data theres probably not old data
            #
            if column_label not in df_raw.columns:  
                df_raw[column_label] = 0
                df_calculated[df_calculated_name] = 0

            for i,row in df_raw[df_raw["id"] == match_id].iterrows(): #this function similar to stats_sum_column, this itterates over each batch of id=match_id (which is unique 10 rows (10players per unique match))
                levelup_row = row[column_label] #gets the specific cell data by the name, "playbackdata.."

                if isinstance(levelup_row, list): #kind of disgusting fix, if the column entry (aka row) is normal its a list, if its not normal (aka empty, None or NaN) then its not a list
                    levelup_df = pd.DataFrame(levelup_row) #turns the cell data, a list of dicts, into df for easier computation
                    df_filtered = levelup_df[levelup_df["time"]<=seconds]
                    level = df_filtered.iloc[-1][df_calculated_name] #gets last level event, aka most recent level up. data distilled from df --> int
                    df_calculated.loc[i,df_calculated_name] = level #adds this int to df_calculated by the row its on
                else:
                    continue
        
        levels_column(df_raw, df_calculated, match_id, minute, "playbackData.playerUpdateLevelEvents", "level")


        def kills_deaths_column(df_raw,df_calculated,match_id,minute,column_label,df_calculated_name): #ALMOST IDENTICAL TO LEVELS_COLUMN
            seconds = (minute-1) * 60

            if column_label not in df_raw.columns:  
                df_raw[column_label] = 0
                df_calculated[df_calculated_name] = 0

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
                    df_raw[column_label] = 0
                    continue

        kills_deaths_column(df_raw,df_calculated,match_id,minute,"playbackData.killEvents","kills")
        kills_deaths_column(df_raw,df_calculated,match_id,minute,"playbackData.deathEvents","deaths")

    df_calculated["isOnMyTeam"] = df_raw["isOnMyTeam"] #has to be at the end because the master for loop creates the df_raw["isOnMyTeam"]

    return df_calculated #finishes for loop



#PLAYER SPECIFIC CALCULATIONS
#most of the work is getting specific values from df_calculated into a sum/average. Requires no specifics as it calculates this for every single player (and data is all main character centric)

def player_calculations(df_calculated, steam_id, minute, isOnMyTeam, number_of_matches_to_parse, position, winrate_dict):
    player_calculations_dict = {} #final output is dict of dicts, add by player_calculations_dict["dict_name"]=dict

    def player_parameters(steam_id, minute, isOnMyTeam, number_of_matches_to_parse, position):
        parameter_dicts = {
            "steam_id": steam_id,
            "minute": minute-1,
            "isOnMyTeam": isOnMyTeam,
            "number_of_matches_to_parse": number_of_matches_to_parse,
            "position": position,
        }
        return parameter_dicts

    parameters_dict = player_parameters(steam_id, minute, isOnMyTeam, number_of_matches_to_parse, position)

    def networth_difference(df_calculated):
        nw_dict = {#Ally-Enemy 
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
        player_calculations_dict["networth_difference"] = nw_dict
    

    networth_difference(df_calculated)

    def average_of_each_players_stat(df_calculated, stat_label, dict_key, mode="Append"): #this takes the average of each of the 10 unique players stats` and gives it back in a dict 1-10 listed in order of your team then their team
        average_dict = {}
        average_dict[1] = float(round((df_calculated.loc[(df_calculated["position"] == "POSITION_1") & (df_calculated["isOnMyTeam"] == True)][stat_label]).mean(),5))  #gets all your pos and team row, gets all these rows at [stat_label], means and rounds to dict[key:1]
        average_dict[2] = float(round((df_calculated.loc[(df_calculated["position"] == "POSITION_2") & (df_calculated["isOnMyTeam"] == True)][stat_label]).mean(),5)) 
        average_dict[3] = float(round((df_calculated.loc[(df_calculated["position"] == "POSITION_3") & (df_calculated["isOnMyTeam"] == True)][stat_label]).mean(),5)) 
        average_dict[4] = float(round((df_calculated.loc[(df_calculated["position"] == "POSITION_4") & (df_calculated["isOnMyTeam"] == True)][stat_label]).mean(),5)) 
        average_dict[5] = float(round((df_calculated.loc[(df_calculated["position"] == "POSITION_5") & (df_calculated["isOnMyTeam"] == True)][stat_label]).mean(),5)) 

        average_dict[6] = float(round((df_calculated.loc[(df_calculated["position"] == "POSITION_1") & (df_calculated["isOnMyTeam"] == False)][stat_label]).mean(),5)) 
        average_dict[7] = float(round((df_calculated.loc[(df_calculated["position"] == "POSITION_2") & (df_calculated["isOnMyTeam"] == False)][stat_label]).mean(),5)) 
        average_dict[8] = float(round((df_calculated.loc[(df_calculated["position"] == "POSITION_3") & (df_calculated["isOnMyTeam"] == False)][stat_label]).mean(),5)) 
        average_dict[9] = float(round((df_calculated.loc[(df_calculated["position"] == "POSITION_4") & (df_calculated["isOnMyTeam"] == False)][stat_label]).mean(),5)) 
        average_dict[10]= float(round((df_calculated.loc[(df_calculated["position"] == "POSITION_5") & (df_calculated["isOnMyTeam"] == False)][stat_label]).mean(),5)) 
        #Bruh do vectorisation with mean(axis=0)? the numpy or pandas way
        if mode == "Append": #by default will append value to the output dict with key:value
            player_calculations_dict[dict_key] = average_dict

        elif mode == "Value": #if instead you want only value
            return average_dict

    average_of_each_players_stat(df_calculated,"lastHitsPerMinuteSum","lastHitsAverage")
    average_of_each_players_stat(df_calculated,"deniesPerMinuteSum","deniesAverage")
    average_of_each_players_stat(df_calculated,"level","levelAverage")



    def quick_kda_zip():
        kills_dict = average_of_each_players_stat(df_calculated,"kills","kdaAverage", mode="Value")
        deaths_dict = average_of_each_players_stat(df_calculated,"deaths","kdaAverage", mode="Value")
        kda_dict = {key: f"{round(kills_dict[key],2)} / {round(deaths_dict[key],2)}" for key in kills_dict}
        player_calculations_dict["kdaAverage"] = kda_dict

    quick_kda_zip()
    player_calculations_dict["winrate"] = winrate_dict

    df_player_calculations = pd.DataFrame(player_calculations_dict)
    return df_player_calculations, parameters_dict


#PLAYER SPECIFIC GRAPHS
def player_graphs(df_calculated, position): #can specify position and isOnMyTeam=False to generate graphs of enemies/other players
    df_centric_to_main_character = df_calculated[(df_calculated["position"] == position) & (df_calculated["isOnMyTeam"] == True)]
    dict_of_plts = {}


    def stat_graph(locator, need_ith_term=False, levels_kda = False):
        if need_ith_term == True: #only runs for networth_diff
            start = int(position[-1]) + 5 - 1#for POSITION_1, start = 1 + 5 - 1 = 5. So this should take the networth diff 6-10, which is opposition laner. -1 is df starts at row 0, not row 1
            df_y_values = df_calculated.iloc[start::10]["networthDifference"]
        elif need_ith_term == False:
            df_y_values = df_centric_to_main_character[locator]
            df_y_values = df_y_values.iloc[::-1]
        
        df_x_values = range(1, len(df_y_values)+1)
        plt.figure()

        plt.scatter(df_x_values, df_y_values, alpha=0.5)
        plt.xlabel("oldest --> newest games")
        plt.ylabel("data")
        plt.title(f"{locator}")
        plt.gca().invert_xaxis() #so graph reads oldest --> newest instead of listing newest games from the left side

        if levels_kda == True: #just makes window value more precise for levels/kda, which usually has so little datapoints from playbackdata running out it always looks meaningless
            window_value = 5
        elif levels_kda == False: 
            window_value = 25

        df_moving_average = df_y_values.rolling(window=window_value, min_periods=1).mean() #this is the average in a window of 10, will be inaccurate for first 10 and last 10 items
        plt.plot(df_x_values, df_moving_average, color='blue', label='Moving Average', linewidth=2)

        current_plot = plt.gcf() #get current figure
        dict_of_plts[locator] = current_plot
    

    stat_graph("networthDifference", need_ith_term=True)
    stat_graph("lastHitsPerMinuteSum")
    stat_graph("deniesPerMinuteSum")
    stat_graph("level", levels_kda = True)
    stat_graph("kills", levels_kda = True)
    stat_graph("deaths", levels_kda = True) #will take more work to get graph of kda, as when its 1/0, you can't plot the ratio

    return dict_of_plts


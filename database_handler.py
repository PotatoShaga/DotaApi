import sqlite3
import json

#This file hosts the functions which interact with the SQLite database

def table_player_calculations(df_player_calculations): #inserts or updates the data inside player_calculations 
    sqlite_connection = sqlite3.connect("sql.db")
    cursor = sqlite_connection.cursor()
    
    steam_id = df_player_calculations["player_parameters"][0]["steam_id"]
    number_of_matches = df_player_calculations["player_parameters"][0]["number_of_matches_to_parse"]
    position = int(df_player_calculations["player_parameters"][0]["position"][-1]) # turns "POSITION_1" --> int(1)
    minute = df_player_calculations["player_parameters"][0]["minute"]
    isOnMyTeam = df_player_calculations["player_parameters"][0]["isOnMyTeam"]

    column_name_string = f"steam_id, number_of_matches, position, minute, isOnMyTeam"
    column_value_string = f"{steam_id}, {number_of_matches}, {position}, {minute}, {isOnMyTeam}"
    for dict in df_player_calculations.columns:
        cell_dict = df_player_calculations.loc[0, dict]
        if (dict == "networth_difference"): #currently, only use for loop for nw_diff (most important column), maybe later expand this for loop
            for key in cell_dict.keys():
                column_name = f"nw_diff_{key}"
                column_value = df_player_calculations[dict][0][key]
                column_name_string += f", {column_name}"
                column_value_string += f", {column_value}"
        else:
            pass

    #print(f"{column_name_string} = {column_value_string}")
    query = f"INSERT OR REPLACE INTO player_calculations ({column_name_string}) VALUES ({column_value_string})" #need '{}' for text, integers dont need it
    cursor.execute(query)
    #query = f"INSERT OR REPLACE INTO player_calculations (steam_id, networth_difference) VALUES ({steam_id}, '{networth_difference_json}')" #need '{}' for text, integers dont need it
    #cursor.execute(query)

    cursor.close()
    sqlite_connection.commit()
    sqlite_connection.close()

### THOUGHTS: WILL I REALLY NEED ALL THE COLUMNS? LIKE LASTHIT_4 (MY POS4 CS), LIKE CMON ITS MROE IMPORTAMT TO SET UP WORKING SQL. MAYBE JUST MANUAALY ADD MOST IMPORTANT COLUMNS?

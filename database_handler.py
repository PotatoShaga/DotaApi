import sqlite3
import json
import pandas as pd

#This file hosts the functions which interact with the SQLite database

def table_player_calculations(df_player_calculations, parameters_dict): #inserts or updates the data inside player_calculations 
    sqlite_connection = sqlite3.connect("sql.db")
    cursor = sqlite_connection.cursor()
    table_name = "player_calculations"

    steam_id = parameters_dict["steam_id"]
    number_of_matches = parameters_dict["number_of_matches_to_parse"]
    position = int(parameters_dict["position"][-1]) # turns "POSITION_1" --> int(1)
    minute = parameters_dict["minute"]
    isOnMyTeam = parameters_dict["isOnMyTeam"]

    flat_dict = parameters_dict # parameters dict will be our first few columns 
    for column in df_player_calculations.columns:
        for i, value in df_player_calculations[column].items(): # iterates over each item in the column
            flat_dict[f"{column}_{i}"] = value
    flat_df = pd.DataFrame([flat_dict])
    print(flat_df)

    
    flat_df.to_sql(table_name, sqlite_connection, if_exists="replace",index=False,index_label="{steam_id}")

    cursor.close()
    sqlite_connection.commit()
    sqlite_connection.close()

### THOUGHTS: WILL I REALLY NEED ALL THE COLUMNS? LIKE LASTHIT_4 (MY POS4 CS), LIKE CMON ITS MROE IMPORTAMT TO SET UP WORKING SQL. MAYBE JUST MANUAALY ADD MOST IMPORTANT COLUMNS?

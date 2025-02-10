import sqlite3
import json

#This file hosts the functions which interact with the SQLite database

def db_player_calculations(df_player_calculations): #inserts or updates the data inside player_calculations 
    sqlite_connection = sqlite3.connect("sql.db")
    cursor = sqlite_connection.cursor()
    
    steam_id = df_player_calculations["player_parameters"][0]["steam_id"]
    player_parameters_json = json.dumps(df_player_calculations["player_parameters"][0])
    networth_difference_json = json.dumps(df_player_calculations["networth_difference"][0])

    query = f"INSERT OR REPLACE INTO player_calculations (steam_id, parameters, networth_difference) VALUES ({steam_id}, '{player_parameters_json}', '{networth_difference_json}')"
    cursor.execute(query)

    sqlite_connection.commit()
    sqlite_connection.close()


from dotenv import load_dotenv
load_dotenv()
import json
import pandas as pd
import mysql.connector
import os
from sqlalchemy import create_engine, text
import mysql.connector
import mysql
from mysql.connector import Error

#This file hosts the functions which interact with the SQLite database

def table_player_calculations_staging(df_player_calculations, parameters_dict,engine): #inserts or updates the data inside player_calculations 
    table_name = "player_calculations"
    table_name_staging = "player_calculations_staging"
    with engine.connect() as conn:
        flat_dict = parameters_dict # parameters dict will be our first few columns 
        for column in df_player_calculations.columns:
            for i, value in df_player_calculations[column].items(): # iterates over each item in the column
                flat_dict[f"{column}_{i}"] = value
        flat_df = pd.DataFrame([flat_dict])
        flat_df.to_sql(table_name_staging, con=engine, if_exists="replace", index=False) # replace staging table with row
        print("df to sql successful ")
        return flat_df

def join_tables(flat_df, engine):
    table_name = "player_calculations"
    table_name_staging = "player_calculations_staging"
    with engine.connect() as conn:
        columns = ", ".join(flat_df.columns) # insert or replace the two tables
        
        table_join_query = f"""
            REPLACE INTO {table_name} ({columns})
            SELECT {columns} FROM {table_name_staging}""" 

        conn.execute(text(table_join_query))
        conn.commit()
        conn.close()
        print("Staging table join succesful")
    
### THOUGHTS: WILL I REALLY NEED ALL THE COLUMNS? LIKE LASTHIT_4 (MY POS4 CS), LIKE CMON ITS MROE IMPORTAMT TO SET UP WORKING SQL. MAYBE JUST MANUAALY ADD MOST IMPORTANT COLUMNS?

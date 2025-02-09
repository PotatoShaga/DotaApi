import sqlite3

#This file hosts the functions which interact with the SQLite database

sqlite_connection = sqlite3.connect("sql.db")

cursor = sqlite_connection.cursor()
print("INIT?")

query = "select sqlite_version();"
cursor.execute(query)
result = cursor.fetchall()
print(f"version is {format(result)} and whatever result is {result}")
cursor.close()
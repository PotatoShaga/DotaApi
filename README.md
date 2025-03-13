# DotaApi
![image](https://github.com/user-attachments/assets/1641a688-4fad-40e6-9c59-5c7b0ee6b919)


This python program takes in your steam_id and position to request a query to StratzApi. Processing the data from the query, it provides a statistical overview (data + graph) of your relative networth, cs/denies, level, and kda at a selected minute. This program can be run from the terminal, or run from a website locally. FOR BOTH you need to add a .env file to the DotaApi folder so that it contains 

TOKEN = {stratz_api_token} 

which is provided at https://stratz.com/api. 

The data processing uses mostly Pandas' dataframes, the data is given in the form of an excelsheet, the graphs were made with Matplotlib, and the website was created with Django. 

# Running the website locally
Make sure you have the .env file. Change your current directory to DotaApi/djangotut, and type into the console python manage.py runserver. Then ctrl-click the local address to open it. The unneeded excel files (pngs, raw _data exceel sheet) are stored inside djangotut. 

# netWorthDifference
For networthDifference, the stats are ordered by comparing the respective positions to themselves for index 1-5. Index 6-10 are comparing positions to their lane opposition. It follows the table below:  

Formula: AllyPosition - EnemyPosition  
#1 is 1-1 #so gets difference between pos1 of your team and pos1 of enemy team  
#2 is 2-2  
#3 is 3-3  
#4 is 4-4  
#5 is 5-5  
#6 is 1-3 #so gets difference between pos1 of your team and pos3 of enemy team  
#7 is 2-2  
#8 is 3-1  
#9 is 4-5  
#10 is 5-4  

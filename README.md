# DotaApi
![image](https://github.com/user-attachments/assets/e9749430-061f-4389-bc39-31612ebec1d5)
![image](https://github.com/user-attachments/assets/be4f25a5-32a9-499c-8da7-d2715e422e89)

Given input parameters of your steamid, position, minute, and number of matches to parse, this program analyzes the data to return and visualize trends for 6 unique categories, with each containing 10 datapoints (1 for every player in the game). This is achieved by sending GraphQL queries to StratzApi, processing the data in pandas DataFrame, and then graphing the change in time of these stats with Matplotlib. The 6 unique categories are your winrates, networthDifferences, total CS, total denies, level, and kda. These stats are all taken at the specified minute snapshot. 

This program also uses basic SQL queries to store each player's preformance analysis as a 65 column row in a MySQL database. This program can be run from the terminal, or run as a locally deployed website with django. For both you need to add a .env file to the DotaApi folder so that it contains 

TOKEN = {stratz_api_token} 

which is provided at https://stratz.com/api. 

The MySQL connections also require a password for a useraccount in .env, which currently I've only created for myself, so you will need to disable the MySQL functions. 


# Running the website locally
Make sure you have the .env file. Change your current directory to DotaApi/djangotut, and type into the console python manage.py runserver. Then ctrl-click the local address to open it. The extra files (pngs, raw _data excel sheet) are stored inside djangotut. 

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

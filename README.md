# DotaApi
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

There is a large issue with stratz api not returning playbackData for certain matches/matches past a certain point. Probably to do with how they parse matches/requires manual parse. Values will default to 0 when theres no data, which will dampen stats towards 0.

# Running the website locally
Change your current directory to DotaApi/djangotut, and type into the console python manage.py runserver. Then ctrl click the local address to open it. The unneeded excel files (pngs, raw _data exceel sheet) are stored inside djangotut. 

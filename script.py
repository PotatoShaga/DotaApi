import pandas as pd
import api_handler
import calculations

pd.options.display.max_columns = None


#VARIABLES

steam_id = 405788540
position = "POSITION_1"
"========================================================"
duration = 20
minute = 11 #MINUTE 11 BY DEFAULT. minute 11 is exactly 10:01
skip_interval = 10
number_of_matches_to_parse = 200 #accepts numbers 0-{skip_interval}, for numbers above it needs to be intervals of {skip_interval}
"========================================================"

def make_all_excel_sheets(df_raw,df_player_calculations): #just for ease of use, so i dont have to call every one seperately
    def excel_sheets_maker(df,sheet_name):
        file_name = sheet_name + ".xlsx"
        with open(file_name,"w") as df_file:
            df.to_excel(file_name)

    excel_sheets_maker(df_raw,"raw_data")
    excel_sheets_maker(df_player_calculations,"player_calculations")


print(df_raw)

df_calculated = (adding_columns(df_raw,steam_id,minute)) #this function turns df_raw into df_calculated
print("--------------------")
print(df_calculated)

df_player_calculations = player_calculations(df_calculated)
print(df_player_calculations)

make_all_excel_sheets()
print(f"Number of matches parsed: {(df_calculated.shape[0])/10}")

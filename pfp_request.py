# Import Libraries/Modules
import numpy as np
import pandas as pd
import random
import time
from team_dict import nfl_teams
from league_info import nfl_conference_division

# Line Breaks for formatting
line_break = '-' * 70

# Introduction to program
print("""
NFL PFP Data Request Program!   
      """) # For formatting only
print(line_break) # For formatting only

# Request team information for analysis
while True:
    try:
        team = input("Enter the full NFL Team Name being requested: ").strip().title()
        if team not in nfl_teams:
            print('Invalid team name. Please input a valid NFL team name.')
            continue
        else:
            pfp_team = nfl_teams[team]
            break
    except ValueError:
        print('Invalid input. Please try again.')
        continue

# Request seasons for analysis
while True:
    try:
        start_season = int(input('Enter the starting season: '))
        end_season = int(input('Enter the ending season: '))
        if start_season < 2002 or end_season > 2025: # Considers Houston Texans inception in 2002
            print("""
Seasons must be between 2002 and 2025. Please re-enter the seasons.
                  """)
            continue
        elif start_season > end_season:
            print("""
Starting season must be less than or equal to the ending season. Please re-enter the seasons.
                  """)
            continue
        else:
            print(f"""
We will retrieve PFP data for the {team} from {start_season} to {end_season}.
                  """)
            break
    except ValueError:
        print("""
Invalid input. Please enter valid season years.
              """)
        continue

# Scrape PFP data

# Column rename dictionary
column_rename = {
    'Unnamed: 5':'Location', 'Rslt':'Result', 'Pts':f'{pfp_team.upper()}_pts', 'PtsO':'Opps_pts',
    'Cmp':'pCmp', 'Att':'pAtt', 'Cmp%':'pCmp%', 'Yds':'pYds', 'TD': 'pTD',
    'Y/A':'pY/A', 'AY/A':'pAY/A', 'Rate':'pRate', 'Yds.1':'SkYds', 'Att.1':'rAtt',
    'Yds.2':'rYds', 'TD.1':'rTD', 'Y/A.1':'rY/A', 'Yds.3':'PntYds', 'Pass':'fdPass',
    'Rsh':'fdRush', 'Pen':'fdPen', 'Pen.1':'Pen', 'Yds.4':'PenYds'
}

# Time calculation start - testing purposes
start_time = time.time()

# Create list of seasons
seasons = range(start_season, end_season+1)

# Create empty dataframe to store PFP data
df = pd.DataFrame()

# Iterate through team's seasons
for season in seasons:
    url = 'https://www.pro-football-reference.com/teams/' + pfp_team + '/' + str(season) + '/gamelog'
    print(f'Gathering {season} season data for the {team}...')
    
    # Scrape Team Gamelog Data
    table_id = 'table_pfr_team-year_game-logs_team-year-regular-season-game-log' # table ID for the HTML table in PFP
    team_df = pd.read_html(url, header=1, attrs={'id': table_id})[0]

    # Drop rows where the 'Rk' value is NaN and rename columns
    team_df = team_df.dropna(subset=['Rk'])
    team_df = team_df.rename(column_rename, axis=1)

    # Add 'team' prefix to game stat columns
    pre_dict = {col:f'{pfp_team.upper()}_{col}' for col in team_df.columns[11:]}
    team_df = team_df.rename(pre_dict, axis=1)

    # Get Opponent Gamelog Data
    table_id_opp = 'table_pfr_team-year_game-logs_team-year-regular-season-opponent-game-log' # table ID for the HTML table in PFP
    opp_df = pd.read_html(url, header=1, attrs={'id': table_id_opp})[0]

    # Drop rows where the 'Rk' value is NaN and rename columns
    opp_df = opp_df.dropna(subset=['Rk'])
    opp_df = opp_df.rename(column_rename, axis=1)

    # Add 'opps' prefix to game stat columns
    pre_dict_opp = {col:f'Opps_{col}' for col in opp_df.columns[11:]}
    opp_df = opp_df.rename(columns=pre_dict_opp)

    # Merge the two data frames
    cols_to_merge = team_df.columns[:11].tolist()

    # Merge based on the first eleven columns
    merged_df = pd.merge(team_df, opp_df, on=cols_to_merge)

    # Insert season and team as new columns
    merged_df.insert(loc=0, column='Season', value=season)
    merged_df.insert(loc=1, column='Team', value=pfp_team)

    # Concatenate the team gamelog to the aggregate data frame
    df = pd. concat([df, merged_df], ignore_index=True)

    # Pause to avoid breaking PFP Policies (no more than 10 requests in one minute)
    time.sleep(random.randint(8,12)) # randomly sleeps between 8 and 12 seconds


# Get the end time and print the time taken
end_time = time.time()

# Clean Dataset

# Drop RK column - not needed for analysis
df = df.drop(columns=['Rk'], axis=1)

# Convert 'Home' column to boolean
df['Location'] = np.where(df['Location'] ==' @', 'Away', 'Home')

# Convert 'Result' column to Win/Loss
df['Result'] = np.where(df['Result'] == 'W', 'W', 'L')

# Convert 'OT' column to boolean and ensure no records are empty
df['OT'] = np.where(df['OT'] == 'OT', 'True', 'False')

# Update data frame to include conference and division information
def get_conference_division(team_abbr):
    """
    Returns the conferenc eand division for the given team abbreviation.
    Handles relocation information for the Raiders, Chargers, and Rams.
    
    Args:
        team_abbr: Team abbreviations from PFR (e.g. GNB, CHI, DET)
        
    Returns:
        A tuble of conference and division or none if not found
    """
    
    for conference, divisions in nfl_conference_division.items():
        for division, teams in divisions.items():
            if team_abbr in teams:
                return conference, division
    return None, None

# Create lists to store conference and division information
opp_conference = []
opp_divisions = []

# Iterate through each opponent and get their conference and division
for opp in df['Opp']:
    # Ensure clean, uppercased opponent abbreviations
    opp_clean = opp.strip().upper()

    # Get conference and division
    conference, division = get_conference_division(opp_clean)

    # Append to lists
    opp_conference.append(conference)
    opp_divisions.append(division)

# Find the position of 'Result' Column to insert new column before
result_pos = df.columns.get_loc('Result')

# Insert new columns into data frame
df.insert(result_pos, 'Opp_Conference', opp_conference)
df.insert(result_pos, 'Opp_Division', opp_divisions)

# Display final data frame information and time taken
print(f"""

Final Result for {team} PFP data retrieval request for the {start_season} to {end_season} seasons:
{line_break}
""")
print(df.info())

print(f"""
Time Elapsed Information:
------------------------------------------
Elapsed time: {end_time - start_time:.2f} seconds
Average time per season: {(end_time - start_time)/len(seasons):.2f} seconds
""")

# Save data frame to CSV

csv_filename = f'{pfp_team.upper()}_PFP_{start_season}_to_{end_season}.csv'
df.to_csv(csv_filename, index=False)

# Notify user that file is saved
print(f""" 
{team} PFP request saved as {csv_filename}! 
""")
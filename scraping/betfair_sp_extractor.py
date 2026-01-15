# Import relevant packages
import matplotlib.pyplot as plt
import os
import bz2
import tarfile
import json
from datetime import datetime
import pandas as pd
import numpy as np
import re

# Step 1: Read and slightly alter dataframe including each PL match
results_df = pd.read_excel("../../../Darts SR/results.xlsx", index_col=False)
# Convert from "Surname, Forename" to "Forname Surname" (Betfair's entries are in this format)
results_df["home_bf"] = results_df["home"].apply(lambda x: f"{x.split(', ')[1]} {x.split(', ')[0]}")
results_df["away_bf"] = results_df["away"].apply(lambda x: f"{x.split(', ')[1]} {x.split(', ')[0]}")

# Step 2: Filter to only relevant paths

# First, filter based on whether a darts player is included
base_directory = 'BASIC'
correct_paths = [] # Paths that include one or more of the players. Match odds, 180 markets etc.
my_players = ['Luke Littler', 'Luke Humphries', 'Gerwyn Price', 'Stephen Bunting', 'Chris Dobey', 'Nathan Aspinall', 'Michael van Gerwen', 'Rob Cross']
player_ids = {} # Player names : player IDs
player_ids_list = [] # List of all player IDs
# Loop through every folder and file
for root, dirs, files in os.walk(base_directory):
    for file_name in files:
        if file_name.endswith(".json"):
            filepath = os.path.join(root, file_name)
            json_objects = []
            with open(filepath, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:  # Skip empty lines
                        try:
                            obj = json.loads(line)
                            json_objects.append(obj)
                        except json.JSONDecodeError as e:
                            print(f"Failed to parse line in {filepath}: {line[:100]}... Error: {e}")
                        for event in json_objects:
                            try:
                                runners = event["mc"][0]["marketDefinition"]["runners"]
                                for plur in runners:
                                    if plur["name"] in my_players:
                                        if filepath not in correct_paths:
                                            correct_paths.append(filepath)
                                        if plur["id"] not in player_ids_list:
                                            player_ids_list.append(plur["id"])
                                            player_ids[plur["id"]] = plur["name"]
                            except:
                                continue


# Next, filter darts betting events into match odds only (e.g. filter out 180 markets etc)
match_paths = []
for filepath in correct_paths:
    # Read each individual JSON
    json_objects = []
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:  # Skip empty lines
                try:
                    obj = json.loads(line)
                    json_objects.append(obj)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse line: {line[:100]}... Error: {e}")
    # Check each event type in the file. For match paths, all types should be match odds.
    types = []
    for event in json_objects:
        try:
            for mc in event["mc"]:
                mtype = mc["marketDefinition"]["marketType"]
                types.append(mtype)
        except:
            continue
    
    if all(t == "MATCH_ODDS" for t in types):
        match_paths.append(filepath)


# Step 3: Extract data for each specific match

# Create dictionaries including price and time for each match
events = {}
event_ids = []
for filepath in match_paths:
    json_objects = []
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line:  # Skip empty lines
                try:
                    obj = json.loads(line)
                    json_objects.append(obj)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse line: {line[:100]}... Error: {e}")

    # Create dictionary for each event
    for event in json_objects:
        try:
            id = event["mc"][0]["id"]
            type = event["mc"][0]["marketDefinition"]["marketType"]
            n_players = event["mc"][0]["marketDefinition"]["numberOfActiveRunners"]
            if id not in event_ids:
                event_ids.append(id)
                events[f"{id}"] = {}
                events[f"{id}"]["market_type"] = type
                events[f"{id}"]["n_players"] = n_players
                events[f"{id}"]["prices"] = {}
                events[f"{id}"]["starting_prices"] = {}
        except:
            continue

    # Fill dictionary of each event
    for event in json_objects:
        pt = event["pt"]
        e_id = event["mc"][0]["id"]
        try:
            rc = event["mc"][0]["rc"]
            for trade in rc:
                price = trade["ltp"]
                player = trade["id"]
                if player not in events[f"{e_id}"]["prices"]:
                    events[f"{e_id}"]["prices"][player] = {}
                    events[f"{e_id}"]["prices"][player]["time"] = []
                    events[f"{e_id}"]["prices"][player]["price"] = []
                events[f"{e_id}"]["prices"][player]["time"].append(pt)
                events[f"{e_id}"]["prices"][player]["price"].append(price)
        except (KeyError, IndexError, TypeError):
            continue

# Manually define Betfair IDs for each player (Rob Cross occurs twice due to a naming error)
player_ids = {43806063: 'Luke Littler',
     3538481: 'Stephen Bunting',
     9301981: 'Nathan Aspinall',
     2475370: 'Michael van Gerwen',
     8343339: 'Gerwyn Price',
     8346579: 'Chris Dobey',
     16199917: 'Luke Humphries',
     79884799: 'Rob Cross',
     10858418: 'Rob Cross'}

# Step 4: Find starting prices for each player in each match

# Function that returns string in lower case without spaces. Accounts for subtle typing errors.
def normalize(s):
    return re.sub(r'[^a-zA-Z]', '', s).lower()


home_bsp = []
away_bsp = []
for index, row in results_df.iterrows():
    home_player = row["home_bf"]
    away_player = row["away_bf"]
    #print(f"Fixture: {home_player} vs {away_player}")
    filtered_paths = []
    date = row["date"]
    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    year_string = date_obj.strftime('%Y')
    month_string = date_obj.strftime('%b')
    day_string = date_obj.day

    # Filter through all paths for the correct one
    for path in match_paths:
        if f"BASIC\\{year_string}\\{month_string}\\{day_string}\\" in path:
            filtered_paths.append(path)
            
    # There should be 7 matches (paths) per week
    if len(filtered_paths) != 7:
        print(f"ERROR. Date: {date}, number of files: {len(filtered_paths)}")

    
    for filepath in filtered_paths:
        correct_path = None
        #Open file
        json_objects = []
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line:  # Skip empty lines
                    try:
                        obj = json.loads(line)
                        json_objects.append(obj)
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse line: {line[:100]}... Error: {e}")
                        
        # Search JSON file for player names
        match_players = []
        for event in json_objects:
            try:
                for mc in event['mc']:
                    runners = event['mc'][0]['marketDefinition']['runners']
                    for player in runners:
                        name = player['name']
                        if name not in match_players:
                            match_players.append(name)
            except:
                continue
        #print(f"{match_players}, Home: {home_player}, Away: {away_player}")
        
        # Check if home and away players are in 
        normalized_home = normalize(home_player)
        normalized_away = normalize(away_player)
        normalized_matches = [normalize(name) for name in match_players]
        
        if (normalized_home in normalized_matches) and (normalized_away in normalized_matches):
            correct_path = filepath
            #print(f"Correct path found: {correct_path}")
            break
    
    # Use the correct path
    temp_filename = correct_path.split("\\")[-1]
    code = temp_filename.split(".json")[0]
    
    # Find times that the event is "inplay"
    inply_times = []
    for event in json_objects:
        try:
            inply = event["mc"][0]["marketDefinition"]["inPlay"]
        except:
            inply = False
        if inply:
            inply_times.append(event["pt"])
    # Sort times that are inplay and pick the lowest as the start time.
    sorted_datetimes = sorted(
        [datetime.fromtimestamp(ts / 1000) for ts in inply_times]
    )
    start_time = sorted_datetimes[0] # Normal time
    start_time_pt= min(inply_times) # Precise time in timestamp form

    # Loop through price vs time data and hence find the starting price
    specific_event = events[f"{code}"]
    for player in specific_event['prices']:
        prices = specific_event['prices'][player]['price']
        times = specific_event['prices'][player]['time']
        highest_time = 0
        for i in range(len(prices)):
            if times[i] < start_time_pt and times[i] > highest_time:
                highest_time = times[i]
                index = i
        bsp = prices[index]
        # Append starting price to either home or away
        if player_ids[player] == row["home_bf"]:
            home_bsp.append(bsp)
        elif player_ids[player] == row["away_bf"]:
            away_bsp.append(bsp)
        else:
            print(f"Error, filepath: {filepath}")

# Add a column for starting price
results_df["home_sp"] = home_bsp
results_df["away_sp"] = away_bsp

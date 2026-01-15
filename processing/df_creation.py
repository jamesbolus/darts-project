import requests
import json
import pandas as pd
import time
import os
import numpy as np
from datetime import datetime, timezone


def create_new_df_simple():
    # Remove and create new processed_tournaments file
    processed_file = "processed_tournaments.txt"
    if os.path.exists(processed_file):
        os.remove(processed_file)
    
    # Create a new empty file
    with open(processed_file, "w") as f:
        f.write("") 

    k = 1
    all_tournaments = os.listdir("../data")
    
    def treb_rate(stats, number):
        attempts = stats[number]["attempts"]
        return stats[number]["successes"] / attempts if attempts > 0 else 0
    
    scoring_segments = [20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 0, 50]
    
    scoring_misses = {1:20, 2:17, 3:19, 4:18,
                      5:20, 6:13, 7:19, 8:16, 9:14, 25:50}
    
    def treb_detect(score, hit, multiplier):
        """
        Returns (score, is treble attempt, is treble success)
        """
        if score > 60:
            if hit in scoring_segments:
                if multiplier == 3:
                    return(score-hit*multiplier, 1, 1)
                else:
                    return(score-hit*multiplier, 1, 0)
            else:
                return(score-hit*multiplier, 1, 0)
        else:
            return(score-hit*multiplier, 0, 0)
    
    
    for tournament in all_tournaments:
        games_list = os.listdir(f"../data/{tournament}")
        games_list = [f for f in games_list if not f.endswith(".csv")]
        
        for fixture in games_list:
            # Read file            
            with open(f"../data/{tournament}/{fixture}", 'r') as file:
                js = json.load(file)
    
            # Match code
            match_code = fixture.replace(".json", "")
    
            home_legs = js['sport_event_status']['home_score']
            away_legs = js['sport_event_status']['away_score']
                
            # Date
            try:
                # if it's just like "8 August"
                raw_date = js["sport_event"]["date"].replace(", ", "")
                raw_time = js["sport_event"].get("start_time", "00:00")  # fallback to midnight if missing
                
                # Combine into one string (add dummy year)
                raw = f"{raw_date} 2025 {raw_time}"
                
                # Parse both date and time
                dt = datetime.strptime(raw, "%d %B %Y %H:%M")
                dt = dt.replace(tzinfo=timezone.utc)  # make it UTC-aware
            except:
                raw_date = js["sport_event"]["start_time"]
                dt = datetime.fromisoformat(raw_date)
                if dt.tzinfo is None:  # if naive, force UTC
                    dt = dt.replace(tzinfo=timezone.utc)
                else:  # normalize to UTC
                    dt = dt.astimezone(timezone.utc)
            
            # Store both
            date_sort = dt
            date = dt.strftime("%#d %B")   # Windows-safe (e.g., "8 August")
       
    
            # Competition
            comp = tournament
    
            tl = js["timeline"]
    
            # Players
            home = js['sport_event']['competitors'][0]['name']
            away = js['sport_event']['competitors'][1]['name']
    
            # Calculate throw
            for event in tl:
                if event["type"] == "dart":
                    first_throw = event["competitor"]
                    throw = 0 if first_throw == "home" else 1
                    break
                    
            if not throw:
                for event in tl:
                    if event["type"] == "score_change":
                        throw = 0 if event["away_score"] == 501 else 1
                        break
    
            
            # T20, 19 and 18 percent
            js_type = 0 if any(event["type"] == "dart" for event in tl) else 1
            
            if js_type:
                # Code for only score change data
                pass
                
            
            else:
                # Code for dart data
                home_score = 501
                away_score = 501
                home_treb_attempt = 0
                home_treb_success = 0
                away_treb_attempt = 0
                away_treb_success = 0      
            
            
                # Loop through every event
                for event in tl:
                    if event["type"] == "score_change":
                        home_score = event["home_score"]
                        away_score = event["away_score"]
                    elif event["type"] == "leg_score_change":
                        home_score = 501
                        away_score = 501
                    elif event["type"] == "dart":
                        thrower = event["competitor"]
                        # Scoring darts
                        if thrower == "home":
                            home_score, is_at, is_suc = treb_detect(home_score, event["dart_score"], event["dart_score_multiplier"])
                            home_treb_attempt += is_at
                            home_treb_success += is_suc
                        elif thrower == "away":
                            away_score, is_at, is_suc = treb_detect(away_score, event["dart_score"], event["dart_score_multiplier"])
                            away_treb_attempt += is_at
                            away_treb_success += is_suc

                treb_rate_home = home_treb_success/home_treb_attempt
                treb_rate_away = away_treb_success/away_treb_attempt

                # Statistics
                home_stats_all = js['statistics']['totals']['competitors'][0]['statistics']
                away_stats_all = js['statistics']['totals']['competitors'][1]['statistics']

                # Check pcnt
                try:
                    home_check_pcnt = home_stats_all['checkout_percentage']
                    away_check_pcnt = away_stats_all['checkout_percentage']
                except:
                    home_check_pcnt = None
                    away_check_pcnt = None

                # 3 Dart average
                try:
                    home_3da = home_stats_all['average_3_darts']
                    away_3da = away_stats_all['average_3_darts']
                except:
                    home_3da = None
                    away_3da = None

                # checkouts
                try:
                    home_checkouts = home_stats_all['checkouts']
                    away_checkouts = away_stats_all['checkouts']
                except:
                    home_checkouts = None
                    away_checkouts = None
                
                # darts at double
                try:
                    home_darts_at_dbl = home_stats_all['darts_at_dbl']
                    away_darts_at_dbl = away_stats_all['darts_at_dbl']
                except:
                    home_darts_at_dbl = None
                    away_darts_at_dbl = None
                
                # checkouts 100s plus
                try:
                    home_checkouts_100s_plus = home_stats_all['checkouts_100s_plus']
                    away_checkouts_100s_plus = away_stats_all['checkouts_100s_plus']
                except:
                    home_checkouts_100s_plus = None
                    away_checkouts_100s_plus = None
                
                # highest checkout
                try:
                    home_highest_checkout = home_stats_all['highest_checkout']
                    away_highest_checkout = away_stats_all['highest_checkout']
                except:
                    home_highest_checkout = None
                    away_highest_checkout = None
                
                # scores 100s plus
                try:
                    home_scores_100s_plus = home_stats_all['scores_100s_plus']
                    away_scores_100s_plus = away_stats_all['scores_100s_plus']
                except:
                    home_scores_100s_plus = None
                    away_scores_100s_plus = None
                
                # scores 140s plus
                try:
                    home_scores_140s_plus = home_stats_all['scores_140s_plus']
                    away_scores_140s_plus = away_stats_all['scores_140s_plus']
                except:
                    home_scores_140s_plus = None
                    away_scores_140s_plus = None
                
                # scores 180s
                try:
                    home_scores_180s = home_stats_all['scores_180s']
                    away_scores_180s = away_stats_all['scores_180s']
                except:
                    home_scores_180s = None
                    away_scores_180s = None
                    

                winner = 0 if home_legs > away_legs else 1                
                
                
                # Rows
                new_row = {
                            "filename": match_code,
                            "date": date,
                            "date_sort": date_sort,
                            "home": home,
                            "away": away,
                            "winner": winner,
                            "home_score": home_legs,
                            "away_score": away_legs,
                            "competition": comp,
                            "throw": throw,
                        
                            # Home stats
                            "home_checkout_percentage": home_check_pcnt,
                            "home_treb_rate": treb_rate_home,
                            "home_3da": home_3da,
                            "home_treb_attempt": home_treb_attempt,
                            "home_treb_success": home_treb_success,
                            "home_checkouts": home_checkouts,
                            "home_darts_at_dbl": home_darts_at_dbl,
                            "home_checkouts_100s_plus": home_checkouts_100s_plus,
                            "home_highest_checkout": home_highest_checkout,
                            "home_scores_100s_plus": home_scores_100s_plus,
                            "home_scores_140s_plus": home_scores_140s_plus,
                            "home_scores_180s": home_scores_180s,
                        
                            # Away stats
                            "away_checkout_percentage": away_check_pcnt,
                            "away_treb_rate": treb_rate_away,
                            "away_3da": away_3da,
                            "away_treb_attempt": away_treb_attempt,
                            "away_treb_success": away_treb_success,
                            "away_checkouts": away_checkouts,
                            "away_darts_at_dbl": away_darts_at_dbl,
                            "away_checkouts_100s_plus": away_checkouts_100s_plus,
                            "away_highest_checkout": away_highest_checkout,
                            "away_scores_100s_plus": away_scores_100s_plus,
                            "away_scores_140s_plus": away_scores_140s_plus,
                            "away_scores_180s": away_scores_180s,
                        }


                if k == 1:
                    df = pd.DataFrame([new_row])
                else:
                    new_df = pd.DataFrame([new_row])
                    df = pd.concat([df, new_df], ignore_index=True)
                
                k += 1
    
    
        
        
        with open("processed_tournaments.txt", "a") as file:
            file.write(f"{tournament}.\n")
                
    df["date_sort"] = pd.to_datetime(df["date_sort"], errors="coerce")
    df["date_sort"] = df["date_sort"].dt.tz_localize(None)

    
    # Sort by date and save as excel
    df = df.sort_values("date_sort").reset_index(drop=True)
    df.to_excel("df_simple.xlsx", index=False)

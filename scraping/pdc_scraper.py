from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup

import datetime
import json
import os
import re
import time
import pandas as pd
import numpy as np
import csv
from datetime import datetime

# Define dictionaries used for data mapping
data_points = ['Averages (3 darts)', '100+ thrown', '140+ thrown', '180 thrown', 
               'Highest checkout', 'Checkouts 100+', 'Checkout percentage', 'Checkouts']

data_points_mapping = {'Averages (3 darts)': 'average_3_darts',
                       '100+ thrown': 'scores_100s_plus',
                       '140+ thrown': 'scores_140s_plus',
                       '180 thrown': 'scores_180s',
                       'Highest checkout': 'highest_checkout',
                       'Checkouts 100+': 'checkouts_100s_plus',
                       'Checkout percentage': 'checkout_percentage',
                       'Checkouts': 'checkouts'}

# Define dictionaries to store data in
sample_dict = {
    "sport_event": {
        "id": None,
        "date": None,
        "start_time": None,
        "sport_event_context": {
            "category": {"name": None, "id": None},
            "competition": {"id": None, "name": None},
            "round": {"name": None}
        },
        "competitors": [
            {"id": None, "name": None, "abbreviation": None, "qualifier": "home"},
            {"id": None, "name": None, "abbreviation": None, "qualifier": "away"}
        ]
    },

    "sport_event_status": {
        "home_score": None,
        "away_score": None,
        "winner": None,
        "winner_id": None
    },

    "statistics": {
        "totals": {
            "competitors": [
                {
                    "id": None,
                    "name": None,
                    "abbreviation": None,
                    "qualifier": "home",
                    "statistics": {
                        "average_3_darts": None,
                        "checkout_percentage": None,
                        "checkouts": None,
                        "darts_at_dbl": None,
                        "checkouts_100s_plus": None,
                        "highest_checkout": None,
                        "scores_100s_plus": None,
                        "scores_140s_plus": None,
                        "scores_180s": None
                    }
                },
                {
                    "id": None,
                    "name": None,
                    "abbreviation": None,
                    "qualifier": "away",
                    "statistics": {
                        "average_3_darts": None,
                        "checkout_percentage": None,
                        "checkouts": None,
                        "darts_at_dbl": None,
                        "checkouts_100s_plus": None,
                        "highest_checkout": None,
                        "scores_100s_plus": None,
                        "scores_140s_plus": None,
                        "scores_180s": None
                    }
                }
            ]
        }
    }                
}

dart_temp = {"type": "dart", "competitor": None, 
            "dart_score": None, "dart_score_multiplier": None,
            "dart_score_total": None, "is_checkout_attempt": None,
            "is_bust": None}

score_change_temp = {"type": "score_change", "home_score": None, "away_score": None}

leg_change_temp = {"type": "leg_score_change", "competitor": None, "home_score": None, "away_score": None}

# Define functions used to process data
def parse_darts(throw_text: str, n):
    a = [
        d.replace(")", "").replace("|", "").strip()
        for d in throw_text.split("(")[n].split("|")
    ]
    return a

def check_dart(dart):
    if "T" in dart:
        multiplier = 3
        number = int(dart[1:])
    elif "D" in dart:
        multiplier = 2
        number = int(dart[1:])
    elif dart == "Miss":
        multiplier = 0
        number = 0
    else:
        multiplier = 1
        number = int(dart)
    return(number, multiplier)

def name_split(name):
    parts = name.split()
    forename = parts[0]
    surname = " ".join(parts[1:])
    new_name = f"{surname}, {forename}"
    return new_name

def pdc_scrape(days_back, days_scraped):
  driver = webdriver.Chrome()
  # Open the page
  driver.get("https://www.pdc.tv/live-scores")
  time.sleep(2)
  # Handle cookies popup first
  try:
      consent_button = WebDriverWait(driver, 10).until(
          EC.element_to_be_clickable((By.CSS_SELECTOR, "button[mode='primary']"))
      )
      consent_button.click()
      print("Cookie banner closed")
  except:
      print("No cookie banner appeared")
  
  # Scroll back a number of days
  for i in range(days_back):
      # Switch days
      switcher_button = WebDriverWait(driver, 15).until(
          EC.element_to_be_clickable((By.CSS_SELECTOR, ".sr-switcher__wrapper > div:nth-child(1)"))
      )
      driver.execute_script("arguments[0].click();", switcher_button)
      print("Switcher button clicked")
      time.sleep(1.6)

  for j in range(days_scraped):
      # Check if there are matches on this day. If there are, create a list of them all
      try:
          matches = WebDriverWait(driver, 10).until(
              EC.presence_of_all_elements_located(
                  (By.CSS_SELECTOR, ".sr-match__container.srt-base-1-is-hoverable.srm-is-clickable")
              )
          )
          print(f"Found {len(matches)} matches")
      except TimeoutException:
          matches = []
          print("No matches available today")
      
      m_num = 0
      
      # Loop through each match
      for match in matches:
          # Load empty dictionary for match data
          match_dict = sample_dict.copy()
          
          # Scroll into view
          driver.execute_script("arguments[0].scrollIntoView(true);", match)
          time.sleep(1)
      
          # Click match
          driver.execute_script("arguments[0].click();", match)
          time.sleep(4)
      
          # Read html data
          soup = BeautifulSoup(driver.page_source, features="html.parser")
      
          # Full date
          match_date = soup.find("span", class_="sr-lmt-0-ms-date__date-date-month")
          try:
              match_dict["sport_event"]["date"] = match_date.text
          except:
              match_dict["sport_event"]["date"] = None
      
          # Home and away player names
          team1_div = soup.find("div", class_="sr-lmt-plus-scb__teams srm-team1")
          home_player = team1_div.find("div", class_="sr-lmt-plus-scb__team-name").text.strip()
          team2_div = soup.find("div", class_="sr-lmt-plus-scb__teams srm-team2")
          away_player = team2_div.find("div", class_="sr-lmt-plus-scb__team-name").text.strip()
  
          # Check for error
          error_msg = soup.find("div", class_="sr-error__container srt-base-1")
          if error_msg:
              print(f"Error: {home_player} vs {away_player}")
              continue
      
          # Home and away final legs
          score_div = soup.find("div", class_="sr-lmt-plus-scb__result srm-hasServiceIndicator")
          if score_div:
              home_final_legs = int(score_div.find("div", class_="srm-team1").text)
              away_final_legs = int(score_div.find("div", class_="srm-team2").text)
          else:
              home_final_legs = None
              away_final_legs = None
      
          # Note competitors, final legs and winner
          match_dict["sport_event"]["competitors"][0]["name"] = name_split(home_player)
          match_dict["sport_event"]["competitors"][1]["name"] = name_split(away_player)
          
          match_dict["sport_event_status"]["home_score"] = home_final_legs
          match_dict["sport_event_status"]["away_score"] = away_final_legs
          
          match_dict["sport_event_status"]["winner"] = "home" if home_final_legs > away_final_legs else "away"
      
          # Category
          cat_name = soup.find("div", class_="sr-ml-list__realcategory-name")
          if cat_name:
              match_dict["sport_event"]["sport_event_context"]["category"]['name'] = cat_name.text
          else:
              match_dict["sport_event"]["sport_event_context"]["category"]['name'] = None
      
          # Competition name
          comp_name = soup.find("span", class_="sr-lmt-setsport-ms-title__title-item sr-lmt-setsport-ms-title__tournament-name")
          raw_name = comp_name.get_text(strip=True)
          clean_name = re.sub(r'[<>:"/\\|?*]', '', raw_name)
          clean_name = clean_name.replace("\xa0", " ").strip()
          
          try:
              match_dict["sport_event"]["sport_event_context"]["competition"]['name'] = clean_name.text
          except:
              match_dict["sport_event"]["sport_event_context"]["competition"]['name'] = None
      
          # Make folder for comp if it does not exist
          folder_path = os.path.join("data", clean_name)
          os.makedirs(folder_path, exist_ok=True)
      
          # Make CSV file if it does not exist.
          csv_path = os.path.join(folder_path, "summary.csv")
      
          if not os.path.exists(csv_path):
              with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
                  writer = csv.writer(f)
                  writer.writerow(["match_code", "home", "away", "date", "n_statistics", "tl_length"])
      
          # Match Date
          match_date = soup.find("span", class_="sr-lmt-0-ms-date__date-date-month")
          raw_date = match_date.text.strip().lstrip(",").strip()
          day_month = datetime.strptime(raw_date, "%d %B")
          
          # Start time
          start_time = soup.find("span", class_="sr-lmt-0-ms-date__date-time")
          if start_time:
              match_dict["sport_event"]["start_time"] = start_time.text
          else:
              match_dict["sport_event"]["start_time"] = None
      
          # Copy match statistics
          divs = soup.find_all("div", attrs={"class": "sr-lmt-plus-0-hor-chart__top"})
          for div in divs:
              name = div.find("div", class_="sr-lmt-plus-0-hor-chart__title srt-text-secondary srm-is-uppercase").text.strip()
              match_dict['statistics']['totals']['competitors'][0]['statistics'][data_points_mapping[f"{name}"]] = div.find("div", class_="sr-lmt-plus-0-hor-chart__display-value srm-left srm-is-bold srm-top").text.strip()
              match_dict['statistics']['totals']['competitors'][1]['statistics'][data_points_mapping[f"{name}"]] = div.find("div", class_="sr-lmt-plus-0-hor-chart__display-value srm-right srm-is-bold srm-top").text.strip()
      
          
          # Find timeline button and click
          button = WebDriverWait(driver, 10).until(
              EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test-tab='timeline']"))
          )
          driver.execute_script("arguments[0].scrollIntoView(true);", button)
          time.sleep(1)
          driver.execute_script("arguments[0].click();", button)
          time.sleep(4)
      
          # Read new page soup
          soup = BeautifulSoup(driver.page_source, features="html.parser")
          
          # Make list of all timeline events
          tl_divs = soup.find("div", class_ = "sr-lmt-plus-pbp__content srt-base-1")
          tl_events = tl_divs.find_all("li", class_ = "sr-lmt-plus-pbp-rowdarts__wrapper")
      
          timeline = [] # Create empty timeline
      
          # Loop through each event
          for ev in reversed(tl_events):
              # Check if event is a throw
              throw = ev.find("div", class_="sr-lmt-plus-pbp-rowdarts__points")
              if throw:
                  home_throw = ev.find("div", class_="sr-lmt-plus-pbp-rowdarts__points srm-home")
                  away_throw = ev.find("div", class_="sr-lmt-plus-pbp-rowdarts__points srm-away")
                  leg = ev.find("span", class_="sr-lmt-plus-pbp-rowdarts__text-leg-won")
      
                  # Entry must be split at a different point if it is a leg entry
                  split_index = 2 if leg else 1
                  try:
                      darts = [
                          d.replace(")", "").replace("|", "").strip()
                          for d in throw.text.split("(")[split_index].split("|")
                      ]
                      darts = list(filter(None, darts))
                  except:
                      darts = []
              
                  # Record who is throwing
                  if leg:
                      player = "home" if home_throw else "away"
                      
                      # Record the leg change
                      leg_change = ev.find("div", class_="sr-lmt-plus-pbp-rowdarts__leg-won")
                      home_legs, away_legs = list(map(int, re.findall(r"\d+", leg_change.text)))
                      current_leg_change = leg_change_temp.copy()
                      current_leg_change["competitor"] = player
                      current_leg_change["home_score"] = home_legs
                      current_leg_change["away_score"] = away_legs
                      
                  elif home_throw:
                      player = "home"
                      
                  elif away_throw:
                      player = "away"
                      
                  # Loop through each dart in entry.
                  for dart in darts:
                      individ_temp = dart_temp.copy()
                      number, multiplier = check_dart(dart)
                      individ_temp["competitor"] = player
                      individ_temp["dart_score"] = number
                      individ_temp["dart_score_multiplier"] = multiplier
                      individ_temp["dart_score_total"] = number*multiplier
                      timeline.append(individ_temp)
          
                  # Score change
                  score = ev.find("div", class_="sr-lmt-plus-pbp-rowdarts__score")
                  if score:
                      current_score_change = score_change_temp.copy()
                      home_score, away_score = score.text.split("-")
                      current_score_change["home_score"] = int(home_score.strip())
                      current_score_change["away_score"] = int(away_score.strip())
                      timeline.append(current_score_change)
          
                  # Record leg score change after as this is how data is formatted
                  if leg:
                      timeline.append(current_leg_change)
      
          
          # Record finished timeline
          match_dict["timeline"] = timeline
      
          # Reformat checkouts
          try:
              match_dict["statistics"]["totals"]['competitors'][0]['statistics']['darts_at_dbl'] = match_dict["statistics"]["totals"]['competitors'][0]['statistics']['checkouts'].split("/")[1]
              match_dict["statistics"]["totals"]['competitors'][0]['statistics']['checkouts'] = match_dict["statistics"]["totals"]['competitors'][0]['statistics']['checkouts'].split("/")[0]
              match_dict["statistics"]["totals"]['competitors'][1]['statistics']['darts_at_dbl'] = match_dict["statistics"]["totals"]['competitors'][1]['statistics']['checkouts'].split("/")[1]
              match_dict["statistics"]["totals"]['competitors'][1]['statistics']['checkouts'] = match_dict["statistics"]["totals"]['competitors'][1]['statistics']['checkouts'].split("/")[0]
          
              # Remove % from checkout percentage
              match_dict["statistics"]["totals"]['competitors'][0]['statistics']['checkout_percentage'] = match_dict["statistics"]["totals"]['competitors'][0]['statistics']['checkout_percentage'].strip("%")
              match_dict["statistics"]["totals"]['competitors'][1]['statistics']['checkout_percentage'] = match_dict["statistics"]["totals"]['competitors'][1]['statistics']['checkout_percentage'].strip("%")
  
          except:
              match_dict["statistics"]["totals"]['competitors'][0]['statistics']['darts_at_dbl'] = None
              match_dict["statistics"]["totals"]['competitors'][0]['statistics']['checkouts'] = None
              match_dict["statistics"]["totals"]['competitors'][1]['statistics']['darts_at_dbl'] = None
              match_dict["statistics"]["totals"]['competitors'][1]['statistics']['checkouts'] = None
  
              
          # Save match dictionary as JSON
          match_code = f"{day_month.day:02d}{day_month.month:02d}{m_num:02d}"
          json_path = os.path.join(folder_path, match_code)
          with open(f"{json_path}.json", "w") as f:
              json.dump(match_dict, f, indent=4)
      
          # Update csv summary with match stats
          with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
              writer = csv.writer(f)
              writer.writerow([match_code, home_player, away_player, match_date.text, len(divs), len(timeline)])
              
      
          m_num += 1
      
          print(f"Match recorded: {home_player} vs {away_player}")
  
      # Switch days
      switcher_button = WebDriverWait(driver, 15).until(
          EC.element_to_be_clickable(
              (By.CSS_SELECTOR, ".sr-switcher__wrapper > div:nth-child(1)")
          )
      )
      driver.execute_script("arguments[0].click();", switcher_button)
      print("Switcher button clicked")
      time.sleep(1.6)

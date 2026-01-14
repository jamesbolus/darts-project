import numpy as np
import random

# Create target dictionaries for each score
target3 = {}
for i in range(61, 502):
    target3[i] = (20, "T")
for i in range(41, 61):
    target3[i] = (int(i-40), "S")
for i in range(2, 41, 2):
    target3[i] = (int(i/2), "D")
for i in range(3, 49, 2):
    target3[i] = (1, "S")
for i in range(171, 502):
    target3[i] = ("score", "T")

# Ideal doubles in order
ideals = [32, 40, 16, 24, 20, 36, 8, 28, 12, 30, 4, 38, 18, 14, 10, 34, 22, 2, 26, 6]
ideals.reverse()

# Aiming for number in ideals
for score in target3:
    for aim in ideals:
        if score not in ideals:
            for i in range(1, 21):
                if score-i == aim:
                    target3[score] = (i, 'S')
                elif score-(3*i) == aim:
                    target3[score] = (i, 'T')

target2 = target3.copy()
target1 = target3.copy()

# Logic for bull checks
bull_check = [110, 107, 104, 101]
for score in target2:
    for i in range(18, 21):
        if score-i in bull_check:
            target2[score] = (i, 'T')

def throw(score, tr, dr):
    """
    Simulates a player's 3 dart visit to the board.
    """
    inhand = 3
    checkout = 0
    original_score = score
    while inhand > 0 and checkout == 0:
        # Set the target based on current score and how many darts are in hand
        if inhand == 3:
            target_number, target_type = target3.get(score, (20, 'T'))
        elif inhand == 2:
            target_number, target_type = target2.get(score, (20, 'T'))
        elif inhand == 1:
            target_number, target_type = target1.get(score, (20, 'T'))
        elif inhand == 0:
            return(score, inhand, checkout)
        else:
            print("Error, inhand is not in range")

        r = random.random() # Generate random number to determine target
        p_switch = 0.25 # Probability of throwing at 19s rather than 20.
        if target_type == 'T':
            if target_number == "score":
                r2 = random.random() # Generate random number to determine what is hit
                target_number = 20 if r2 > p_switch else 19
            if r < tr:
                score -= target_number*3
            else:
                score -= target_number
            inhand -= 1
                
        elif target_type == 'D':
            if r < dr:
                score -= target_number*2
                if score == 0:
                    checkout = 1
            else:
                r3 = random.random()
                change = target_number if r3 > 0.5 else 0
                score -= change
                if score == 1:
                    score = 2
            inhand -= 1
    
        elif target_type == 'S':
            score -= target_number
            inhand -= 1
            
        if score < 0 or score == 1:
            return (original_score, 0)
    return (score, checkout)


def leg(start_throw, home_tr, home_dr, away_tr, away_dr):
    """
    Simulates a leg of darts.
    """
    turn = start_throw
    home_score = 501
    away_score = 501
    checkout = 0
    while checkout == 0:
        if turn == 0:
            home_score, checkout = throw(home_score, home_tr, home_dr)     
            turn = 1
            if checkout == 1:
                winner = 0
        elif turn == 1:
            away_score, checkout = throw(away_score, away_tr, away_dr)      
            turn = 0
            if checkout == 1:
                winner = 1
    return winner

def leg_match(best_of, home_tr, home_dr, away_tr, away_dr, start_throw):
    """
    Simulates a leg format darts match.
    """
    next_throw = start_throw
    win_score = int((best_of+1)/2)
    home_legs = 0
    away_legs = 0

    while max(home_legs, away_legs) < win_score:
        winner = leg(next_throw, home_tr, home_dr, away_tr, away_dr) # Simulate 1 leg
        next_throw = 1 if next_throw == 0 else 0 # Update for next throw
        # Update scores
        if winner == 0:
            home_legs += 1
        elif winner == 1:
            away_legs += 1
            
    score = f"{home_legs} - {away_legs}"
    if home_legs > away_legs:
        match_winner = 0
    elif away_legs > home_legs:
        match_winner = 1

    return (score, match_winner)

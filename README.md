# GridironMetrics-CFB

A fast football data tool that reads raw game files and instantly turns them into useful stats for coaches. 

Instead of looking at basic box scores, this tool breaks down every single play to show how efficient an offense is under real game pressure.

---

## 🏈 Core Analytics Capabilities

### 1. Situational Success Rates
This tracks if a play actually kept the offense on schedule based on coaching standards:
*   **1st Down:** Successful if the play gains at least half of the yards needed.
*   **2nd Down:** Successful if the play gains at least 70% of the yards needed.
*   **3rd & 4th Down:** Successful only if the play picks up the first down.

### 2. Big-Play Tracking (Explosive Plays)
The tool automatically highlights chunk plays that shift field positioning:
*   **Passing Plays:** Any pass that gains 15 or more yards.
*   **Rushing Plays:** Any run that gains 10 or more yards.

### 3. Opponent Quality Weighting
A successful play against a top-tier defense matters more than a successful play against a weak opponent. The tool automatically adjusts the final success score based on how talented the opponent's roster is.

### 4. Play-Calling Tendencies
Automatically calculates down-by-down run/pass ratios so coaches can instantly see team tendencies on 1st down and critical 3rd downs.

---

## 🛠️ How the Data Flows

```text
[Get Live Game Data] -> [Save Raw Files] -> [Run Math Filters] -> [Print Stats Report]
```

---

## 🚀 Example Data Output

When you run the tool, it instantly reads the game data, runs the math, and prints out a clean row-by-row confirmation log like this:

```text
Initializing GridironMetrics-CFB Analytics Engine...

--- Pipeline Transformation Matrix ---
Successfully loaded 6 raw play rows into DataFrame.
Raw Success Rate:             50.0%
Talent-Adjusted Success Index: 31.2
Total Explosive Plays Created: 1

--- Coaching Tendency Breakdown ---
1st Down Play-Calling: Run: 66.7% (2) | Pass: 33.3% (1)
3rd Down Play-Calling: Run: 0.0% (0) | Pass: 100.0% (1)

--- Detailed Play Inspection Log ---
Play 1: Run | Down: 1 | Dist: 10 | Yds Gained: 6 | Success: True | Explosive: False
Play 2: Run | Down: 1 | Dist: 10 | Yds Gained: 2 | Success: False | Explosive: False
Play 3: Pass | Down: 1 | Dist: 10 | Yds Gained: 12 | Success: True | Explosive: False
Play 4: Pass | Down: 2 | Dist: 8 | Yds Gained: 3 | Success: False | Explosive: False
Play 5: Pass | Down: 3 | Dist: 4 | Yds Gained: 16 | Success: True | Explosive: True
Play 6: Run | Down: 4 | Dist: 2 | Yds Gained: 1 | Success: False | Explosive: False
```

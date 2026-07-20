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
A successful play against a top-tier defense matters more than a successful play against a weak opponent(Ex: A 3rd & 5 conversion vs Ohio State is more meaningful than one against UConn). The tool automatically adjusts the final success score based on how talented the opponent's roster is.

---

## 🛠️ How the Data Flows

```text
[Get Live Game Data] -> [Save Raw Files] -> [Run Math Filters] -> [Print Stats Report]
```

---

## 🚀 Example Data Output

When you run the tool, it instantly reads the game data, runs the math, and prints out a clean row-by-row confirmation log like this:

Initializing GridironMetrics-CFB Analytics Engine...

--- Pipeline Transformation Matrix ---
Successfully loaded 4 raw play rows into DataFrame.
Raw Success Rate:             50.0%
Talent-Adjusted Success Index: 31.2
Total Explosive Plays Created: 1

--- Detailed Play Inspection Log ---
Play 1: Run | Dn: 1 | Dist: 10 | Yds Gained: 6 | Success: True | Explosive: False
Play 2: Pass | Dn: 2 | Dist: 8 | Yds Gained: 3 | Success: False | Explosive: False
Play 3: Pass | Dn: 3 | Dist: 4 | Yds Gained: 16 | Success: True | Explosive: True
Play 4: Run | Dn: 4 | Dist: 2 | Yds Gained: 1 | Success: False | Explosive: False
```

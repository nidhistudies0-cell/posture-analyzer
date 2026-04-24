# Posture Analyzer — Gym Tracker

A real-time posture analysis and gym tracking tool built with Python, MediaPipe, and OpenCV.

---

## What this project does

- Detects body landmarks in real time using your webcam
- Calculates joint angles using dot product vector mathematics
- Classifies posture as **GOOD / ADJUST SLIGHTLY / BAD** per joint
- Counts gym reps and detects UP/DOWN stage for 10 exercises
- Gives a live multi-joint form score out of 100
- Detects hunchback posture while sitting at a desk
- Alerts you after sustained bad posture (3–5 seconds)
- Switch between **GYM mode** and **SITTING mode** with one key press
- Cycle through all 10 exercises with A / D keys

---

## The math behind it

This is the core of the entire project. Every posture decision comes from this formula.

Given three joint coordinates A, B, C — where B is the joint being measured:

```
Vector AB = (Ax - Bx, Ay - By)
Vector CB = (Cx - Bx, Cy - By)

Dot product = AB · CB = (ABx × CBx) + (ABy × CBy)

cos θ = (AB · CB) / (|AB| × |CB|)

θ = arccos(cos θ) × (180 / π)
```

**Example from original paper:**
- A(2,3), B(5,7), C(9,6)
- AB = (3, 4), CB = (-4, 1)
- Dot product = -8
- |AB| = 5, |CB| ≈ 4.123
- cos θ ≈ -0.388
- θ ≈ **112.8° → GOOD POSTURE**

---

## Project structure

```
posture_analyzer/
│
├── main.py           # Webcam loop, mode switching, exercise router, UI overlay
├── angle_utils.py    # Dot product angle calculation (unchanged)
├── classifier.py     # Posture thresholds and form scoring for all exercises
├── README.md         # This file
└── .gitignore        # Excludes venv and cache files
```

---

## File-by-file explanation

### `angle_utils.py`
Contains one function: `calculate_angle(A, B, C)`.  
Takes three (x, y) coordinate tuples and returns the angle at joint B in degrees.  
**Unchanged from v1.**

### `classifier.py`
Contains three functions:

**`classify_posture(angle, joint)`**  
Compares the angle against thresholds for that specific joint/exercise key.  
Each exercise has dedicated joint keys (e.g. `"squat_knee_down"`, `"pushup_elbow_up"`) so thresholds shift correctly based on the movement phase.

**`get_form_score(angle, ideal)`**  
Returns a score 0–100 based on how close the actual angle is to the ideal.

**`get_multi_joint_score(*angle_ideal_pairs)`**  
Averages form scores across multiple joints. Used for exercises where two joints matter equally (e.g. push ups track both elbow and hip).

**`get_sitting_score(neck_angle, spine_angle)`**  
Unchanged from v1. Averages neck and spine scores for an overall sitting score.

### `main.py`
Opens the webcam, runs MediaPipe every frame, extracts landmark coordinates, routes to the correct exercise block, and draws the UI.

**Two modes — same S key to switch:**

| Mode | What it tracks |
|------|----------------|
| GYM | 10 exercises with rep counting and per-joint angle feedback |
| SITTING | Neck + spine alignment, hunch detection, sitting score |

---

## Exercises and thresholds

Thresholds for the 5 original exercises were calibrated from a dataset of 31,033 real exercise samples.  
The dataset percentiles used: p10/p25 → lower bound of GOOD, p75/p90 → upper bound of GOOD, just outside → ADJUST.

### Original exercises (dataset-calibrated)

| Exercise | Rep trigger joint | DOWN threshold | UP threshold | Dataset source |
|---|---|---|---|---|
| Squats | Knee | < 90° | > 160° | knee p25=84 (bottom), p75=177 (stand) |
| Push Ups | Elbow | < 90° | > 155° | elbow p25=83 (bottom), p75=169 (top) |
| Pull Ups | Elbow | hang > 150° → pull < 90° | — | elbow p25=61 (top), p75=174 (hang) |
| Jumping Jacks | Shoulder | < 25° | > 130° | shoulder p25=14 (down), p75=147 (up) |
| Russian Twists | Shoulder (side proxy) | < 10° | — | hip p50=52 (seat lean), knee p50=85 |

### New exercises (added v2)

| Exercise | Rep trigger | Key thresholds | What's checked |
|---|---|---|---|
| **Lunges** | Knee | DOWN < 105°, UP > 160° | Front knee 80–105° at bottom; hip 85–120° |
| **Plank** | Hold timer | Hip 160–180°, Elbow 155–180°, Knee 155–180° | Three joints checked simultaneously |
| **Bicep Curls** | Elbow | UP < 65°, DOWN > 155° | Elbow curl range; shoulder swing detected |
| **Shoulder Press** | Elbow | DOWN < 110°, UP > 155° | Elbow from ~90° start to full lockout |
| **Deadlift** | Hip | DOWN < 100°, UP > 160° | Hip hinge depth; knee soft bend monitored |

### Joint thresholds table (all keys in `classifier.py`)

| Key | GOOD range | ADJUST range | Used for |
|---|---|---|---|
| `squat_knee_down` | 70–100° | 100–120° | Squat bottom phase |
| `squat_knee_up` | 160–180° | 140–160° | Squat standing phase |
| `squat_hip` | 45–100° | 100–130° | Squat hip depth |
| `pushup_elbow_down` | 60–100° | 100–120° | Push up bottom |
| `pushup_elbow_up` | 155–180° | 130–155° | Push up top |
| `pushup_hip` | 155–180° | 130–155° | Plank body alignment |
| `pullup_elbow_up` | 20–90° | 90–120° | Pull up top position |
| `pullup_elbow_down` | 150–180° | 120–150° | Dead hang |
| `jack_shoulder_down` | 0–25° | 25–50° | Arms at side |
| `jack_shoulder_up` | 130–180° | 90–130° | Arms overhead |
| `jack_elbow` | 148–180° | 120–148° | Elbow straight |
| `twist_hip` | 30–90° | 90–140° | Torso lean |
| `twist_knee` | 60–120° | 40–60° | Knees bent |
| `lunge_knee_down` | 80–105° | 65–80° | Lunge bottom |
| `lunge_knee_up` | 160–180° | 140–160° | Lunge standing |
| `lunge_hip` | 85–120° | 120–145° | Hip alignment |
| `plank_hip` | 160–180° | 140–160° | Body flat |
| `plank_elbow` | 155–180° | 130–155° | Arms straight |
| `plank_knee` | 155–180° | 135–155° | Legs straight |
| `curl_elbow_up` | 30–65° | 65–85° | Curl top |
| `curl_elbow_down` | 155–180° | 130–155° | Arm extended |
| `curl_shoulder` | 0–30° | 30–50° | No swing |
| `press_elbow_up` | 155–180° | 130–155° | Press lockout |
| `press_elbow_down` | 80–110° | 60–80° | Start position |
| `deadlift_hip_down` | 45–100° | 100–130° | Hip hinge |
| `deadlift_hip_up` | 160–180° | 140–160° | Standing lockout |
| `deadlift_knee` | 100–150° | 80–100° | Knee soft bend |

---

## MediaPipe landmark indices used

| Body point | Index |
|---|---|
| Left ear | 7 |
| Left shoulder | 11 |
| Right shoulder | 12 |
| Left elbow | 13 |
| Right elbow | 14 |
| Left wrist | 15 |
| Left hip | 23 |
| Right hip | 24 |
| Left knee | 25 |
| Right knee | 26 |
| Left ankle | 27 |
| Right ankle | 28 |

Full landmark map: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker

---

## Controls

| Key | Action |
|---|---|
| `A` | Previous exercise (GYM mode) |
| `D` | Next exercise (GYM mode) |
| `R` | Reset rep counter / plank timer |
| `S` | Switch between GYM and SITTING mode |
| `Q` | Quit |

---

## Setup instructions

### Requirements
- Python **3.11.9** (MediaPipe does not support 3.12 or 3.13)
- A working webcam

### Step 1 — clone the repo
```
git clone https://github.com/YOURUSERNAME/posture-analyzer.git
cd posture-analyzer
```

### Step 2 — create a virtual environment with Python 3.11
```
py -3.11 -m venv venv311
```

### Step 3 — activate it

**Windows:**
```
venv311\Scripts\activate
```
**Mac/Linux:**
```
source venv311/bin/activate
```

### Step 4 — install libraries
```
pip install opencv-python mediapipe==0.10.9 numpy
```

### Step 5 — run the program
```
python main.py
```

### Troubleshooting

| Error | Fix |
|---|---|
| `module mediapipe has no attribute solutions` | Run `pip install mediapipe==0.10.9` |
| `Cannot open camera` | Change `VideoCapture(0)` to `VideoCapture(1)` in main.py |
| `ModuleNotFoundError` | Make sure venv311 is activated before running |
| Sitting mode not detecting | Turn sideways so camera sees your profile |
| Plank hold not starting | Hip angle must reach 160°+ — ensure full body is visible |

---

## How to add a new exercise

1. **Add thresholds** in `classifier.py` under the `thresholds` dict (e.g. `"myex_knee_down": {...}`)
2. **Add the exercise name** to `GYM_EXERCISES` list in `main.py`
3. **Add an `elif exercise == "MY EXERCISE":` block** in the GYM mode section of `main.py`:
   - Get the landmark coords with `get_coords()`
   - Calculate angles with `calculate_angle()`
   - Define the UP/DOWN rep-counting logic
   - Call `classify_posture()` with the right key
   - Call `draw_info_panel()` with your angle lines

The math never changes — only the joint indices and threshold keys do.

---

## Completed items (v2)

- [x] Add lunges rep counter (knee angle)
- [x] Add plank hold timer (hip + elbow + knee)
- [x] Add bicep curl rep counter (elbow angle + shoulder swing detection)
- [x] Add shoulder press rep counter (elbow angle)
- [x] Add deadlift rep counter (hip hinge angle)
- [x] Multi-joint form scoring for all exercises
- [x] Exercise cycle with A / D keys
- [x] Dataset-calibrated thresholds for all 5 original exercises

## Future improvements

- [ ] Save session data to CSV after each workout
- [ ] Generate a matplotlib graph of angle over time per exercise
- [ ] Add voice feedback using `pyttsx3`
- [ ] Build a simple tkinter UI to select exercise before starting
- [ ] Add left/right side switching for unilateral exercises (lunges, curls)
- [ ] Rep tempo tracking (time per rep)

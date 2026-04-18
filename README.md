# Posture Analyzer — Gym Tracker

A real-time posture analysis and gym tracking tool built with Python, MediaPipe, and OpenCV.  


---

## What this project does

- Detects body landmarks in real time using your webcam
- Calculates joint angles using dot product vector mathematics
- Classifies posture as **GOOD / ADJUST SLIGHTLY / BAD**
- Counts gym reps (squats) and detects UP/DOWN stage
- Gives a live form score out of 100
- Detects hunchback posture while sitting at a desk
- Alerts you after sustained bad posture (3–5 seconds)
- Switch between GYM mode and SITTING mode with one key press

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
├── main.py           # Webcam loop, mode switching, UI overlay
├── angle_utils.py    # Dot product angle calculation
├── classifier.py     # Posture thresholds and form scoring
├── README.md         # This file
└── .gitignore        # Excludes venv and cache files
```

---

## File-by-file explanation

### `angle_utils.py`
Contains one function: `calculate_angle(A, B, C)`.  
Takes three (x, y) coordinate tuples and returns the angle at joint B in degrees.  
This is a direct Python translation of the Java `findAngle()` method from the original project.

```python
import numpy as np

def calculate_angle(A, B, C):
    AB = np.array([A[0] - B[0], A[1] - B[1]])
    CB = np.array([C[0] - B[0], C[1] - B[1]])
    dot = np.dot(AB, CB)
    mag_AB = np.linalg.norm(AB)
    mag_CB = np.linalg.norm(CB)
    cos_theta = np.clip(dot / (mag_AB * mag_CB), -1.0, 1.0)
    return round(np.degrees(np.arccos(cos_theta)), 2)
```

---

### `classifier.py`
Contains two functions:

**`classify_posture(angle, joint)`**  
Compares the calculated angle against thresholds for each joint type and returns a label and colour.

| Joint    | GOOD          | ADJUST        | BAD            |
|----------|---------------|---------------|----------------|
| knee     | 70° – 110°    | 60° – 70°     | < 60° or >110° |
| hip      | 160° – 180°   | 140° – 160°   | < 140°         |
| shoulder | 150° – 180°   | 130° – 150°   | < 130°         |
| elbow    | 30° – 160°    | 20° – 30°     | < 20°          |
| neck     | 140° – 180°   | 120° – 140°   | < 120°         |
| spine    | 150° – 180°   | 130° – 150°   | < 130°         |

**`get_form_score(angle, ideal)`**  
Returns a score 0–100 based on how close the actual angle is to the ideal angle.  
`score = max(0, 100 - abs(actual - ideal))`

**`get_sitting_score(neck_angle, spine_angle)`**  
Averages the neck and spine scores for an overall sitting posture score.

---

### `main.py`
The main program. Opens the webcam, runs MediaPipe Pose detection every frame, extracts landmark coordinates, calls `calculate_angle()`, calls `classify_posture()`, and draws everything on screen.

**Two modes:**

**GYM mode** — tracks squats  
- Joints used: right hip (24) → right knee (26) → right ankle (28)  
- Counts reps by detecting angle going below 90° (DOWN) then above 160° (UP)  
- Alerts after 3 seconds of bad posture

**SITTING mode** — detects hunchback at a desk  
- Neck angle: left ear (7) → left shoulder (11) → left hip (23)  
- Spine angle: left shoulder (11) → left hip (23) → left knee (25)  
- Alerts after 5 seconds of hunching  
- Works best when camera is to your side (profile view)

**Controls:**
| Key | Action |
|-----|--------|
| `S` | Switch between GYM and SITTING mode |
| `Q` | Quit |

---

## MediaPipe landmark indices used

| Body point    | Index |
|---------------|-------|
| Left ear      | 7     |
| Left shoulder | 11    |
| Right shoulder| 12    |
| Left elbow    | 13    |
| Right elbow   | 14    |
| Left hip      | 23    |
| Right hip     | 24    |
| Left knee     | 25    |
| Right knee    | 26    |
| Left ankle    | 27    |
| Right ankle   | 28    |

Full landmark map: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker

---

## Setup instructions for teammates

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
|-------|-----|
| `module mediapipe has no attribute solutions` | Run `pip install mediapipe==0.10.9` |
| `Cannot open camera` | Change `VideoCapture(0)` to `VideoCapture(1)` in main.py |
| `ModuleNotFoundError` | Make sure venv311 is activated before running |
| Sitting mode not detecting | Turn sideways so camera sees your profile |

---

## How to contribute — adding a new exercise

To add a new exercise (e.g. bicep curl), you only need to:

1. **Add thresholds** in `classifier.py` under the `thresholds` dictionary
2. **Pick the right landmark indices** from the table above
3. **Add the angle calculation** in `main.py` using the same `calculate_angle()` call
4. **Display it** using `cv2.putText()`

The math never changes — only the joint indices and thresholds do.

---

## Future improvements to work on

- [ ] Add bicep curl rep counter (elbow angle)
- [ ] Add pushup detection (elbow + shoulder)
- [ ] Save session data to CSV after each workout
- [ ] Generate a matplotlib graph of angle over time
- [ ] Add voice feedback using `pyttsx3`
- [ ] Build a simple tkinter UI to select exercise before starting
- [ ] Add left/right side switching for gym exercises

---

## Original project reference

This project is based on the mathematical model from:  
**"Mathematical Modeling in Posture Analysis"** — Vanshika Aneja & Advika Mathur  
The Java implementation used IntelliJ IDEA with Swing (ImagePanel + mouse click input).  
This Python version replaces manual point clicking with automatic real-time MediaPipe landmark detection.

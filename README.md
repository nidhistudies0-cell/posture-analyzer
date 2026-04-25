# 🏋️ Posture Analyzer — Real-Time Gym  Tracker

A real-time posture analysis tool powered by **MediaPipe** and **OpenCV** that tracks body landmarks through your webcam, classifies joint angles, counts reps, and gives live form feedback for 10 exercises plus a sitting posture mode.

---

## Features

- **10 Gym Exercises** — Squats, Push Ups, Pull Ups, Jumping Jacks, Russian Twists, Lunges, Plank, Bicep Curls, Shoulder Press, Deadlift
- **Sitting Mode** — Neck and spine angle tracking for desk posture
- **Live Rep Counter** — Counts reps automatically based on joint angle thresholds
- **Form Score (0–100)** — Real-time score bar showing how close you are to ideal angles
- **Posture Classification** — GOOD / ADJUST SLIGHTLY / BAD POSTURE labels per joint
- **Sustained Bad Posture Alert** — On-screen warning if bad form is held for 3+ seconds
- **Auto Camera Detection** — Tries camera indices 0, 1, 2 automatically

---

## Project Structure

```
posture-analyzer/
├── main.py          # Core logic — webcam loop, exercise router, UI rendering
├── launcher.py      # GUI launcher — mode and exercise selector
├── angle_utils.py   # Joint angle calculation using NumPy
├── classifier.py    # Angle thresholds, posture labels, form scoring
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.8+
- Webcam

### Install dependencies

```bash
pip install opencv-python mediapipe numpy
```

---

## Usage

### Option 1 — Launcher (recommended)

```bash
python launcher.py
```

Select your mode (GYM or SITTING) and exercise from the GUI, then click Start.

### Option 2 — Direct run

```bash
# Default: GYM mode, Squats
python main.py

# Specific exercise
python main.py --mode GYM --exercise "PUSH UPS"

# Sitting mode
python main.py --mode SITTING
```

### Keyboard Controls (while running)

| Key | Action |
|-----|--------|
| `A` | Previous exercise |
| `D` | Next exercise |
| `R` | Reset reps & stage |
| `S` | Toggle GYM / SITTING mode |
| `Q` | Quit |

---

## Supported Exercises

| Exercise | Joints Tracked | Rep Trigger |
|---|---|---|
| Squats | Knee, Hip | Knee < 90° → > 160° |
| Push Ups | Elbow, Hip | Elbow < 90° → > 155° |
| Pull Ups | Elbow, Shoulder | Elbow > 150° → < 90° |
| Jumping Jacks | Shoulder, Elbow | Shoulder < 25° → > 130° |
| Russian Twists | Hip, Knee, Shoulder | Side-to-side swing |
| Lunges | Knee, Hip | Knee < 105° → > 160° |
| Plank | Hip, Elbow, Knee | Hold timer (seconds) |
| Bicep Curls | Elbow, Shoulder | Elbow > 155° → < 65° |
| Shoulder Press | Elbow, Shoulder | Elbow < 110° → > 155° |
| Deadlift | Hip, Knee | Hip < 100° → > 160° |

---

## How It Works

1. **MediaPipe Pose** extracts 33 body landmarks from each webcam frame
2. **`angle_utils.py`** computes joint angles using the dot-product formula between landmark vectors
3. **`classifier.py`** compares angles against exercise-specific thresholds (derived from dataset percentiles) to label posture and compute a form score
4. **`main.py`** routes the frame to the correct exercise handler, draws skeleton overlays, and renders the info panel

---

## Troubleshooting

**Webcam not opening**
- The app auto-tries indices 0, 1, 2. If all fail, check that no other app is using the camera.
- macOS: grant camera access under System Settings → Privacy & Security → Camera
- Windows: try adding `cv2.CAP_DSHOW` backend if issues persist

**Pose not detected**
- Ensure your full body (or relevant joints) is visible in frame
- Use good lighting — avoid strong backlight
- For side exercises (Plank, Deadlift), face sideways to the camera

**Low form score**
- The score is deviation-based from an ideal angle — small deviations still score well above 70

---

## Module Reference

### `angle_utils.py`
```python
calculate_angle(A, B, C) -> float
# Returns angle at joint B (in degrees) given three (x, y) coordinate tuples
```

### `classifier.py`
```python
classify_posture(angle, joint) -> (label, color)
get_form_score(angle, ideal) -> int          # 0–100 single joint score
get_multi_joint_score(*pairs) -> int         # averaged across joints
get_sitting_score(neck_angle, spine_angle) -> int
```


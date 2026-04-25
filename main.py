import argparse
import cv2
import mediapipe as mp
import time
from angle_utils import calculate_angle
from classifier import classify_posture, get_form_score, get_multi_joint_score, get_sitting_score

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils

def get_coords(landmarks, idx, w, h):
    lm = landmarks[idx]
    return (int(lm.x * w), int(lm.y * h))

# ── exercise list for GYM mode ──────────────────────────────────────────────
GYM_EXERCISES = [
    "SQUATS",
    "PUSH UPS",
    "PULL UPS",
    "JUMPING JACKS",
    "RUSSIAN TWISTS",
    "LUNGES",
    "PLANK",
    "BICEP CURLS",
    "SHOULDER PRESS",
    "DEADLIFT",
]

# ── CLI arguments (passed by launcher.py) ────────────────────────────────────
_parser = argparse.ArgumentParser(description="Posture Analyzer")
_parser.add_argument("--mode",     default="GYM",    choices=["GYM", "SITTING"])
_parser.add_argument("--exercise", default="SQUATS", choices=GYM_EXERCISES)
_args = _parser.parse_args()

# ── state variables ──────────────────────────────────────────────────────────
bad_start    = None
reps         = 0
stage        = None
mode         = _args.mode
exercise_idx = GYM_EXERCISES.index(_args.exercise) if _args.mode == "GYM" else 0
hunch_start  = None
plank_start  = None


def draw_info_panel(frame, exercise, label, color, angle_lines,
                    reps, stage, score, bad_start):
    """
    Draws the black info panel on the top-left.
    angle_lines: list of strings like ["KNEE: 88.4", "HIP: 170.2"]
    """
    panel_h = 60 + len(angle_lines) * 35 + 105
    cv2.rectangle(frame, (0, 0), (320, panel_h), (0, 0, 0), -1)

    cv2.putText(frame, f"MODE: GYM — {exercise}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(frame, f"POSTURE: {label}",
                (10, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    y = 95
    for line in angle_lines:
        cv2.putText(frame, line,
                    (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 1)
        y += 32

    cv2.putText(frame, f"REPS:  {reps}",
                (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
    cv2.putText(frame, f"STAGE: {stage}",
                (10, y + 32), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 0), 2)
    cv2.putText(frame, f"FORM:  {score}/100",
                (10, y + 64), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 255, 128), 2)

    # form score bar
    bar_y = y + 80
    bar_w = int((score / 100) * 290)
    cv2.rectangle(frame, (10, bar_y), (300, bar_y + 14), (50, 50, 50), -1)
    bar_color = (0, 255, 0) if score >= 70 else \
                (0, 165, 255) if score >= 40 else (0, 0, 255)
    cv2.rectangle(frame, (10, bar_y), (10 + bar_w, bar_y + 14), bar_color, -1)

    # sustained bad posture alert
    if label == "BAD POSTURE" and bad_start is not None:
        elapsed = time.time() - bad_start
        if elapsed > 3:
            cv2.putText(frame, "FIX YOUR POSTURE",
                        (30, frame.shape[0] // 2), cv2.FONT_HERSHEY_SIMPLEX,
                        1.2, (0, 0, 255), 3)


def open_camera():
    """
    Try camera indices 0, 1, 2 in order.
    Returns an opened VideoCapture or raises SystemExit.
    """
    for idx in range(3):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"[INFO] Camera opened at index {idx}")
                return cap
            cap.release()
    print("[ERROR] No webcam found on indices 0, 1, or 2.")
    print("        Make sure your camera is connected and not used by another app.")
    print("        On macOS: check System Settings → Privacy & Security → Camera")
    raise SystemExit(1)


with mp_pose.Pose(min_detection_confidence=0.6,
                  min_tracking_confidence=0.6) as pose:

    cap = open_camera()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or frame is None:
            print("[WARNING] Failed to grab frame. Retrying...")
            time.sleep(0.05)
            continue

        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark

            mp_draw.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS
            )

            # ════════════════════════════════════════════════════════════════
            #   GYM MODE — exercise router
            # ════════════════════════════════════════════════════════════════
            if mode == "GYM":
                exercise = GYM_EXERCISES[exercise_idx]

                # ── SQUATS ───────────────────────────────────────────────────
                if exercise == "SQUATS":
                    hip   = get_coords(lm, 24, w, h)
                    knee  = get_coords(lm, 26, w, h)
                    ankle = get_coords(lm, 28, w, h)
                    r_shoulder = get_coords(lm, 12, w, h)

                    knee_angle = calculate_angle(hip, knee, ankle)
                    hip_angle  = calculate_angle(r_shoulder, hip, knee)

                    if knee_angle < 90:
                        stage = "DOWN"
                    if knee_angle > 160 and stage == "DOWN":
                        stage = "UP"
                        reps += 1

                    joint_key = "squat_knee_down" if stage == "DOWN" else "squat_knee_up"
                    label, color = classify_posture(knee_angle, joint_key)
                    score = get_multi_joint_score((knee_angle, 90), (hip_angle, 170))

                    cv2.line(frame, hip, knee, color, 2)
                    cv2.line(frame, ankle, knee, color, 2)
                    cv2.putText(frame, f"{knee_angle}", knee,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.putText(frame, f"{hip_angle}", hip,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    draw_info_panel(frame, exercise, label, color,
                                    [f"KNEE:  {knee_angle}", f"HIP:   {hip_angle}"],
                                    reps, stage, score, bad_start)

                # ── PUSH UPS ─────────────────────────────────────────────────
                elif exercise == "PUSH UPS":
                    l_shoulder = get_coords(lm, 11, w, h)
                    l_elbow    = get_coords(lm, 13, w, h)
                    l_wrist    = get_coords(lm, 15, w, h)
                    l_hip      = get_coords(lm, 23, w, h)
                    l_knee     = get_coords(lm, 25, w, h)

                    elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                    hip_angle   = calculate_angle(l_shoulder, l_hip, l_knee)

                    if elbow_angle < 90:
                        stage = "DOWN"
                    if elbow_angle > 155 and stage == "DOWN":
                        stage = "UP"
                        reps += 1

                    joint_key = "pushup_elbow_down" if stage == "DOWN" else "pushup_elbow_up"
                    label, color = classify_posture(elbow_angle, joint_key)
                    hip_label, _ = classify_posture(hip_angle, "pushup_hip")
                    if hip_label == "BAD POSTURE":
                        label, color = "BAD POSTURE — BODY SAG", (0, 0, 255)
                    score = get_multi_joint_score((elbow_angle, 90), (hip_angle, 170))

                    cv2.line(frame, l_shoulder, l_elbow, color, 2)
                    cv2.line(frame, l_elbow, l_wrist, color, 2)
                    cv2.putText(frame, f"{elbow_angle}", l_elbow,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.putText(frame, f"{hip_angle}", l_hip,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    draw_info_panel(frame, exercise, label, color,
                                    [f"ELBOW: {elbow_angle}", f"HIP:   {hip_angle}"],
                                    reps, stage, score, bad_start)

                # ── PULL UPS ─────────────────────────────────────────────────
                elif exercise == "PULL UPS":
                    l_shoulder = get_coords(lm, 11, w, h)
                    l_elbow    = get_coords(lm, 13, w, h)
                    l_wrist    = get_coords(lm, 15, w, h)
                    l_hip      = get_coords(lm, 23, w, h)

                    elbow_angle    = calculate_angle(l_shoulder, l_elbow, l_wrist)
                    shoulder_angle = calculate_angle(l_elbow, l_shoulder, l_hip)

                    if elbow_angle > 150:
                        stage = "HANG"
                    if elbow_angle < 90 and stage == "HANG":
                        stage = "UP"
                        reps += 1
                    if elbow_angle > 150 and stage == "UP":
                        stage = "HANG"

                    joint_key = "pullup_elbow_up" if stage == "UP" else "pullup_elbow_down"
                    label, color = classify_posture(elbow_angle, joint_key)
                    score = get_multi_joint_score((elbow_angle, 60), (shoulder_angle, 155))

                    cv2.line(frame, l_shoulder, l_elbow, color, 2)
                    cv2.line(frame, l_elbow, l_wrist, color, 2)
                    cv2.putText(frame, f"{elbow_angle}", l_elbow,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.putText(frame, f"{shoulder_angle}", l_shoulder,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    draw_info_panel(frame, exercise, label, color,
                                    [f"ELBOW:    {elbow_angle}",
                                     f"SHOULDER: {shoulder_angle}"],
                                    reps, stage, score, bad_start)

                # ── JUMPING JACKS ────────────────────────────────────────────
                elif exercise == "JUMPING JACKS":
                    l_elbow    = get_coords(lm, 13, w, h)
                    l_shoulder = get_coords(lm, 11, w, h)
                    l_hip      = get_coords(lm, 23, w, h)
                    l_wrist    = get_coords(lm, 15, w, h)

                    shoulder_angle = calculate_angle(l_elbow, l_shoulder, l_hip)
                    elbow_angle    = calculate_angle(l_shoulder, l_elbow, l_wrist)

                    if shoulder_angle < 25:
                        stage = "DOWN"
                    if shoulder_angle > 130 and stage == "DOWN":
                        stage = "UP"
                        reps += 1
                    if shoulder_angle < 25 and stage == "UP":
                        stage = "DOWN"

                    joint_key = "jack_shoulder_down" if stage == "DOWN" else "jack_shoulder_up"
                    label, color = classify_posture(shoulder_angle, joint_key)
                    score = get_multi_joint_score((shoulder_angle, 160), (elbow_angle, 165))

                    cv2.line(frame, l_elbow, l_shoulder, color, 2)
                    cv2.line(frame, l_shoulder, l_hip, color, 2)
                    cv2.putText(frame, f"{shoulder_angle}", l_shoulder,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.putText(frame, f"{elbow_angle}", l_elbow,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    draw_info_panel(frame, exercise, label, color,
                                    [f"SHOULDER: {shoulder_angle}",
                                     f"ELBOW:    {elbow_angle}"],
                                    reps, stage, score, bad_start)

                # ── RUSSIAN TWISTS ───────────────────────────────────────────
                elif exercise == "RUSSIAN TWISTS":
                    l_shoulder = get_coords(lm, 11, w, h)
                    l_hip      = get_coords(lm, 23, w, h)
                    l_knee     = get_coords(lm, 25, w, h)
                    l_ankle    = get_coords(lm, 27, w, h)
                    l_elbow    = get_coords(lm, 13, w, h)

                    hip_angle      = calculate_angle(l_shoulder, l_hip, l_knee)
                    knee_angle     = calculate_angle(l_hip, l_knee, l_ankle)
                    shoulder_angle = calculate_angle(l_elbow, l_shoulder, l_hip)

                    if shoulder_angle < 10:
                        if stage == "LEFT" or stage is None:
                            stage = "RIGHT"
                        elif stage == "RIGHT":
                            stage = "LEFT"
                            reps += 1

                    hip_label, hip_color = classify_posture(hip_angle, "twist_hip")
                    knee_label, _        = classify_posture(knee_angle, "twist_knee")

                    label = hip_label
                    color = hip_color
                    if knee_label == "BAD POSTURE" and label != "BAD POSTURE":
                        label, color = "KEEP KNEES BENT", (0, 165, 255)

                    score = get_multi_joint_score((hip_angle, 52), (knee_angle, 90))

                    cv2.line(frame, l_shoulder, l_hip, hip_color, 2)
                    cv2.line(frame, l_hip, l_knee, hip_color, 2)
                    cv2.putText(frame, f"{hip_angle}", l_hip,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.putText(frame, f"{knee_angle}", l_knee,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    draw_info_panel(frame, exercise, label, color,
                                    [f"HIP:   {hip_angle}  (target: 30-90)",
                                     f"KNEE:  {knee_angle}  (target: 60-120)"],
                                    reps, stage, score, bad_start)

                # ── LUNGES ───────────────────────────────────────────────────
                elif exercise == "LUNGES":
                    r_hip   = get_coords(lm, 24, w, h)
                    r_knee  = get_coords(lm, 26, w, h)
                    r_ankle = get_coords(lm, 28, w, h)
                    r_shoulder = get_coords(lm, 12, w, h)

                    knee_angle = calculate_angle(r_hip, r_knee, r_ankle)
                    hip_angle  = calculate_angle(r_shoulder, r_hip, r_knee)

                    if knee_angle < 105:
                        stage = "DOWN"
                    if knee_angle > 160 and stage == "DOWN":
                        stage = "UP"
                        reps += 1

                    joint_key = "lunge_knee_down" if stage == "DOWN" else "lunge_knee_up"
                    label, color = classify_posture(knee_angle, joint_key)
                    score = get_multi_joint_score((knee_angle, 90), (hip_angle, 100))

                    cv2.line(frame, r_hip, r_knee, color, 2)
                    cv2.line(frame, r_knee, r_ankle, color, 2)
                    cv2.putText(frame, f"{knee_angle}", r_knee,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.putText(frame, f"{hip_angle}", r_hip,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    draw_info_panel(frame, exercise, label, color,
                                    [f"KNEE:  {knee_angle}  (target: 80-105)",
                                     f"HIP:   {hip_angle}  (target: 85-120)"],
                                    reps, stage, score, bad_start)

                # ── PLANK ────────────────────────────────────────────────────
                elif exercise == "PLANK":
                    l_shoulder = get_coords(lm, 11, w, h)
                    l_elbow    = get_coords(lm, 13, w, h)
                    l_wrist    = get_coords(lm, 15, w, h)
                    l_hip      = get_coords(lm, 23, w, h)
                    l_knee     = get_coords(lm, 25, w, h)
                    l_ankle    = get_coords(lm, 27, w, h)

                    elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
                    hip_angle   = calculate_angle(l_shoulder, l_hip, l_knee)
                    knee_angle  = calculate_angle(l_hip, l_knee, l_ankle)

                    hip_label, hip_color   = classify_posture(hip_angle, "plank_hip")
                    elbow_label, _         = classify_posture(elbow_angle, "plank_elbow")
                    knee_label, _          = classify_posture(knee_angle, "plank_knee")

                    if "BAD" in hip_label:
                        label, color = hip_label, hip_color
                    elif "ADJUST" in hip_label:
                        label, color = "ADJUST — CHECK HIPS", (0, 165, 255)
                    else:
                        label, color = "GOOD POSTURE", (0, 200, 0)

                    if label == "GOOD POSTURE":
                        if plank_start is None:
                            plank_start = time.time()
                        stage = f"{int(time.time() - plank_start)}s HOLD"
                    else:
                        plank_start = None
                        stage = "HOLD POSITION"

                    score = get_multi_joint_score(
                        (hip_angle, 170), (elbow_angle, 170), (knee_angle, 170)
                    )

                    cv2.line(frame, l_shoulder, l_hip, hip_color, 2)
                    cv2.line(frame, l_hip, l_knee, hip_color, 2)
                    cv2.putText(frame, f"{hip_angle}", l_hip,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.putText(frame, f"{elbow_angle}", l_elbow,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    draw_info_panel(frame, exercise, label, color,
                                    [f"HIP:   {hip_angle}  (target: 160-180)",
                                     f"ELBOW: {elbow_angle}  (target: 155-180)",
                                     f"KNEE:  {knee_angle}  (target: 155-180)"],
                                    reps, stage, score, bad_start)

                # ── BICEP CURLS ──────────────────────────────────────────────
                elif exercise == "BICEP CURLS":
                    l_shoulder = get_coords(lm, 11, w, h)
                    l_elbow    = get_coords(lm, 13, w, h)
                    l_wrist    = get_coords(lm, 15, w, h)
                    l_hip      = get_coords(lm, 23, w, h)

                    elbow_angle    = calculate_angle(l_shoulder, l_elbow, l_wrist)
                    shoulder_angle = calculate_angle(l_elbow, l_shoulder, l_hip)

                    if elbow_angle > 155:
                        stage = "DOWN"
                    if elbow_angle < 65 and stage == "DOWN":
                        stage = "UP"
                        reps += 1

                    joint_key = "curl_elbow_up" if stage == "UP" else "curl_elbow_down"
                    label, color = classify_posture(elbow_angle, joint_key)

                    shoulder_label, _ = classify_posture(shoulder_angle, "curl_shoulder")
                    if shoulder_label == "BAD POSTURE":
                        label, color = "DON'T SWING", (0, 0, 255)

                    score = get_multi_joint_score((elbow_angle, 45), (shoulder_angle, 10))

                    cv2.line(frame, l_shoulder, l_elbow, color, 2)
                    cv2.line(frame, l_elbow, l_wrist, color, 2)
                    cv2.putText(frame, f"{elbow_angle}", l_elbow,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.putText(frame, f"{shoulder_angle}", l_shoulder,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    draw_info_panel(frame, exercise, label, color,
                                    [f"ELBOW:    {elbow_angle}",
                                     f"SHOULDER: {shoulder_angle}  (keep still)"],
                                    reps, stage, score, bad_start)

                # ── SHOULDER PRESS ───────────────────────────────────────────
                elif exercise == "SHOULDER PRESS":
                    l_elbow    = get_coords(lm, 13, w, h)
                    l_shoulder = get_coords(lm, 11, w, h)
                    l_wrist    = get_coords(lm, 15, w, h)
                    l_hip      = get_coords(lm, 23, w, h)

                    elbow_angle    = calculate_angle(l_shoulder, l_elbow, l_wrist)
                    shoulder_angle = calculate_angle(l_elbow, l_shoulder, l_hip)

                    if elbow_angle < 110:
                        stage = "DOWN"
                    if elbow_angle > 155 and stage == "DOWN":
                        stage = "UP"
                        reps += 1

                    joint_key = "press_elbow_up" if stage == "UP" else "press_elbow_down"
                    label, color = classify_posture(elbow_angle, joint_key)
                    score = get_multi_joint_score((elbow_angle, 95), (shoulder_angle, 160))

                    cv2.line(frame, l_shoulder, l_elbow, color, 2)
                    cv2.line(frame, l_elbow, l_wrist, color, 2)
                    cv2.putText(frame, f"{elbow_angle}", l_elbow,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.putText(frame, f"{shoulder_angle}", l_shoulder,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    draw_info_panel(frame, exercise, label, color,
                                    [f"ELBOW:    {elbow_angle}",
                                     f"SHOULDER: {shoulder_angle}"],
                                    reps, stage, score, bad_start)

                # ── DEADLIFT ─────────────────────────────────────────────────
                elif exercise == "DEADLIFT":
                    r_shoulder = get_coords(lm, 12, w, h)
                    r_hip      = get_coords(lm, 24, w, h)
                    r_knee     = get_coords(lm, 26, w, h)
                    r_ankle    = get_coords(lm, 28, w, h)

                    hip_angle  = calculate_angle(r_shoulder, r_hip, r_knee)
                    knee_angle = calculate_angle(r_hip, r_knee, r_ankle)

                    if hip_angle < 100:
                        stage = "DOWN"
                    if hip_angle > 160 and stage == "DOWN":
                        stage = "UP"
                        reps += 1

                    joint_key = "deadlift_hip_down" if stage == "DOWN" else "deadlift_hip_up"
                    label, color = classify_posture(hip_angle, joint_key)
                    score = get_multi_joint_score((hip_angle, 170), (knee_angle, 120))

                    cv2.line(frame, r_shoulder, r_hip, color, 2)
                    cv2.line(frame, r_hip, r_knee, color, 2)
                    cv2.line(frame, r_knee, r_ankle, color, 2)
                    cv2.putText(frame, f"{hip_angle}", r_hip,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                    cv2.putText(frame, f"{knee_angle}", r_knee,
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    draw_info_panel(frame, exercise, label, color,
                                    [f"HIP:   {hip_angle}  (hinge to 45-100)",
                                     f"KNEE:  {knee_angle}  (soft bend: 100-150)"],
                                    reps, stage, score, bad_start)

                # ── bad posture timer (shared) ───────────────────────────────
                if label == "BAD POSTURE" or label.startswith("BAD"):
                    if bad_start is None:
                        bad_start = time.time()
                else:
                    bad_start = None

                # ── exercise selector strip (top right) ──────────────────────
                cv2.putText(frame, f"< A | {exercise} | D >",
                            (w - 300, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (200, 200, 200), 1)

            # ════════════════════════════════════════════════════════════════
            #   SITTING MODE
            # ════════════════════════════════════════════════════════════════
            elif mode == "SITTING":
                l_ear      = get_coords(lm, 7,  w, h)
                l_shoulder = get_coords(lm, 11, w, h)
                l_hip      = get_coords(lm, 23, w, h)
                l_knee     = get_coords(lm, 25, w, h)

                neck_angle  = calculate_angle(l_ear,      l_shoulder, l_hip)
                spine_angle = calculate_angle(l_shoulder, l_hip,      l_knee)

                neck_label,  neck_color  = classify_posture(neck_angle,  "neck")
                spine_label, spine_color = classify_posture(spine_angle, "spine")

                sitting_score = get_sitting_score(neck_angle, spine_angle)

                if "BAD" in neck_label or "BAD" in spine_label:
                    overall_label = "HUNCHING DETECTED"
                    overall_color = (0, 0, 255)
                elif "ADJUST" in neck_label or "ADJUST" in spine_label:
                    overall_label = "ADJUST POSTURE"
                    overall_color = (0, 165, 255)
                else:
                    overall_label = "SITTING WELL"
                    overall_color = (0, 200, 0)

                if "BAD" in neck_label or "BAD" in spine_label:
                    if hunch_start is None:
                        hunch_start = time.time()
                    elif time.time() - hunch_start > 5:
                        cv2.putText(frame, "SIT UP STRAIGHT!",
                                    (30, 340), cv2.FONT_HERSHEY_SIMPLEX,
                                    1.3, (0, 0, 255), 3)
                else:
                    hunch_start = None

                cv2.line(frame, l_ear,      l_shoulder, neck_color,  2)
                cv2.line(frame, l_shoulder, l_hip,      spine_color, 2)
                cv2.line(frame, l_hip,      l_knee,     spine_color, 2)

                cv2.putText(frame, f"{neck_angle}",
                            l_shoulder, cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, (255, 255, 0), 2)
                cv2.putText(frame, f"{spine_angle}",
                            l_hip, cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, (255, 255, 0), 2)

                cv2.rectangle(frame, (0, 0), (320, 290), (0, 0, 0), -1)
                cv2.putText(frame, "MODE: SITTING",
                            (10, 35), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 255), 2)
                cv2.putText(frame, f"STATUS: {overall_label}",
                            (10, 75), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, overall_color, 2)
                cv2.putText(frame, f"NECK:  {neck_angle}  {neck_label}",
                            (10, 115), cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, neck_color, 2)
                cv2.putText(frame, f"SPINE: {spine_angle}  {spine_label}",
                            (10, 150), cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, spine_color, 2)
                cv2.putText(frame, f"SCORE: {sitting_score}/100",
                            (10, 190), cv2.FONT_HERSHEY_SIMPLEX,
                            0.65, (0, 255, 128), 2)

                bar_w = int((sitting_score / 100) * 300)
                cv2.rectangle(frame, (10, 205), (310, 220), (50, 50, 50), -1)
                bar_color = (0, 255, 0) if sitting_score >= 70 else \
                            (0, 165, 255) if sitting_score >= 40 else (0, 0, 255)
                cv2.rectangle(frame, (10, 205), (10 + bar_w, 220), bar_color, -1)

                cv2.putText(frame, "Tip: face sideways to camera",
                            (10, 255), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (180, 180, 180), 1)

        # ── bottom bar: controls ─────────────────────────────────────────────
        ctrl = "A/D: prev/next exercise  |  R: reset  |  S: switch mode  |  Q: quit"
        cv2.putText(frame, ctrl,
                    (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX,
                    0.42, (180, 180, 180), 1)

        cv2.imshow("Posture Analyzer - Gym Tracker", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        elif key == ord('s'):
            if mode == "GYM":
                mode = "SITTING"
                hunch_start = None
            else:
                mode = "GYM"
                bad_start = None
                reps      = 0
                stage     = None
                plank_start = None

        elif key == ord('a') and mode == "GYM":
            exercise_idx = (exercise_idx - 1) % len(GYM_EXERCISES)
            reps = 0
            stage = None
            bad_start = None
            plank_start = None

        elif key == ord('d') and mode == "GYM":
            exercise_idx = (exercise_idx + 1) % len(GYM_EXERCISES)
            reps = 0
            stage = None
            bad_start = None
            plank_start = None

        elif key == ord('r') and mode == "GYM":
            reps = 0
            stage = None
            plank_start = None

    cap.release()
    cv2.destroyAllWindows()
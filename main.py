import cv2
import mediapipe as mp
import time
from angle_utils import calculate_angle
from classifier import classify_posture, get_form_score, get_sitting_score

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils

def get_coords(landmarks, idx, w, h):
    lm = landmarks[idx]
    return (int(lm.x * w), int(lm.y * h))

cap = cv2.VideoCapture(0)

# --- state variables ---
bad_start    = None
reps         = 0
stage        = None
mode         = "GYM"      # start in gym mode, press S to switch
hunch_start  = None       # timer for sitting hunch alert

with mp_pose.Pose(min_detection_confidence=0.6,
                  min_tracking_confidence=0.6) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

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

            # ════════════════════════════════════
            #           GYM MODE
            # ════════════════════════════════════
            if mode == "GYM":
                hip   = get_coords(lm, 24, w, h)
                knee  = get_coords(lm, 26, w, h)
                ankle = get_coords(lm, 28, w, h)

                knee_angle = calculate_angle(hip, knee, ankle)
                label, color = classify_posture(knee_angle, "knee")
                score = get_form_score(knee_angle, ideal=90)

                # rep counter
                if knee_angle < 90:
                    stage = "DOWN"
                if knee_angle > 160 and stage == "DOWN":
                    stage = "UP"
                    reps += 1

                # bad posture timer
                if label == "BAD POSTURE":
                    if bad_start is None:
                        bad_start = time.time()
                    elif time.time() - bad_start > 3:
                        cv2.putText(frame, "FIX YOUR POSTURE",
                                    (30, 310), cv2.FONT_HERSHEY_SIMPLEX,
                                    1.2, (0, 0, 255), 3)
                else:
                    bad_start = None

                # draw joint lines
                cv2.line(frame, hip,   knee,  color, 2)
                cv2.line(frame, ankle, knee,  color, 2)

                # angle at joint
                cv2.putText(frame, f"{knee_angle}",
                            knee, cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (255, 255, 0), 2)

                # info panel
                cv2.rectangle(frame, (0, 0), (300, 260), (0, 0, 0), -1)
                cv2.putText(frame, "MODE: GYM",
                            (10, 35), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (0, 255, 255), 2)
                cv2.putText(frame, f"POSTURE: {label}",
                            (10, 75), cv2.FONT_HERSHEY_SIMPLEX,
                            0.65, color, 2)
                cv2.putText(frame, f"ANGLE:   {knee_angle}",
                            (10, 110), cv2.FONT_HERSHEY_SIMPLEX,
                            0.65, (255, 255, 255), 2)
                cv2.putText(frame, f"REPS:    {reps}",
                            (10, 145), cv2.FONT_HERSHEY_SIMPLEX,
                            0.65, (255, 255, 255), 2)
                cv2.putText(frame, f"STAGE:   {stage}",
                            (10, 180), cv2.FONT_HERSHEY_SIMPLEX,
                            0.65, (255, 255, 0), 2)
                cv2.putText(frame, f"FORM:    {score}/100",
                            (10, 215), cv2.FONT_HERSHEY_SIMPLEX,
                            0.65, (0, 255, 128), 2)

                # form score bar
                bar_w = int((score / 100) * 280)
                cv2.rectangle(frame, (10, 230), (290, 245), (50, 50, 50), -1)
                bar_color = (0, 255, 0) if score >= 70 else \
                            (0, 165, 255) if score >= 40 else (0, 0, 255)
                cv2.rectangle(frame, (10, 230), (10 + bar_w, 245), bar_color, -1)

            # ════════════════════════════════════
            #           SITTING MODE
            # ════════════════════════════════════
            elif mode == "SITTING":
                # landmark points
                l_ear      = get_coords(lm, 7,  w, h)
                l_shoulder = get_coords(lm, 11, w, h)
                l_hip      = get_coords(lm, 23, w, h)
                l_knee     = get_coords(lm, 25, w, h)

                # angles
                neck_angle  = calculate_angle(l_ear,      l_shoulder, l_hip)
                spine_angle = calculate_angle(l_shoulder, l_hip,      l_knee)

                # classify each
                neck_label,  neck_color  = classify_posture(neck_angle,  "neck")
                spine_label, spine_color = classify_posture(spine_angle, "spine")

                # overall sitting score
                sitting_score = get_sitting_score(neck_angle, spine_angle)

                # determine overall status
                if "BAD" in neck_label or "BAD" in spine_label:
                    overall_label = "HUNCHING DETECTED"
                    overall_color = (0, 0, 255)
                elif "ADJUST" in neck_label or "ADJUST" in spine_label:
                    overall_label = "ADJUST POSTURE"
                    overall_color = (0, 165, 255)
                else:
                    overall_label = "SITTING WELL"
                    overall_color = (0, 200, 0)

                # hunch alert after 5 seconds
                if "BAD" in neck_label or "BAD" in spine_label:
                    if hunch_start is None:
                        hunch_start = time.time()
                    elif time.time() - hunch_start > 5:
                        cv2.putText(frame, "SIT UP STRAIGHT!",
                                    (30, 340), cv2.FONT_HERSHEY_SIMPLEX,
                                    1.3, (0, 0, 255), 3)
                else:
                    hunch_start = None

                # draw body lines
                cv2.line(frame, l_ear,      l_shoulder, neck_color,  2)
                cv2.line(frame, l_shoulder, l_hip,      spine_color, 2)
                cv2.line(frame, l_hip,      l_knee,     spine_color, 2)

                # angle labels on joints
                cv2.putText(frame, f"{neck_angle}",
                            l_shoulder, cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, (255, 255, 0), 2)
                cv2.putText(frame, f"{spine_angle}",
                            l_hip, cv2.FONT_HERSHEY_SIMPLEX,
                            0.55, (255, 255, 0), 2)

                # info panel
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

                # sitting score bar
                bar_w = int((sitting_score / 100) * 300)
                cv2.rectangle(frame, (10, 205), (310, 220), (50, 50, 50), -1)
                bar_color = (0, 255, 0) if sitting_score >= 70 else \
                            (0, 165, 255) if sitting_score >= 40 else (0, 0, 255)
                cv2.rectangle(frame, (10, 205), (10 + bar_w, 220), bar_color, -1)

                cv2.putText(frame, "Tip: face sideways to camera",
                            (10, 255), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (180, 180, 180), 1)

        # --- mode label bottom left ---
        cv2.putText(frame, "Press S: switch mode  |  Q: quit",
                    (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (180, 180, 180), 1)

        cv2.imshow("Posture Analyzer - Gym Tracker", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # switch mode and reset counters
            if mode == "GYM":
                mode = "SITTING"
                hunch_start = None
            else:
                mode = "GYM"
                bad_start = None
                reps  = 0
                stage = None

cap.release()
cv2.destroyAllWindows()
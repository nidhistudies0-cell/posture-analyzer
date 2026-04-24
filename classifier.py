def classify_posture(angle, joint="knee"):
    thresholds = {
        # ── sitting posture joints (unchanged) ──────────────────────────────
        "neck": {
            "good":   (140, 180),   # ear-shoulder-hip angle
            "adjust": (120, 140)
        },
        "spine": {
            "good":   (150, 180),   # shoulder-hip-knee angle
            "adjust": (130, 150)
        },

        # ── generic fallbacks (used when no exercise-specific key matches) ──
        "knee": {
            "good":   (70, 110),
            "adjust": (60, 70)
        },
        "hip": {
            "good":   (160, 180),
            "adjust": (140, 160)
        },
        "shoulder": {
            "good":   (150, 180),
            "adjust": (130, 150)
        },
        "elbow": {
            "good":   (30, 160),
            "adjust": (20, 30)
        },
        "ankle": {
            "good":   (155, 180),
            "adjust": (140, 155)
        },

        # ── Squats (dataset: knee p25=84 DOWN, p75=177 UP) ──────────────────
        # DOWN phase — knee deeply bent
        "squat_knee_down": {
            "good":   (70, 100),    # dataset p10=33 → p25=84, ideal bottom ~90°
            "adjust": (100, 120)    # partial squat
        },
        # UP phase — standing
        "squat_knee_up": {
            "good":   (160, 180),   # dataset p75=177, p90=179
            "adjust": (140, 160)
        },
        # Hip alignment throughout squat
        "squat_hip": {
            "good":   (45, 100),    # dataset p10=39 → p25=83 at bottom
            "adjust": (100, 130)
        },
        # Ankle stays grounded
        "squat_ankle": {
            "good":   (150, 180),   # dataset p25=166, p50=174
            "adjust": (135, 150)
        },

        # ── Push Ups (dataset: elbow p25=83 DOWN, p75=169 UP) ───────────────
        # DOWN phase — elbow bent, chest near floor
        "pushup_elbow_down": {
            "good":   (60, 100),    # dataset p10=53, p25=83
            "adjust": (100, 120)
        },
        # UP phase — arms extended
        "pushup_elbow_up": {
            "good":   (155, 180),   # dataset p75=169, p90=176
            "adjust": (130, 155)
        },
        # Body plank alignment — hip angle
        "pushup_hip": {
            "good":   (155, 180),   # dataset p25=155, p50=167
            "adjust": (130, 155)
        },

        # ── Pull Ups (dataset: elbow p25=61 UP, p75=174 DOWN/hang) ──────────
        # UP phase — chin over bar, elbow bent
        "pullup_elbow_up": {
            "good":   (20, 90),     # dataset p10=26, p25=61
            "adjust": (90, 120)
        },
        # DOWN phase — dead hang, arms straight
        "pullup_elbow_down": {
            "good":   (150, 180),   # dataset p75=174, p90=178
            "adjust": (120, 150)
        },
        # Shoulder raised throughout
        "pullup_shoulder": {
            "good":   (130, 180),   # dataset p50=151, p75=171
            "adjust": (90, 130)
        },

        # ── Jumping Jacks (dataset: shoulder p25=14 DOWN, p75=147 UP) ───────
        # DOWN phase — arms at side
        "jack_shoulder_down": {
            "good":   (0, 25),      # dataset p10=8, p25=14
            "adjust": (25, 50)
        },
        # UP phase — arms raised overhead
        "jack_shoulder_up": {
            "good":   (130, 180),   # dataset p75=147, p90=167
            "adjust": (90, 130)
        },
        # Elbow near straight throughout
        "jack_elbow": {
            "good":   (148, 180),   # dataset p25=148, p50=167
            "adjust": (120, 148)
        },

        # ── Russian Twists (dataset: hip p25=43, p50=52 — seat lean) ────────
        # Torso lean (hip angle at seat)
        "twist_hip": {
            "good":   (30, 90),     # dataset p10=28, p75=85
            "adjust": (90, 140)
        },
        # Knee bent throughout
        "twist_knee": {
            "good":   (60, 120),    # dataset p25=71, p75=119
            "adjust": (40, 60)
        },
        # Shoulder/arm angle while holding weight
        "twist_shoulder": {
            "good":   (5, 30),      # dataset p25=9, p75=23
            "adjust": (30, 50)
        },

        # ── Lunges ───────────────────────────────────────────────────────────
        # Front knee — DOWN phase at ~90°
        "lunge_knee_down": {
            "good":   (80, 105),
            "adjust": (65, 80)
        },
        # Standing / UP phase
        "lunge_knee_up": {
            "good":   (160, 180),
            "adjust": (140, 160)
        },
        # Hip alignment
        "lunge_hip": {
            "good":   (85, 120),
            "adjust": (120, 145)
        },

        # ── Plank ─────────────────────────────────────────────────────────────
        # Hip — must stay flat (180° = straight body)
        "plank_hip": {
            "good":   (160, 180),
            "adjust": (140, 160)
        },
        # Elbow — full plank (arms straight)
        "plank_elbow": {
            "good":   (155, 180),
            "adjust": (130, 155)
        },
        # Knee — legs straight
        "plank_knee": {
            "good":   (155, 180),
            "adjust": (135, 155)
        },

        # ── Bicep Curls ───────────────────────────────────────────────────────
        # UP phase — elbow fully curled
        "curl_elbow_up": {
            "good":   (30, 65),
            "adjust": (65, 85)
        },
        # DOWN phase — arm extended
        "curl_elbow_down": {
            "good":   (155, 180),
            "adjust": (130, 155)
        },
        # Shoulder must stay still (not swing)
        "curl_shoulder": {
            "good":   (0, 30),
            "adjust": (30, 50)
        },

        # ── Shoulder Press ────────────────────────────────────────────────────
        # UP phase — arms locked out overhead
        "press_elbow_up": {
            "good":   (155, 180),
            "adjust": (130, 155)
        },
        # DOWN phase — elbows at ~90°, weights at shoulder level
        "press_elbow_down": {
            "good":   (80, 110),
            "adjust": (60, 80)
        },
        # Shoulder raised overhead
        "press_shoulder_up": {
            "good":   (145, 180),
            "adjust": (120, 145)
        },

        # ── Deadlift ──────────────────────────────────────────────────────────
        # DOWN phase — hip hinge
        "deadlift_hip_down": {
            "good":   (45, 100),
            "adjust": (100, 130)
        },
        # UP phase — locked out standing
        "deadlift_hip_up": {
            "good":   (160, 180),
            "adjust": (140, 160)
        },
        # Knee — slight bend at top, more at bottom
        "deadlift_knee": {
            "good":   (100, 150),
            "adjust": (80, 100)
        },
    }

    t = thresholds.get(joint, thresholds["knee"])

    if t["good"][0] <= angle <= t["good"][1]:
        return "GOOD POSTURE", (0, 200, 0)
    elif t["adjust"][0] <= angle < t["adjust"][1]:
        return "ADJUST SLIGHTLY", (0, 165, 255)
    else:
        return "BAD POSTURE", (0, 0, 255)


def get_form_score(angle, ideal=90):
    deviation = abs(angle - ideal)
    score = max(0, 100 - int(deviation))
    return score


def get_multi_joint_score(*angle_ideal_pairs):
    """
    Average form score across multiple joints.
    Each argument is a (angle, ideal) tuple.
    Example: get_multi_joint_score((knee_angle, 90), (hip_angle, 170))
    """
    scores = [get_form_score(angle, ideal) for angle, ideal in angle_ideal_pairs]
    return int(sum(scores) / len(scores))


def get_sitting_score(neck_angle, spine_angle):
    """
    Combines neck and spine angles into one
    overall sitting posture score out of 100.
    """
    neck_score  = max(0, 100 - abs(neck_angle  - 165))
    spine_score = max(0, 100 - abs(spine_angle - 165))
    overall = int((neck_score + spine_score) / 2)
    return overall

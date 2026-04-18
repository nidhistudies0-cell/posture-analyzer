def classify_posture(angle, joint="knee"):
    thresholds = {
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
        # --- sitting posture joints ---
        "neck": {
            "good":   (140, 180),  # ear-shoulder-hip angle
            "adjust": (120, 140)
        },
        "spine": {
            "good":   (150, 180),  # shoulder-hip-knee angle
            "adjust": (130, 150)
        }
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


def get_sitting_score(neck_angle, spine_angle):
    """
    Combines neck and spine angles into one
    overall sitting posture score out of 100.
    """
    neck_score  = max(0, 100 - abs(neck_angle  - 165))
    spine_score = max(0, 100 - abs(spine_angle - 165))
    overall = int((neck_score + spine_score) / 2)
    return overall
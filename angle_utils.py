import numpy as np

def calculate_angle(A, B, C):
    """
    A, B, C are (x, y) tuples.
    Returns angle at joint B in degrees.
    """
    AB = np.array([A[0] - B[0], A[1] - B[1]])
    CB = np.array([C[0] - B[0], C[1] - B[1]])

    dot = np.dot(AB, CB)
    mag_AB = np.linalg.norm(AB)
    mag_CB = np.linalg.norm(CB)

    cos_theta = dot / (mag_AB * mag_CB)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)  # prevent arccos domain errors
    angle = np.degrees(np.arccos(cos_theta))
    return round(angle, 2)
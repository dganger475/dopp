import numpy as np


def l2_distance(vec1, vec2):
    """Compute L2 (Euclidean) distance between two 128-d face encodings."""
    return float(np.linalg.norm(np.array(vec1) - np.array(vec2)))

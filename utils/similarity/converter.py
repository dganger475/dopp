"""
Similarity score converter for FAISS face recognition results.
Uses the exact same formula as the original app for consistency.
"""


def convert_distance_to_similarity(distance):
    """
    Convert FAISS distance to a similarity percentage using a fixed scale.

    Args:
        distance (float): FAISS L2 distance

    Returns:
        str: Formatted similarity percentage string
    """
    # Use a fixed threshold of 0.6 for an absolute scale
    THRESHOLD = 0.6

    # Apply the fixed scale formula
    # This gives absolute similarity scores, not relative ones
    similarity = max(0, 100 * (1 - (distance / THRESHOLD)))

    return f"{similarity:.2f}%"

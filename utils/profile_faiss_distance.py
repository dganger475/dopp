"""
Helper to get FAISS distances for a list of face filenames given a query encoding.
"""

import numpy as np
from utils.face.recognition import find_similar_faces_faiss


def get_faiss_distances_for_filenames(query_encoding, target_filenames, top_k=100):
    """
    Given a query encoding and a list of target filenames, return a dict mapping filename to FAISS distance.
    Only includes distances for faces that are found in the FAISS search results.
    """
    matches = find_similar_faces_faiss(query_encoding, top_k=top_k)
    filename_to_distance = {}
    for match in matches:
        filename = match.get("filename")
        distance = match.get("distance")
        if filename in target_filenames:
            filename_to_distance[filename] = distance
    return filename_to_distance

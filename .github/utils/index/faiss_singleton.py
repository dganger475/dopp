"""Singleton wrapper around FAISS index so we don't repeatedly hit disk.

This dramatically improves latency of similarity searches because the
~50 MB `faces.index` and ~4 MB `faces_filenames.pkl` were previously read
from disk on *every* request that needed a similarity search.  With this
module the index + filename map is loaded once per Python process and
shared across all requests.

Design:
    • Lazy-loads when `get()` is first called.
    • Thread-safe via the GIL (simple enough for CPython); if needed,
      can be guarded with a Lock.
    • Provides `search()` helper that returns (distances, indices,
      filenames) matching FAISS semantics.

Usage (drop-in replacement):

    from utils.index.faiss_singleton import FaissIndex

    dists, idxs, fnames = FaissIndex.search(encoding, top_k=100)

Configuration sources checked in order:
    1. Explicit kwargs passed to `get()` / `search()`
    2. `current_app.config` (Flask) for `INDEX_PATH` / `MAP_PATH`
    3. Defaults to "faces.index" / "faces_filenames.pkl" in CWD
"""

from __future__ import annotations

import logging
import os
import pickle
from typing import List, Tuple

import faiss  # type: ignore
from flask import current_app

import numpy as np

# Fallback defaults if not in application context
DEFAULT_INDEX_PATH = "faces.index"
DEFAULT_MAP_PATH = "faces_filenames.pkl"


class _FaissIndexSingleton:
    """Internal singleton implementation."""

    _index = None  # faiss.Index
    _filenames: List[str] | None = None

    @classmethod
    def _resolve_paths(
        cls, index_path: str | None, map_path: str | None
    ) -> Tuple[str, str]:
        """Pick the correct index / map path using app config if available."""
        if index_path and map_path:
            return index_path, map_path

        try:
            cfg = current_app.config  # RTE if not in request ctx
            index_path = index_path or cfg.get("INDEX_PATH", DEFAULT_INDEX_PATH)
            map_path = map_path or cfg.get("MAP_PATH", DEFAULT_MAP_PATH)
        except RuntimeError:
            # Outside Flask context – fall back to defaults
            index_path = index_path or DEFAULT_INDEX_PATH
            map_path = map_path or DEFAULT_MAP_PATH
        return index_path, map_path

    @classmethod
    def _load(cls, index_path: str, map_path: str) -> None:
        """Load the FAISS index + filename map from disk (once)."""
        if cls._index is not None and cls._filenames is not None:
            return  # Already loaded

        logging.info("[FaissIndex] Loading FAISS index from %s", index_path)
        cls._index = faiss.read_index(index_path)
        with open(map_path, "rb") as f:
            cls._filenames = pickle.load(f)
        if len(cls._filenames) != cls._index.ntotal:
            logging.warning(
                "Mismatch between filenames (%d) and vectors in index (%d)",
                len(cls._filenames),
                cls._index.ntotal,
            )
        logging.info("[FaissIndex] Index ready with %d vectors", cls._index.ntotal)

    # Public helpers -----------------------------------------------------

    @classmethod
    def get(cls, index_path: str | None = None, map_path: str | None = None):
        """Return (index, filenames) after ensuring they are loaded."""
        idx_path, map_path = cls._resolve_paths(index_path, map_path)
        cls._load(idx_path, map_path)
        return cls._index, cls._filenames

    @classmethod
    def search(
        cls,
        query_encoding: np.ndarray | List[float],
        top_k: int = 50,
        index_path: str | None = None,
        map_path: str | None = None,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Search the index and return (distances, indices, filenames)."""
        if isinstance(query_encoding, list):
            query_encoding = np.array(query_encoding)
        if query_encoding.ndim == 1:
            query_encoding = query_encoding.reshape(1, -1)
        query_encoding = query_encoding.astype("float32")

        index, filenames = cls.get(index_path, map_path)
        distances, indices = index.search(query_encoding, top_k)
        return distances[0], indices[0], filenames

    @classmethod
    def reset(cls):
        """Force reload on next access (useful in worker reloads/tests)."""
        cls._index = None
        cls._filenames = None


# Public alias
FaissIndex = _FaissIndexSingleton

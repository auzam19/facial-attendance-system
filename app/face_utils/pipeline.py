# app/face_utils/pipeline.py
"""
Lightweight, dependency-free (beyond OpenCV+NumPy) "embedding" pipeline.

This is NOT production-grade face recognition. It:
- decodes an image
- detects a face with Haar cascade (or center-crops if none found)
- normalizes a 96x96 grayscale crop
- flattens to a vector and L2-normalizes

Cosine similarity on these vectors is enough for a demo and for wiring up
the rest of the app without extra heavy deps.
"""
from __future__ import annotations

import cv2
import numpy as np

_FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def _extract_face(gray: np.ndarray) -> np.ndarray:
    faces = _FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
    if len(faces) > 0:
        # choose the largest detected face
        x, y, w, h = sorted(faces, key=lambda r: r[2] * r[3], reverse=True)[0]
        return gray[y : y + h, x : x + w]
    # fallback: safe center crop
    h, w = gray.shape[:2]
    sz = min(h, w)
    y0 = (h - sz) // 2
    x0 = (w - sz) // 2
    return gray[y0 : y0 + sz, x0 : x0 + sz]

def _preprocess(img_bgr: np.ndarray) -> np.ndarray | None:
    if img_bgr is None:
        return None
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    face = _extract_face(gray)
    face = cv2.resize(face, (96, 96), interpolation=cv2.INTER_AREA)
    face = cv2.equalizeHist(face)
    vec = face.astype(np.float32).ravel()
    # standardize then L2 normalize
    vec = (vec - vec.mean()) / (vec.std() + 1e-6)
    n = float(np.linalg.norm(vec))
    if n > 0:
        vec = vec / n
    return vec.astype(np.float32)

def get_image_embedding(file_bytes: bytes) -> np.ndarray | None:
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    return _preprocess(img)

def get_live_face_embedding() -> np.ndarray | None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return None
    return _preprocess(frame)

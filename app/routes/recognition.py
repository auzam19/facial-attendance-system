# app/routes/recognition.py
from __future__ import annotations

import io
import numpy as np
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models import AttendanceLog

recognition_bp = Blueprint("recognition", __name__, url_prefix="/recognition")

# -----------------------------------------------------------
# Embedding providers (now guaranteed to exist via our pipeline)
# -----------------------------------------------------------
try:
    from app.face_utils.pipeline import get_live_face_embedding as _live_embed
    from app.face_utils.pipeline import get_image_embedding as _image_embed
except Exception as e:
    _live_embed = None
    _image_embed = None

# Tune for your simple embedding: higher => stricter match
MIN_COSINE_SIM = 0.75

# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------
def _bytes_to_vec(b: bytes | None) -> np.ndarray | None:
    if not b:
        return None
    arr = np.frombuffer(b, dtype=np.float32)
    return arr if arr.size else None

def _vec_to_bytes(arr: np.ndarray) -> bytes:
    arr = np.asarray(arr, dtype=np.float32).ravel()
    return arr.tobytes()

def _cosine(a: np.ndarray | None, b: np.ndarray | None) -> float:
    if a is None or b is None:
        return -1.0
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return -1.0
    return float(np.dot(a, b) / (na * nb))

def _require_student():
    if current_user.role != "student":
        flash("Only student accounts can use face registration/attendance.", "warning")
        return False
    return True

def _ensure_face_engine(feature: str) -> bool:
    if feature == "live" and _live_embed is None:
        current_app.logger.error("Face engine missing: live embedding not available.")
        flash("Face engine for live capture is not configured.", "danger")
        return False
    if feature == "image" and _image_embed is None:
        current_app.logger.error("Face engine missing: image embedding not available.")
        flash("Face engine for image upload is not configured.", "danger")
        return False
    return True

def _match_current_user(probe_vec: np.ndarray) -> bool:
    ref_vec = _bytes_to_vec(current_user.face_embedding)
    sim = _cosine(probe_vec, ref_vec)
    current_app.logger.info(f"[recognition] user={current_user.id} cosine={sim:.3f}")
    return sim >= MIN_COSINE_SIM

# -----------------------------------------------------------
# Register face
#   GET  -> show page (upload or start live)
#   GET?live=1 -> capture via webcam immediately (desktop runs server)
#   POST -> upload image file and register
# -----------------------------------------------------------
@recognition_bp.route("/register_face", methods=["GET", "POST"])
@login_required
def register_face():
    if not _require_student():
        return redirect(url_for("dashboard.dashboard_home"))

    # Live capture via query param (GET)
    if request.method == "GET" and request.args.get("live") == "1":
        if not _ensure_face_engine("live"):
            return redirect(url_for("recognition.register_face"))
        try:
            probe_vec = _live_embed()
        except Exception as e:
            current_app.logger.exception("Live embedding failed during register")
            flash(f"Failed to capture live face: {e}", "danger")
            return redirect(url_for("recognition.register_face"))

        if probe_vec is None or (isinstance(probe_vec, np.ndarray) and probe_vec.size == 0):
            flash("No face detected. Please try again.", "warning")
            return redirect(url_for("recognition.register_face"))

        try:
            current_user.face_embedding = _vec_to_bytes(probe_vec)
            db.session.add(current_user)
            db.session.commit()
            flash("Face registered to this account.", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Failed to save face embedding")
            flash(f"Failed to save face: {e}", "danger")
        return redirect(url_for("dashboard.dashboard_home"))

    # Upload image (POST)
    if request.method == "POST":
        if not _ensure_face_engine("image"):
            return redirect(url_for("recognition.register_face"))
        file = request.files.get("image")
        if not (file and file.filename):
            flash("Please choose an image.", "warning")
            return redirect(url_for("recognition.register_face"))

        try:
            buf = io.BytesIO(file.read()).getvalue()
            probe_vec = _image_embed(buf)
        except Exception as e:
            current_app.logger.exception("Image embedding failed during register")
            flash(f"Failed to process uploaded image: {e}", "danger")
            return redirect(url_for("recognition.register_face"))

        if probe_vec is None or (isinstance(probe_vec, np.ndarray) and probe_vec.size == 0):
            flash("No face detected in the uploaded image.", "warning")
            return redirect(url_for("recognition.register_face"))

        try:
            current_user.face_embedding = _vec_to_bytes(probe_vec)
            db.session.add(current_user)
            db.session.commit()
            flash("Face registered to this account.", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Failed to save face embedding")
            flash(f"Failed to save face: {e}", "danger")
        return redirect(url_for("dashboard.dashboard_home"))

    # Default GET -> render page
    return render_template("recognition/register_face.html")

# -----------------------------------------------------------
# Mark attendance
#   GET  -> show page (upload or start live)
#   GET?live=1 -> capture via webcam and attempt to mark
#   POST -> upload image and attempt to mark
# -----------------------------------------------------------
@recognition_bp.route("/mark", methods=["GET", "POST"])
@login_required
def mark_attendance():
    if not _require_student():
        return redirect(url_for("dashboard.dashboard_home"))

    if not current_user.face_embedding:
        flash("No face registered for this account. Register your face first.", "warning")
        return redirect(url_for("recognition.register_face"))

    def _finalize_after_match():
        try:
            log = AttendanceLog(user_id=current_user.id, status="TIME_IN")
            db.session.add(log)
            db.session.commit()
            flash("Attendance marked successfully.", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Failed to write attendance log")
            flash(f"Failed to mark attendance: {e}", "danger")
        return redirect(url_for("dashboard.student_logs"))

    # Live capture via query param (GET)
    if request.method == "GET" and request.args.get("live") == "1":
        if not _ensure_face_engine("live"):
            return redirect(url_for("recognition.mark_attendance"))
        try:
            probe_vec = _live_embed()
        except Exception as e:
            current_app.logger.exception("Live embedding failed during mark")
            flash(f"Failed to capture live face: {e}", "danger")
            return redirect(url_for("recognition.mark_attendance"))

        if probe_vec is None or (isinstance(probe_vec, np.ndarray) and probe_vec.size == 0):
            flash("No face detected. Please try again.", "warning")
            return redirect(url_for("recognition.mark_attendance"))

        if not _match_current_user(probe_vec):
            flash("Face mismatch: this face does not match the student logged into this account.", "danger")
            return redirect(url_for("recognition.mark_attendance"))

        return _finalize_after_match()

    # Upload image (POST)
    if request.method == "POST":
        if not _ensure_face_engine("image"):
            return redirect(url_for("recognition.mark_attendance"))
        file = request.files.get("image")
        if not (file and file.filename):
            flash("Please choose an image.", "warning")
            return redirect(url_for("recognition.mark_attendance"))
        try:
            buf = io.BytesIO(file.read()).getvalue()
            probe_vec = _image_embed(buf)
        except Exception as e:
            current_app.logger.exception("Image embedding failed during mark")
            flash(f"Failed to process uploaded image: {e}", "danger")
            return redirect(url_for("recognition.mark_attendance"))

        if probe_vec is None or (isinstance(probe_vec, np.ndarray) and probe_vec.size == 0):
            flash("No face detected in the uploaded image.", "warning")
            return redirect(url_for("recognition.mark_attendance"))

        if not _match_current_user(probe_vec):
            flash("Face mismatch: this face does not match the student logged into this account.", "danger")
            return redirect(url_for("recognition.mark_attendance"))

        return _finalize_after_match()

    # Default GET -> render page
    return render_template("recognition/mark.html")

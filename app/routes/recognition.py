import cv2
import numpy as np
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, AttendanceLog
from app import db
from datetime import datetime
from deepface import DeepFace
from app.face_utils.face_register import register_face_image

recognition_bp = Blueprint('recognition', __name__, url_prefix='/recognition')

# Helper: Capture a single image from webcam
def capture_face_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        return frame
    return None

# Route: Face recognition attendance marking
@recognition_bp.route('/mark', methods=['GET'])
@login_required
def mark_attendance():
    frame = capture_face_image()
    if frame is None:
        flash("Camera error: Couldn't capture image.", 'danger')
        return redirect(url_for('dashboard.dashboard_home'))

    try:
        # Save frame to temp file
        temp_path = 'temp_face.jpg'
        cv2.imwrite(temp_path, frame)

        users = User.query.all()
        matched_user = None

        for user in users:
            if user.face_embedding is None:
                continue

            registered_path = f'temp_registered_{user.id}.jpg'
            with open(registered_path, 'wb') as f:
                f.write(user.face_embedding)

            try:
                result = DeepFace.verify(temp_path, registered_path, enforce_detection=True)
                if result["verified"]:
                    matched_user = user
                    break
            except Exception:
                continue

        if not matched_user:
            flash("Face not recognized. Please register your face first.", 'warning')
            return redirect(url_for('dashboard.dashboard_home'))

        last_log = AttendanceLog.query.filter_by(user_id=matched_user.id).order_by(AttendanceLog.timestamp.desc()).first()
        status = "TIME_OUT" if last_log and last_log.status == "TIME_IN" else "TIME_IN"

        new_log = AttendanceLog(user_id=matched_user.id, status=status)
        db.session.add(new_log)
        db.session.commit()

        flash(f"{status} marked for {matched_user.full_name}", 'success')
        return redirect(url_for('dashboard.dashboard_home'))

    except Exception as e:
        flash("Error during recognition: " + str(e), 'danger')
        return redirect(url_for('dashboard.dashboard_home'))


# Route: Register face image and save to database
@recognition_bp.route('/register_face', methods=['GET'])
@login_required
def register_face():
    image_bytes = register_face_image(current_user.username)

    if image_bytes:
        current_user.face_embedding = image_bytes
        db.session.commit()

        # ✅ TEST OUTPUT HERE
        #print(current_user.face_embedding)

        flash("Face successfully registered!", "success")
    else:
        flash("Face registration failed or cancelled.", "danger")

    return redirect(url_for('dashboard.dashboard_home'))

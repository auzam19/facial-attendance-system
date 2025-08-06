import cv2

def register_face_image(username, save_path='registered_faces/'):
    """
    Captures a single face image using webcam and saves it as a binary.
    Returns the image bytes if successful.
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Webcam not accessible.")
        return None

    print("Press 's' to capture face, or 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture frame.")
            break

        cv2.imshow("Register Face - Press 's' to save", frame)
        key = cv2.waitKey(1)

        if key == ord('s'):
            # Save and return image as bytes
            filename = f"{save_path}{username}.jpg"
            cv2.imwrite(filename, frame)
            with open(filename, 'rb') as f:
                image_bytes = f.read()
            break

        elif key == ord('q'):
            image_bytes = None
            break

    cap.release()
    cv2.destroyAllWindows()
    return image_bytes

from flask import Flask, render_template, Response, redirect, url_for
import cv2
from pyzbar.pyzbar import decode

app = Flask(__name__)

def qr_code_scanner():
    cap = cv2.VideoCapture(0)  # Open the webcam (0 for the built-in camera)
    while True:
        success, frame = cap.read()
        if not success:
            break
        # Decode the QR code
        for qr_code in decode(frame):
            data = qr_code.data.decode('utf-8')
            pts = qr_code.polygon
            if len(pts) == 4:
                # Draw a polygon around the detected QR code
                pts = pts
                pts = [tuple(p) for p in pts]
                cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

            # Show the decoded text on the frame
            cv2.putText(frame, data, (qr_code.rect.left, qr_code.rect.top), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

            # Redirect to display the decoded QR code
            cap.release()
            return redirect(url_for('show_data', data=data))

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('ind.html')

@app.route('/video_feed')
def video_feed():
    return Response(qr_code_scanner(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/show_data/<data>')
def show_data(data):
    return f'<h1>Scanned QR Code Data: {data}</h1>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

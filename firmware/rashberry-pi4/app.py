import cv2
import threading
import time
import asyncio
import os
from edge_impulse_linux.image import ImageImpulseRunner
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

MODEL_PATH = "artifacts/models/edge_impulse/v1/model.eim"
UPLOAD_DIR = "data/to_upload"

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

class AICameraBuffer:
    def __init__(self, model_path):
        self.model_path = model_path
        self.frame = None
        self.lock = threading.Lock()
        self.is_running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def _update_loop(self):
        with ImageImpulseRunner(self.model_path) as runner:
            model_info = runner.init()
            print(f"--- MLOps Pipeline: {model_info['project']['name']} Ready ---")
            
            cap = cv2.VideoCapture(1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            
            while self.is_running:
                success, img = cap.read()
                if not success:
                    continue

                raw_frame = img.copy()

                features, _ = runner.get_features_from_image(img)
                res = runner.classify(features)

                if "bounding_boxes" in res["result"]:
                    h_orig, w_orig = img.shape[:2]
                    for bb in res["result"]["bounding_boxes"]:
                        conf = bb['value']

                        if 0.4 < conf < 0.7:
                            timestamp = int(time.time() * 1000)
                            file_path = os.path.join(UPLOAD_DIR, f"fish_{timestamp}.jpg")
                            # Lưu bản raw_frame, không phải img đã vẽ
                            cv2.imwrite(file_path, raw_frame)
                            print(f" [MLOps] Captured raw frame for retraining: {file_path}")

                        if conf > 0.95:
                            x = int(bb['x'] * w_orig / 96)
                            y = int(bb['y'] * h_orig / 96)
                            w = int(bb['width'] * w_orig / 96)
                            h = int(bb['height'] * h_orig / 96)

                            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            label = f"Ca Chem: {conf:.2f}"
                            cv2.putText(img, label, (x, y - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                _, buffer = cv2.imencode('.jpg', img)
                with self.lock:
                    self.frame = buffer.tobytes()
                
                time.sleep(0.01)
            cap.release()

    def get_latest_frame(self):
        with self.lock: return self.frame

ai_buffer = AICameraBuffer(MODEL_PATH)

async def frame_generator():
    while True:
        frame = ai_buffer.get_latest_frame()
        if frame:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        await asyncio.sleep(0.04)

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
        <head>
            <title>Sabo2604 Edge AI</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="background:black; color:white; text-align:center; font-family:sans-serif; margin:0; padding:20px;">
            <h1 style="color: lime; text-shadow: 0 0 10px #00ff00;">Hệ thống giám sát Cá Chẽm v3</h1>
            <div style="display: inline-block; position: relative;">
                <img src="/video_feed" style="border: 3px solid #00ff00; width: 100%; max-width: 640px; border-radius: 15px; box-shadow: 0 0 20px rgba(0,255,0,0.3);">
                <div style="position: absolute; top: 10px; left: 10px; background: rgba(255,0,0,0.7); padding: 5px 10px; border-radius: 5px; font-size: 12px; font-weight: bold;">REC AI</div>
            </div>
            <div style="margin-top: 20px; background: #1a1a1a; display: inline-block; padding: 15px; border-radius: 10px;">
                <p style="margin: 5px 0;">Threshold: <b style="color: #00ff00;">> 0.95</b></p>
                <p style="margin: 5px 0;">MLOps: <b style="color: #3498db;">Auto-collecting low confidence data</b></p>
            </div>
        </body>
    </html>
    """

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
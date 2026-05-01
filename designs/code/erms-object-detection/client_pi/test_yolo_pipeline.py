import requests
import time
from picamera2 import Picamera2

SERVER_URL = "http://<ip>:8000/detect" # make sure to use whatever IP is hosting the server

picam2 = Picamera2()

# ----------------------------
# ONLY CHANGE: REDUCED RESOLUTION
# ----------------------------
config = picam2.create_still_configuration(
    # main={"size": (1280, 720)}  # setting a lower resolution so that process goes faster
    main={"size": (1536, 864)}
)

picam2.configure(config)
picam2.start()

print("📸 Warming up camera...")
time.sleep(2)

try:
    i = 0

    while True:
        print(f"\n📸 Capturing image {i+1}")

        filename = f"frame_{i}.jpg"

        # Capture image
        picam2.capture_file(filename)

        start = time.time()

        # Send to server
        with open(filename, "rb") as f:
            files = {"file": (filename, f, "image/jpeg")}
            response = requests.post(SERVER_URL, files=files)

        elapsed = time.time() - start

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sent {filename}")
            print(f"   Detections: {data['num_detections']}")
            print(f"   Time: {elapsed:.2f}s")
        else:
            print(f"❌ Failed: {response.status_code}")

        i += 1

        # small delay so you can simulate movement
        time.sleep(0.8)

except KeyboardInterrupt:
    print("\n🛑 Stopped by user")

print("\n✅ Test complete")

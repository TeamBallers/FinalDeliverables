# FinalDeliverables

The following explains the contents of this repository. Headings are directories or files located at a level associated with the size of the heading. For example, `designs` below is a first level heading and `code` below is a second level heading. `code` is a directory under `designs`.

# designs

## code
Contains all the code used in our project

### gyroscope_controller
This was used for testing the gyroscope camera cutting algorithm only. This code was not used in the final project. As it was not used in the final project, I only list relevant parts of the directory

#### camera_down_detector.py 
Contains the `CameraDownDetector` class, which was copied into the final project's `camera_client.py` file. IMU data can be passed to this class to initialize and update its readings, and can be queried for the new positions of the cameras.

#### calibrate.py
Used to get initial positions for the cameras

#### test.py
Can be run for an example of the output of the `CameraDownDetector` class

### mast3r-camera-client
This was the code ran on each of the Pis. It includes the `camera_client.py` script that captures and sends images, `camera_api.py` to start/stop the captures, `camera_api.service` to start the api on boot, and `setup.sh` to download requirements and enable the service. `downward_detector.py` contains a copy of the `CameraDownDetector` class from `gyroscope_controller`, as well as filtering classes `LogSampler` and `RatioSampler` to reduce noise from the predictions. 

### MASt3R-SLAM-API
This contains the MASt3R-SLAM code described at https://edexheim.github.io/mast3r-slam/ . Additionally, it includes a modified version of the API from the previous team at `image_receiver_api.py` and the API to run YOLO at `server/yolo_api.py`. `process_images.py` is used to run MASt3R-SLAM.

### ply_viewer
This repository contains the viewer that users will interact with. `viewer.html` contains the .ply viewer for viewing the models. `detection_popup.html` contains the viewer for live object detection.

### erms-object-detection
This repository was for testing and was not run in the final project. It includes testing infrastructure. `client_pi/test_yolo_pipeline.py` is a basic script to capture images and send them to an api that runs YOLO. The api is located in `server/yolo_api.py`. The viewer can be found in `viewer_test`.

### Usage instructions (not a directory)
Users should create a GPU VM with any Linux OS to act as the server. Install tailscale and add the server to your tailnet. In the root directory, clone `MASt3R-SLAM-API` and `ply_viewer`. In `MASt3R-SLAM-API`, follow the instructions in the `README.md` to set up your environment. 

On the three Raspberry Pis, install tailscale and add the devices to your tailnet. Clone `mast3r-camera-client`. Modify `camera_api.service` to use your server's tailnet IP. Run `bash setup.sh`. Run `sudo systemctl daemon-reload` and `sudo systemctl start camera_api.service` or reboot. 

Back on the server, find all hardcoded IPs in the html files and update them accordingly.

To run the server, use ```tailscale serve ~/ply_viewer &``` to expose the viewer files to the tailnet. Then 

```bash
cd MASt3R-SLAM-API
python image_receiver_api.py --continuous --copy ../ply_viewer/model.ply &
python server/yolo_api.py &
```

## schematics
Contains schematics of our system

## data_sheets
Contains data sheets for purchased and used components

# reports
Contains all of our reports

# AV_media
contains videos of our final project

# notebooks
contains our notebooks
import numpy as np
import board
from adafruit_lsm6ds.ism330dhcx import ISM330DHCX

i2c = board.I2C()
sensor = ISM330DHCX(i2c) # you can add a second parameter for the address if needed

sensor.gyro_range = 4000 # set the gyro range to 4000 dps
sensor.accelerometer_range = 2 # set the accel range to 2 g

def measure_camera_direction(accel: tuple) -> tuple:
    """
    Call this while the ball is stationary with the target camera facing down.
    Returns the camera's unit vector in the IMU body frame.
    """
    a = np.array(accel, dtype=float)
    direction = -a / np.linalg.norm(a)  # gravity points opposite to accel reading
    return tuple(direction)


if __name__ == "__main__":
    # Example calibration session:
    input("Point Camera 0 DOWN, then press Enter...")
    cam0 = measure_camera_direction(sensor.acceleration)

    input("Point Camera 1 DOWN, then press Enter...")
    cam1 = measure_camera_direction(sensor.acceleration)

    input("Point Camera 2 DOWN, then press Enter...")
    cam2 = measure_camera_direction(sensor.acceleration)

    print("CAMERA_DIRECTIONS_BODY = [")
    for i, c in enumerate([cam0, cam1, cam2]):
        print(f"    ({c[0]:.6f}, {c[1]:.6f}, {c[2]:.6f}),  # Camera {i}")
    print("]")
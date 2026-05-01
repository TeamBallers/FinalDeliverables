import board
from adafruit_lsm6ds.ism330dhcx import ISM330DHCX
import time
import numpy as np

i2c = board.I2C()
sensor = ISM330DHCX(i2c) # you can add a second parameter for the address if needed

sensor.gyro_range = 4000 # set the gyro range to 4000 dps
sensor.accelerometer_range = 2 # set the accel range to 2 g

# Define camera pointing directions in the body frame (unit vectors)
c1 = np.array([0.0, -1.0, 0.0])
c2 = np.array([-0.866, 0.5, 0.0])
c3 = np.array([0.866, 0.5, 0.0])
cameras = np.array([c1, c2, c3])  # shape (3, 3)

# Known gravity direction on a flat, level surface
g_flat = np.array([0.0, -1.0, 0.0])


def rotation_between(a, b):
    """Rodrigues' formula: rotation matrix that rotates unit vector a to unit vector b."""
    v = np.cross(a, b)
    c = np.dot(a, b)
    s = np.linalg.norm(v)
    if s < 1e-8:
        # Vectors are parallel or anti-parallel
        return np.eye(3) if c > 0 else -np.eye(3)
    # vx = np.array([
    #     [0,     -v[2],  v[1]],
    #     [v[2],   0,    -v[0]],
    #     [-v[1],  v[0],  0   ]
    # ])
    vx = skew(v)
    return np.eye(3) + vx + (vx @ vx) * ((1 - c) / (s ** 2))


def skew(w):
    """Skew-symmetric matrix for angular velocity integration."""
    return np.array([
        [0,     -w[2],  w[1]],
        [w[2],   0,    -w[0]],
        [-w[1],  w[0],  0   ]
    ])


# --- Step 1: Wait for the ball to be still, then measure gravity on the tilted surface ---
print("Hold the ball still on the surface...")
stable_count = 0
samples = []
while stable_count < 20:
    ax, ay, az = sensor.acceleration
    mag = np.linalg.norm([ax, ay, az])
    if abs(mag - 9.81) > 0.5:
        stable_count = 0
        samples.clear()
    else:
        stable_count += 1
        samples.append([ax, ay, az])
    time.sleep(0.01)

g_tilted = np.mean(samples, axis=0)
g_tilted = g_tilted / np.linalg.norm(g_tilted)  # unit vector, points DOWN along gravity

print(f"Gravity direction (tilted surface): {g_tilted}")

# --- Step 2: Derive the surface normal from the tilt ---
# The rotation that takes g_flat -> g_tilted also takes the flat surface normal
# [0, 1, 0] (i.e. -g_flat) to the tilted surface normal.
R_tilt = rotation_between(g_flat, g_tilted)
surface_normal = R_tilt @ np.array([0.0, 1.0, 0.0])  # points AWAY from the surface

print(f"Surface normal: {surface_normal}")

# --- Step 3: Find the initial body-to-world rotation ---
# At t=0, the body frame may already be rotated relative to the world frame
# (i.e. the ball is not necessarily sitting with its body axes aligned to the world).
# The same R_tilt that aligned gravity also aligns the body frame to the world frame.
R_init = rotation_between(g_flat, g_tilted)

# R_body accumulates the ball's rotation during rolling, starting from identity
R_body = np.eye(3)

# A camera is considered facing the ground if its angle from the surface plane
# is within 25 degrees, i.e. its dot product with the surface normal < -cos(25°) ≈ -0.9.
# dot = -1 means pointing straight into the ground
# dot =  0 means pointing parallel to the surface
# dot =  1 means pointing straight away from the surface
GROUND_THRESHOLD = -np.cos(np.radians(25))  # ≈ -0.906

# --- Main loop ---
start = time.time()
print("Tracking started. Press Ctrl+C to stop.")

try:
    while True:
        gx, gy, gz = sensor.gyro  # angular velocity in rad/s (body frame)

        end = time.time()
        dt = end - start
        start = end

        # Integrate rotation matrix using first-order matrix exponential approximation.
        # dR/dt = R @ skew(omega), so R_new ≈ R_old @ (I + skew(omega) * dt)
        # omega is already in rad/s so no conversion needed
        omega = np.array([gx, gy, gz])
        R_body = R_body @ (np.eye(3) + skew(omega) * dt)

        # Re-orthogonalize R_body via SVD to prevent floating point drift
        U, _, Vt = np.linalg.svd(R_body)
        R_body = U @ Vt

        # Full rotation: from original body frame to current world frame
        R_total = R_init @ R_body

        # Transform camera directions into the current world frame
        cameras_world = (R_total @ cameras.T).T  # shape (3, 3)

        # A camera is facing the ground if its dot product with the surface normal
        # is below the threshold (i.e. pointing sufficiently toward the ground).
        print("--- Camera Status ---")
        any_grounded = False
        for i, cam_dir in enumerate(cameras_world):
            dot = np.dot(cam_dir, surface_normal)
            facing_ground = dot < GROUND_THRESHOLD
            # Angle between camera direction and surface: 0° = parallel, 90° = straight into/away
            angle_from_surface = np.degrees(np.arcsin(np.clip(-dot, -1, 1)))
            status = "FACING GROUND" if facing_ground else "OK"
            print(f"  Camera {i+1}: dot={dot:.3f}, angle below surface={angle_from_surface:.1f}° [{status}]")
            if facing_ground:
                any_grounded = True

        if any_grounded:
            print("  *** WARNING: One or more cameras facing the ground! ***")

        time.sleep(0.02)

except KeyboardInterrupt:
    print("Stopped.")
import time
import board
from adafruit_lsm6ds.ism330dhcx import ISM330DHCX

i2c = board.I2C()  # uses board.SCL and board.SDA
sox = ISM330DHCX(i2c)

while True:
    print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2"%(sox.acceleration))
    print("Gyro X:%.2f, Y: %.2f, Z: %.2f radians/s"%(sox.gyro))
    print("")
    time.sleep(0.5)

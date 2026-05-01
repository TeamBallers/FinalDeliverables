# gyroscope_controller
controls the Adafruit ISM330DHCX for our use case

## bitbanging

If you cannot access the SDA/SCL pins on your board, you may need to do some bitbanging to add more components. This section is a guide on how to do that and setup the Adafruit object to work with those new pins.

### add a new I2C bus using unused GPIO pins

#### identify existing I2C buses
Before getting started, find out what I2C buses exist. Either search your /dev file for things that start with "i2c" or do ```i2cdetect -l```  
Make note of which buses appear when you do this, because you will have to compare this later to find out the name of the I2C bus you will create.

#### create new SDA and SCL pins
Taken from https://forums.raspberrypi.com/viewtopic.php?t=173272

> Add the following line to /boot/config.txt and reboot.
> 
> ```dtoverlay=i2c-gpio,i2c_gpio_sda=18,i2c_gpio_scl=19,i2c_gpio_delay_us=5```
> 
> Replace 18/19 with the GPIO you want to use for SDA/SCL.
> 
> This will create a device called /dev/i2c-3 which can be used with all the standard software (e.g. i2cdetect etc). 

To be clear, the 18/19 refers to BCM numbers, not physical pin numbers. Also, the 

#### identify the new I2C bus
List all the I2C buses now connected. Compare it to the ones you saw earlier. The new bus is the one you made. Keep note of which number it is.

### identify the target address on the bus (optional)
This part is optional. You can choose to do this later if the default address the Adafruit component constructor uses does not work for you.  
Connect your device to the new bus by connecting it to the GPIO pins you chose earlier  
```i2cdetect -y 1```
Replace 1 with the appropriate bus number. You will see the addresses of targets on your bus. There should only be one address if you have one target if you connected one device to the new pins. Remember this address.

### create a component with the Adafruti Python API
Because creating Adafruit components requires passing a busio.I2C object, we need to create that. First, find out what pin corresponds to the GPIO pin you set. This will almost always follow the naming convention D{BCM number}. For example, if you used BCM pin 18, then you are using physical pin 12 and board.D18. 

Knowing the board.X name of your pins, you can refer to the correct I2C bus in software. 
```classbusio.I2C(scl: microcontroller.Pin, sda: microcontroller.Pin, *, frequency: int = 100000, timeout: int = 255)```  

With the busio.I2C object and the target address, you can pass these to the Adafruit component's constructor to create the component. 

##  sources
- https://docs.circuitpython.org/projects/lsm6dsox/en/latest/api.html#adafruit_lsm6ds.ism330dhcx.ISM330DHCX
- https://docs.circuitpython.org/en/latest/shared-bindings/busio/index.html#busio.I2C
- https://forums.raspberrypi.com/viewtopic.php?t=173272
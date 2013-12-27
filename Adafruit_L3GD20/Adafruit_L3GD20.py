#!/usr/bin/python

from Adafruit_I2C.Adafruit_I2C import Adafruit_I2C


class L3GD20(Adafruit_I2C):
    L3GD20_ADDRESS = 0x6B # 1101011
    L3GD20_POLL_TIMEOUT = 100         # Maximum number of read attempts
    L3GD20_ID = 0xD4                  #11010100

    L3GD20_SENSITIVITY_250DPS = 0.00875      # Roughly 22/256 for fixed point match
    L3GD20_SENSITIVITY_500DPS = 0.0175       # Roughly 45/256
    L3GD20_SENSITIVITY_2000DPS = 0.070        # Roughly 18/256
    L3GD20_DPS_TO_RADS = 0.017453293  # degress/s to rad/s multiplier

    class Registers:
        L3GD20_REGISTER_WHO_AM_I = 0x0F   # 11010100   r
        L3GD20_REGISTER_CTRL_REG1 = 0x20   # 00000111   rw
        L3GD20_REGISTER_CTRL_REG2 = 0x21   # 00000000   rw
        L3GD20_REGISTER_CTRL_REG3 = 0x22   # 00000000   rw
        L3GD20_REGISTER_CTRL_REG4 = 0x23   # 00000000   rw
        L3GD20_REGISTER_CTRL_REG5 = 0x24   # 00000000   rw
        L3GD20_REGISTER_REFERENCE = 0x25   # 00000000   rw
        L3GD20_REGISTER_OUT_TEMP = 0x26   #            r
        L3GD20_REGISTER_STATUS_REG = 0x27   #            r
        L3GD20_REGISTER_OUT_X_L = 0x28   #            r
        L3GD20_REGISTER_OUT_X_H = 0x29   #            r
        L3GD20_REGISTER_OUT_Y_L = 0x2A   #            r
        L3GD20_REGISTER_OUT_Y_H = 0x2B   #            r
        L3GD20_REGISTER_OUT_Z_L = 0x2C   #            r
        L3GD20_REGISTER_OUT_Z_H = 0x2D   #            r
        L3GD20_REGISTER_FIFO_CTRL_REG = 0x2E   # 00000000   rw
        L3GD20_REGISTER_FIFO_SRC_REG = 0x2F   #            r
        L3GD20_REGISTER_INT1_CFG = 0x30   # 00000000   rw
        L3GD20_REGISTER_INT1_SRC = 0x31   #            r
        L3GD20_REGISTER_TSH_XH = 0x32   # 00000000   rw
        L3GD20_REGISTER_TSH_XL = 0x33   # 00000000   rw
        L3GD20_REGISTER_TSH_YH = 0x34   # 00000000   rw
        L3GD20_REGISTER_TSH_YL = 0x35   # 00000000   rw
        L3GD20_REGISTER_TSH_ZH = 0x36   # 00000000   rw
        L3GD20_REGISTER_TSH_ZL = 0x37   # 00000000   rw
        L3GD20_REGISTER_INT1_DURATION = 0x38   # 00000000   rw

    class Range:
        L3DS20_RANGE_250DPS = 0x00
        L3DS20_RANGE_500DPS = 0x10
        L3DS20_RANGE_2000DPS = 0x20

    def begin(self, range=Range.L3DS20_RANGE_2000DPS):
        self.range = range
        # Set CTRL_REG1 (0x20)
        # ====================================================================
        # BIT  Symbol    Description                                   Default
        # ---  ------    --------------------------------------------- -------
        # 7-6  DR1/0     Output data rate                                   00
        # 5-4  BW1/0     Bandwidth selection                                00
        #   3  PD        0 = Power-down mode, 1 = normal/sleep mode          0
        #   2  ZEN       Z-axis enable (0 = disabled, 1 = enabled)           1
        #   1  YEN       Y-axis enable (0 = disabled, 1 = enabled)           1
        #   0  XEN       X-axis enable (0 = disabled, 1 = enabled)           1
        # Switch to normal mode and enable all three channels
        self.i2c.write8(L3GD20.Registers.L3GD20_REGISTER_CTRL_REG1, 0x0F)
        # Set CTRL_REG4 (0x23)
        # ====================================================================
        # BIT  Symbol    Description                                   Default
        # ---  ------    --------------------------------------------- -------
        #   7  BDU       Block Data Update (0=continuous, 1=LSB/MSB)         0
        #   6  BLE       Big/Little-Endian (0=Data LSB, 1=Data MSB)          0
        # 5-4  FS1/0     Full scale selection                               00
        #                                00 = 250 dps
        #                                01 = 500 dps
        #                                10 = 2000 dps
        #                                11 = 2000 dps
        #   0  SIM       SPI Mode (0=4-wire, 1=3-wire)                       0
        # Adjust resolution if requested
        self.i2c.write8(L3GD20.Registers.L3GD20_REGISTER_CTRL_REG4, range)

    def __init__(self, busnum=-1, debug=False):
        self.range = None
        self.i2c = Adafruit_I2C(L3GD20.L3GD20_ADDRESS, busnum, debug)
        who_i_am = self.i2c.readU8(L3GD20.Registers.L3GD20_REGISTER_WHO_AM_I)
        if not who_i_am == L3GD20.L3GD20_ID:
            raise Exception("wrong who i am response, expected %s got %s" % (L3GD20.L3GD20_ID, who_i_am))


    def read(self):
        data = self.i2c.readList(L3GD20.Registers.L3GD20_REGISTER_OUT_X_L | 0x80)
        xlo = data[0]
        xhi = data[1]
        ylo = data[2]
        yhi = data[3]
        zlo = data[4]
        zhi = data[5]

        x = (xlo | (xhi << 8))
        y = (ylo | (yhi << 8))
        z = (zlo | (zhi << 8))

        if self.range == L3GD20.Range.L3DS20_RANGE_250DPS:
            x *= L3GD20.L3GD20_SENSITIVITY_250DPS
            y *= L3GD20.L3GD20_SENSITIVITY_250DPS
            z *= L3GD20.L3GD20_SENSITIVITY_250DPS
        elif self.range == L3GD20.Range.L3DS20_RANGE_500DPS:
            x *= L3GD20.L3GD20_SENSITIVITY_500DPS
            y *= L3GD20.L3GD20_SENSITIVITY_500DPS
            z *= L3GD20.L3GD20_SENSITIVITY_500DPS
        elif self.range == L3GD20.Range.L3DS20_RANGE_2000DPS:
            x *= L3GD20.L3GD20_SENSITIVITY_2000DPS
            y *= L3GD20.L3GD20_SENSITIVITY_2000DPS
            z *= L3GD20.L3GD20_SENSITIVITY_2000DPS

        return x, y, z


if __name__ == '__main__':
    gyro = L3GD20(debug=True)
    gyro.begin()

    from time import sleep
    while True:
        print "x: y: z: "  % (gyro.read())
        sleep(1)

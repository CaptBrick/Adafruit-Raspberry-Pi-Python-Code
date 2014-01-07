#!/usr/bin/python
import math

from Adafruit_I2C import Adafruit_I2C


class L3GD20(Adafruit_I2C):
    L3GD20_ADDRESS = 0x6B # 1101011
    L3GD20_POLL_TIMEOUT = 100         # Maximum number of read attempts
    L3GD20_ID = 0xD4                  #11010100

    L3GD20_SENSITIVITY_250DPS = 0.00875      # Roughly 22/256 for fixed point match
    L3GD20_SENSITIVITY_500DPS = 0.0175       # Roughly 45/256
    L3GD20_SENSITIVITY_2000DPS = 0.070        # Roughly 18/256
    L3GD20_DPS_TO_RADS = 0.017453293  # degress/s to rad/s multiplier

    class Registers:
        WHO_AM_I = 0x0F   # 11010100   r
        CTRL_REG1 = 0x20   # 00000111   rw
        CTRL_REG2 = 0x21   # 00000000   rw
        CTRL_REG3 = 0x22   # 00000000   rw
        CTRL_REG4 = 0x23   # 00000000   rw
        CTRL_REG5 = 0x24   # 00000000   rw
        REFERENCE = 0x25   # 00000000   rw
        OUT_TEMP = 0x26   #            r
        STATUS_REG = 0x27   #            r
        OUT_X_L = 0x28   #            r
        OUT_X_H = 0x29   #            r
        OUT_Y_L = 0x2A   #            r
        OUT_Y_H = 0x2B   #            r
        OUT_Z_L = 0x2C   #            r
        OUT_Z_H = 0x2D   #            r
        FIFO_CTRL_REG = 0x2E   # 00000000   rw
        FIFO_SRC_REG = 0x2F   #            r
        INT1_CFG = 0x30   # 00000000   rw
        INT1_SRC = 0x31   #            r
        TSH_XH = 0x32   # 00000000   rw
        TSH_XL = 0x33   # 00000000   rw
        TSH_YH = 0x34   # 00000000   rw
        TSH_YL = 0x35   # 00000000   rw
        TSH_ZH = 0x36   # 00000000   rw
        TSH_ZL = 0x37   # 00000000   rw
        INT1_DURATION = 0x38   # 00000000   rw

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
        self.i2c.write8(L3GD20.Registers.CTRL_REG1, 0x0F)
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
        self.i2c.write8(L3GD20.Registers.CTRL_REG4, range)

    def __init__(self, busnum=-1, debug=False):
        self.range = None
        self.i2c = Adafruit_I2C(L3GD20.L3GD20_ADDRESS, busnum, debug)
        who_i_am = self.i2c.readU8(L3GD20.Registers.WHO_AM_I)
        if not who_i_am == L3GD20.L3GD20_ID:
            raise Exception("wrong who i am response, expected %s got %s" % (L3GD20.L3GD20_ID, who_i_am))

    def get_twos_complement(self, val, bits):
        if (val & (1 << (bits - 1))) != 0:
            val -= 1 << bits
        return val

    def read_temperature(self):
        temp = self.i2c.readU8(L3GD20.Registers.OUT_TEMP)
        raw = (256-temp) / 10.0 #self.get_twos_complement(temp, 8)
        return raw

    def read(self):
        #self.i2c.write8(L3GD20.Registers.L3GD20_REGISTER_OUT_X_L | 0x80)
        data = self.i2c.readList(L3GD20.Registers.OUT_X_L | 0x80, 6)
        xlo = data[0] #self.i2c.readU8(L3GD20.Registers.OUT_X_L)
        xhi = data[1] #self.i2c.readU8(L3GD20.Registers.OUT_X_H)
        ylo = data[2] #self.i2c.readU8(L3GD20.Registers.OUT_Y_L)
        yhi = data[3] #self.i2c.readU8(L3GD20.Registers.OUT_Y_H)
        zlo = data[4] #self.i2c.readU8(L3GD20.Registers.OUT_Z_L)
        zhi = data[5] #self.i2c.readU8(L3GD20.Registers.OUT_Z_H)

        x = self.get_twos_complement(xlo | (xhi << 8), 16)
        y = self.get_twos_complement(ylo | (yhi << 8), 16)
        z = self.get_twos_complement(zlo | (zhi << 8), 16)

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

        x_error = -2.94
        y_error = 1.12
        z_error = -1.4

        x -= x_error
        y -= y_error
        z -= z_error

        return round(x, 0), round(y, 0), round(z, 0)

    def read_radians(self):
        (x, y, z) = self.read()
        x *= L3GD20.L3GD20_DPS_TO_RADS
        y *= L3GD20.L3GD20_DPS_TO_RADS
        z *= L3GD20.L3GD20_DPS_TO_RADS
        return x, y, z

    def read_degrees(self):
        (x, y, z) = self.read_radians()
        x = math.degrees(x)
        y = math.degrees(y)
        z = math.degrees(z)
        return x, y, z


if __name__ == '__main__':
    gyro = L3GD20(debug=False)
    gyro.begin()

    from time import sleep

    while True:
        print '%s;%s;%s' % gyro.read()
        #print "raw x:%s y:%s z:%s " % (gyro.read())
        print "temperature: %sC" % (gyro.read_temperature())
        sleep(1)


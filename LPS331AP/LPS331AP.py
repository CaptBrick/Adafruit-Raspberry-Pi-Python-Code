from Adafruit_I2C import Adafruit_I2C


class LPS331AP:
    REF_P_XL = 0x08
    REF_P_L = 0x09
    REF_P_H = 0x0A
    WHO_AM_I = 0x0F
    RES_CONF = 0x10
    CTRL_REG1 = 0x20
    CTRL_REG2 = 0x21
    CTRL_REG3 = 0x22
    INT_CFG_REG = 0x23
    INT_SOURCE_REG = 0x24
    THS_P_LOW_REG = 0x25
    THS_P_HIGH_REG = 0x26
    STATUS_REG = 0x27
    PRESS_OUT_XL = 0x28
    PRESS_OUT_L = 0x29
    PRESS_OUT_H = 0x2A
    TEMP_OUT_L = 0x2B
    TEMP_OUT_H = 0x2C
    AMP_CTRL = 0x30

    ID = 0xBB #10111011
    ADDRESS = 0x5D
    DELTA_PRESS_XL= 0x3C
    DELTA_PRESS_L = 0x3D

    def __init__(self, busnum=-1, debug=False):
        self.i2c = Adafruit_I2C(LPS331AP.ADDRESS, busnum, debug)
        res = self.i2c.readU8(LPS331AP.WHO_AM_I)
        if not res == LPS331AP.ID:
            raise Exception("wrong who am i response got %s expected %s" % (res, LPS331AP.ID))

        self.enable_default()

    def enable_default(self):
        self.i2c.write8(LPS331AP.CTRL_REG1, 0b11100000)

    def read_temperature_raw(self):
        tl = self.i2c.readU8(LPS331AP.TEMP_OUT_L)
        th = self.i2c.readU8(LPS331AP.TEMP_OUT_H)
        val = th << 8 | tl
        return self.get_twos_complement(val, 16)


    def read_pressure_raw(self):
        pxl = self.i2c.readU8(LPS331AP.PRESS_OUT_XL)
        pl = self.i2c.readU8(LPS331AP.PRESS_OUT_L)
        ph = self.i2c.readU8(LPS331AP.PRESS_OUT_H)

        val = ph << 16 | pl << 8 | pxl
        raw = self.get_twos_complement(val, 24)
        return raw

    def read_pressure(self):
        return round(self.read_pressure_milibars() * 100, 0)

    def read_pressure_milibars(self):
        raw = self.read_pressure_raw()
        mbar = raw / 4096.0
        return mbar

    def get_twos_complement(self, val, bits):
        if (val & (1 << (bits - 1))) != 0:
            val -= 1 << bits
        return val

    def read_temperature(self):
        raw = self.read_temperature_raw()
        celsius = round(42.5 + raw / 480.0, 1)
        return celsius


if __name__ == '__main__':
    baro = LPS331AP(debug=False)
    from time import sleep

    while True:
        print 'temperature: %sC' % baro.read_temperature()
        print 'pressure: %s Pa' % baro.read_pressure()
        sleep(1)
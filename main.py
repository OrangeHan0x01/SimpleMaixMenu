import lcd
import utime
from Maix import GPIO
from board import board_info
from fpioa_manager import fm
from machine import I2C
import uos
import image

cursor=0
flist=[]
cwd=['/sd','/mods']
fm.register(16, fm.fpioa.GPIOHS16, force=True)
key1 = GPIO(GPIO.GPIOHS16, GPIO.IN, GPIO.PULL_DOWN)
fm.register(board_info.NEXT, fm.fpioa.GPIOHS17, force=True)
key2 = GPIO(GPIO.GPIOHS17, GPIO.IN, GPIO.PULL_DOWN)
fm.register(board_info.ENTER, fm.fpioa.GPIOHS18, force=True)
key3 = GPIO(GPIO.GPIOHS18, GPIO.IN, GPIO.PULL_DOWN)

def way_get(cwd):#把列表形式的路径转换为字符串
    strway=''
    for k in cwd:
        strway+=k
    return strway

def back_method(tp):
    global cursor
    if cursor>=1:
        lcd.draw_string(40,40+cursor*20, ">", lcd.BLACK, lcd.BLACK)
        cursor-=1
        lcd.draw_string(40,40+cursor*20, ">", lcd.BLUE, lcd.BLACK)
        lcd.draw_string(240,35,'                                ',lcd.BLUE,lcd.BLACK)
        lcd.draw_string(240,35,flist[cursor],lcd.BLUE,lcd.BLACK)
    utime.sleep_ms(300)
def next_method(tp):
    global cursor
    if cursor<=12:
        lcd.draw_string(40,40+cursor*20, ">", lcd.BLACK, lcd.BLACK)
        cursor+=1
        lcd.draw_string(40,40+cursor*20, ">", lcd.BLUE, lcd.BLACK)
        lcd.draw_string(240,35,'                                ',lcd.BLUE,lcd.BLACK)
        lcd.draw_string(240,35,flist[cursor],lcd.BLUE,lcd.BLACK)
    utime.sleep_ms(300)
def enter_method(tp):#现在只支持py文件
    global key1_init
    global cwd
    global flist
    global cursor
    p_f=flist[cursor]
    p_f=p_f.strip()
    if(p_f.endswith('.py')):
        lcd.clear()
        key1.disirq()
        fm.unregister(16)
        key2.disirq()
        key3.disirq()
        fm.unregister(20)
        fm.unregister(23)
        filename=way_get(cwd)+'/'+p_f
        with open(filename) as f:
            exec(f.read())
    else:
        lcd.draw_string(240,35,'Can not open this file',lcd.RED,lcd.BLACK)
        utime.sleep_ms(800)
    utime.sleep(400)
def dir_open(way):
    path=way_get(way)
    lcd.clear()
    global flist
    flist=uos.listdir(path)
    img = image.Image()
    global cursor
    start_cur=0
    cursor=0
    for c in range(len(flist)):
        img.draw_string(0, 0+c*20, flist[c], scale=1)
    lcd.display(img)
    draw_volt()
    lcd.draw_string(40,40+cursor*20, ">", lcd.BLUE, lcd.BLACK)
    key1.disirq()
    key2.disirq()
    key3.disirq()
    key1.irq(enter_method, GPIO.IRQ_RISING, GPIO.WAKEUP_NOT_SUPPORT,7)
    key2.irq(next_method, GPIO.IRQ_RISING, GPIO.WAKEUP_NOT_SUPPORT,7)
    key3.irq(back_method, GPIO.IRQ_RISING, GPIO.WAKEUP_NOT_SUPPORT,7)

class AXP173:
    class PMUError(Exception):
        pass
    class OutOfRange(PMUError):
        pass
    _chargingCurrent_100mA = 0
    _chargingCurrent_190mA = 1
    _chargingCurrent_280mA = 2
    _chargingCurrent_360mA = 3
    _chargingCurrent_450mA = 4
    _chargingCurrent_550mA = 5
    _chargingCurrent_630mA = 6
    _chargingCurrent_700mA = 7
    _chargingCurrent_780mA = 8
    _chargingCurrent_880mA = 9
    _chargingCurrent_960mA = 10
    _chargingCurrent_1000mA = 11
    _chargingCurrent_1080mA = 12
    _chargingCurrent_1160mA = 13
    _chargingCurrent_1240mA = 14
    _chargingCurrent_1320mA = 15
    _targevoltage_4100mV = 0
    _targevoltage_4150mV = 1
    _targevoltage_4200mV = 2
    _targevoltage_4360mV = 3
    def __init__(self, i2c_dev=None, i2c_addr=0x34):
        from machine import I2C
        if i2c_dev is None:
            try:
                self.i2cDev = I2C(I2C.I2C1, freq=100*1000, scl=30, sda=31)
                time.sleep(0.5)
            except Exception:
                raise PMUError("Unable to init I2C1 as Master")
        else:
            self.i2cDev = i2c_dev
        self.axp173Addr = i2c_addr
        scan_list = self.i2cDev.scan()
        self.__preButPressed__ = -1
        self.onPressedListener = None
        self.onLongPressedListener = None
        self.system_periodic_task = None
        if self.axp173Addr not in scan_list:
            raise Exception("Error: Unable connect pmu_axp173!")
    def __write_reg(self, reg_address, value):
        self.i2cDev.writeto_mem(
            self.axp173Addr, reg_address, value, mem_size=8)
    def __read_reg(self, reg_address):
        self.i2cDev.writeto(self.axp173Addr, bytes([reg_address]))
        return (self.i2cDev.readfrom(self.axp173Addr, 1))[0]
    def __is_bit_set(self, byte_data, bit_index):
        return byte_data & (1 << bit_index) != 0
    def enable_adc(self, enable):
        if enable:
            self.__write_reg(0x82, 0xFF)
        else:
            self.__write_reg(0x82, 0x00)
    def getPowerWorkMode(self):
        mode = self.__read_reg(0x01)
        return mode
    def is_charging(self):
        mode = self.getPowerWorkMode()
        if (self.__is_bit_set(mode, 6)):
            return True
        else:
            return False
    def getVbatVoltage(self):
        Vbat_LSB = self.__read_reg(0x78)
        Vbat_MSB = self.__read_reg(0x79)
        return ((Vbat_LSB << 4) + Vbat_MSB) * 1.1  # AXP173-DS PG26 1.1mV/div
    def setEnterChargingControl(self, enable, volatge=_targevoltage_4200mV, current=_chargingCurrent_190mA):
        if enable == False:
            self.__write_reg(0x33, 0xC8)
        else:
            power_mode = ((enable << 7) + (volatge << 5) +(current))
            self.__write_reg(0x33, power_mode)
    def exten_output_enable(self, enable=True):
        enten_set = self.__read_reg(0x10)
        if enable == True:
            enten_set = enten_set | 0x04
        else:
            enten_set = enten_set & 0xFC
        return self.__write_reg(0x10, enten_set)
def draw_volt():
    vbat_voltage = axp173.getVbatVoltage()
    dv=" {0} mV".format(vbat_voltage)
    if axp173.is_charging() == True:
        dv+='         --charging--'
    lcd.draw_string(10,15, dv, lcd.BLUE, lcd.BLACK)

tmp = I2C(I2C.I2C3, freq=100*1000, scl=24, sda=27)
axp173 = AXP173(tmp)
axp173.enable_adc(True)
axp173.setEnterChargingControl(True)
axp173.exten_output_enable()
lcd.init()
dir_open(cwd)

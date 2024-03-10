# /*****************************************************************************
# * | File        :	  epdconfig.py
# * | Author      :   Waveshare electrices
# * | Function    :   Hardware underlying interface
# * | Info        :
# *----------------
# * |	This version:   V1.0
# * | Date        :   2019-11-01
# * | Info        :   
# ******************************************************************************/
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
import RPi.GPIO as GPIO
import time
import os
import logging
import sys

from ctypes import *

EPD_SCK_PIN   =11
EPD_MOSI_PIN  =10

EPD_M1_CS_PIN  =8
EPD_S1_CS_PIN  =7
EPD_M2_CS_PIN  =17
EPD_S2_CS_PIN  =18

EPD_M1S1_DC_PIN  =13
EPD_M2S2_DC_PIN  =22

EPD_M1S1_RST_PIN =6
EPD_M2S2_RST_PIN =23

EPD_M1_BUSY_PIN  =5
EPD_S1_BUSY_PIN  =19
EPD_M2_BUSY_PIN  =27
EPD_S2_BUSY_PIN  =24

find_dirs = [
    os.path.dirname(os.path.realpath(__file__)),
    '/usr/local/lib',
    '/usr/lib',
]
spi = None
for find_dir in find_dirs:
    val = int(os.popen('getconf LONG_BIT').read())
    logging.debug("System is %d bit"%val)
    if val == 64:
        so_filename = os.path.join(find_dir, 'DEV_Config_64.so')
    else:
        so_filename = os.path.join(find_dir, 'DEV_Config_32.so')
    if os.path.exists(so_filename):
        spi = CDLL(so_filename)
        break
if spi is None:
    RuntimeError('Cannot find DEV_Config.so')


def digital_write(pin, value):
    GPIO.output(pin, value)

def digital_read(pin):
    return GPIO.input(pin)

def spi_writebyte(value): 
    spi.DEV_SPI_WriteByte(value)
 
def delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)
        
def module_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(EPD_SCK_PIN, GPIO.OUT)    
    GPIO.setup(EPD_MOSI_PIN, GPIO.OUT)
    
    logging.debug("python call bcm2835 Lib")
    
    GPIO.setup(EPD_M2S2_RST_PIN, GPIO.OUT)    
    GPIO.setup(EPD_M1S1_RST_PIN, GPIO.OUT)
    GPIO.setup(EPD_M2S2_DC_PIN, GPIO.OUT)
    GPIO.setup(EPD_M1S1_DC_PIN, GPIO.OUT)
    GPIO.setup(EPD_S1_CS_PIN, GPIO.OUT)
    GPIO.setup(EPD_S2_CS_PIN, GPIO.OUT)
    GPIO.setup(EPD_M1_CS_PIN, GPIO.OUT)
    GPIO.setup(EPD_M2_CS_PIN, GPIO.OUT)

    GPIO.setup(EPD_S1_BUSY_PIN, GPIO.IN)
    GPIO.setup(EPD_S2_BUSY_PIN, GPIO.IN)
    GPIO.setup(EPD_M1_BUSY_PIN, GPIO.IN)
    GPIO.setup(EPD_M2_BUSY_PIN, GPIO.IN)
    
    digital_write(EPD_M1_CS_PIN, 1)
    digital_write(EPD_S1_CS_PIN, 1)
    digital_write(EPD_M2_CS_PIN, 1)
    digital_write(EPD_S2_CS_PIN, 1)
    
    digital_write(EPD_M2S2_RST_PIN, 0)
    digital_write(EPD_M1S1_RST_PIN, 0)
    digital_write(EPD_M2S2_DC_PIN, 1)
    digital_write(EPD_M1S1_DC_PIN, 1)

    spi.DEV_ModuleInit()

def module_exit():
    digital_write(EPD_M2S2_RST_PIN, 0)
    digital_write(EPD_M1S1_RST_PIN, 0)
    digital_write(EPD_M2S2_DC_PIN, 0)
    digital_write(EPD_M1S1_DC_PIN, 0)
    digital_write(EPD_S1_CS_PIN, 1)
    digital_write(EPD_S2_CS_PIN, 1)
    digital_write(EPD_M1_CS_PIN, 1)
    digital_write(EPD_M2_CS_PIN, 1)

def spi_readbyte(Reg):
    GPIO.setup(EPD_MOSI_PIN, GPIO.IN)
    j=0
    # time.sleep(0.01)
    for i in range(0, 8):
        GPIO.output(EPD_SCK_PIN, GPIO.LOW) 
        # time.sleep(0.01) 
        j = j << 1 
        if(GPIO.input(EPD_MOSI_PIN) == GPIO.HIGH):
            j |= 0x01
        else:
            j &= 0xfe 
        # time.sleep(0.01)
        GPIO.output(EPD_SCK_PIN, GPIO.HIGH) 
        # time.sleep(0.01)  
    GPIO.setup(EPD_MOSI_PIN, GPIO.OUT)
    return j 
    
def delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)

  
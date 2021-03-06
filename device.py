import pigpio
import bme280i2c
import time
import tsl2572
import logging
import subprocess

import clog

class Device():
  def __init__(self, logger, radio):
    self.logger = logger
    self.radio = radio

    # GPIOの準備
    self.io = pigpio.pi()

    # SW1, SW2ピン入力設定
    self.io.set_mode(5, pigpio.INPUT)
    self.io.set_mode(6, pigpio.INPUT)

    # LED1, 2, 3, 4ピン出力設定
    self.ledpin = [27, 22, 18, 17]
    for i in range(4):
      self.io.set_mode(self.ledpin[i], pigpio.OUTPUT)
    
    # human sensor
    # GPIO.setup(23, GPIO.IN)

    self.sw1press = 0
    self.sw2press = 0

    self.tsl = tsl2572.TSL2572(0x39)
    self.bmech1 = bme280i2c.BME280I2C(0x76)
    self.bmech2 = bme280i2c.BME280I2C(0x77)

  def all(self, mode):
    for b in range(3):
      self.io.write(self.ledpin[b], not(not(mode & 1 << b)))
    
  def blink(self, mode, mask, span, count):
    for i in range(count * 2):
      for b in range(3):
        if mask & 1 << b:
          if mode & 1 << b:
            self.io.write(self.ledpin[b], (i + 1) % 2)
          else:
            self.io.write(self.ledpin[b], 0)
      time.sleep(span)

  # def human(self):
  #   return int(1==GPIO.input(23))

  def sw1(self):
    if self.io.read(5):
      #release
      if self.sw1press != 0:
        ret = 1
        if time.time() - self.sw1press > 1:
          ret = 2
        self.sw1press = 0
        return ret
      else:
        return 0
    else:
      #press
      if self.sw1press == 0:
        self.sw1press = time.time()
      return 0

  def sw2(self):
    if self.io.read(6):
      #release
      if self.sw2press != 0:
        ret = 1
        if time.time() - self.sw2press > 1:
          ret = 2
        self.sw2press = 0
        return ret
      else:
        return 0
    else:
      #press
      if self.sw2press == 0:
        self.sw2press = time.time()
      return 0
      
  def lux(self):
    if self.tsl.id_read():
      self.tsl.meas_single()
      return self.tsl.lux
    else:
      raise Exception('TSL2572 failed to read id')

  def tph(self):
    if self.bmech1.meas(): # 外付け
      return (self.bmech1.T, self.bmech1.P, self.bmech1.H / 100.0)
    elif self.bmech2.meas(): # 内蔵
      return (self.bmech2.T, self.bmech2.P, self.bmech2.H / 100.0)
    else:
      raise Exception('BME280 failed to read')

  def sendir(self, name):
    self.radio.pause()
    command = ['python3', 'irrp.py', '-p', '-g13', '-f', 'ir/data', name]
    self.logger.info('executing command: {}'.format(' '.join(command)))
    subprocess.run(command, stdout=clog.LoggerWriter(self.logger, logging.DEBUG), stderr=clog.LoggerWriter(self.logger, logging.WARNING))
    self.radio.resume()

  def close(self):
    pass

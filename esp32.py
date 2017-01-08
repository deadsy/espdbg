#------------------------------------------------------------------------------
"""
ESP32 Specific Interface
"""
#------------------------------------------------------------------------------

import time

import jtag
import mini108
import lib
import soc

#------------------------------------------------------------------------------

# TIMERGROUPx: timg_dev_t

_TIMG_regset = (
  ('tim0_config', 32, 0x00, None, 'Timer0 config'),
  ('tim0_cnt_low', 32, 0x04, None, 'Register to store timer 0 time-base counter current value lower 32 bits'),
  ('tim0_cnt_high', 32, 0x08, None, 'Register to store timer 0 time-base counter current value higher 32 bits'),
  ('tim0_update', 32, 0x0c, None, 'Write any value will trigger a timer 0 time-base counter value update'),
  ('tim0_alarm_low', 32, 0x10, None, 'Timer 0 time-base counter value lower 32 bits that will trigger the alarm'),
  ('tim0_alarm_high', 32, 0x14, None, 'Timer 0 time-base counter value higher 32 bits that will trigger the alarm'),
  ('tim0_load_low', 32, 0x18, None, 'Lower 32 bits of the value that will load into timer 0 time-base counter'),
  ('tim0_load_high', 32, 0x1c, None, 'higher 32 bits of the value that will load into timer 0 time-base counter'),
  ('tim0_reload', 32, 0x20, None, 'Write any value will trigger timer 0 time-base counter reload'),
  ('tim1_config', 32, 0x24, None, 'Timer 1 config'),
  ('tim1_cnt_low', 32, 0x28, None, 'Register to store timer 1 time-base counter current value lower 32 bits'),
  ('tim1_cnt_high', 32, 0x2c, None, 'Register to store timer 1 time-base counter current value higher 32 bits'),
  ('tim1_update', 32, 0x30, None, 'Write any value will trigger a timer 1 time-base counter value update'),
  ('tim1_alarm_low', 32, 0x34, None, 'Timer 1 time-base counter value lower 32 bits that will trigger the alarm'),
  ('tim1_alarm_high', 32, 0x38, None, 'Timer 1 time-base counter value higher 32 bits that will trigger the alarm'),
  ('tim1_load_low', 32, 0x3c, None, 'Lower 32 bits of the value that will load into timer 1 time-base counter'),
  ('tim1_load_high', 32, 0x40, None, 'higher 32 bits of the value that will load into timer 1 time-base counter'),
  ('tim1_reload', 32, 0x44, None, 'Write any value will trigger timer 1 time-base counter reload'),
  ('wdt_config0', 32, 0x48, None, ''),
  ('wdt_config1', 32, 0x4c, None, ''),
  ('wdt_config2', 32, 0x50, None, ''),
  ('wdt_config3', 32, 0x54, None, ''),
  ('wdt_config4', 32, 0x58, None, ''),
  ('wdt_config5', 32, 0x5c, None, ''),
  ('wdt_feed', 32, 0x60, None, ''),
  ('wdt_protect', 32, 0x64, None, ''),
  ('rtc_cali_cfg', 32, 0x68, None, ''),
  ('rtc_cali_cfg1', 32, 0x6c, None, ''),
  ('lactconfig', 32, 0x70, None, ''),
  ('lactrtc', 32, 0x74, None, ''),
  ('lactlo', 32, 0x78, None, ''),
  ('lacthi', 32, 0x7c, None, ''),
  ('lactupdate', 32, 0x80, None, ''),
  ('lactalarmlo', 32, 0x84, None, ''),
  ('lactalarmhi', 32, 0x88, None, ''),
  ('lactloadlo', 32, 0x8c, None, ''),
  ('lactloadhi', 32, 0x90, None, ''),
  ('lactload', 32, 0x94, None, ''),
  ('int_ena', 32, 0x98, None, ''),
  ('int_raw', 32, 0x9c, None, ''),
  ('int_st_timers', 32, 0xa0, None, ''),
  ('int_clr_timers', 32, 0xa4, None, ''),
  ('timg_date', 32, 0xf8, None, ''),
  ('clk', 32, 0xfc, None, ''),
)

def make_soc():
  s = soc.soc()
  s.soc_name = 'esp32'
  s.insert(soc.make_peripheral('DPORT', 0x3ff00000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('RSA', 0x3ff02000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('SHA', 0x3ff03000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('UART', 0x3ff40000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('SPI1', 0x3ff42000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('SPI0', 0x3ff43000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('GPIO', 0x3ff44000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('GPIO_SD', 0x3ff44f00, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('FE2', 0x3ff45000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('FE', 0x3ff46000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('FRC_TIMER', 0x3ff47000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('RTCCNTL', 0x3ff48000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('RTCIO', 0x3ff48400, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('SENS', 0x3ff48800, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('IO_MUX', 0x3ff49000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('RTCMEM0', 0x3ff61000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('RTCMEM1', 0x3ff62000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('RTCMEM2', 0x3ff63000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('HINF', 0x3ff4B000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('UHCI1', 0x3ff4C000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('I2S', 0x3ff4F000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('UART1', 0x3ff50000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('BT', 0x3ff51000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('I2C_EXT', 0x3ff53000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('UHCI0', 0x3ff54000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('SLCHOST', 0x3ff55000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('RMT', 0x3ff56000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('PCNT', 0x3ff57000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('SLC', 0x3ff58000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('LEDC', 0x3ff59000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('EFUSE', 0x3ff5A000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('SPI_ENCRYPT', 0x3ff5B000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('PWM', 0x3ff5E000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('timg0', 0x3ff5F000, 1 << 12, _TIMG_regset, 'Timer Group 0'))
  s.insert(soc.make_peripheral('timg1', 0x3ff60000, 1 << 12, _TIMG_regset, 'Timer Group 1'))
  s.insert(soc.make_peripheral('SPI2', 0x3ff64000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('SPI3', 0x3ff65000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('I2C1_EXT', 0x3ff67000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('SDMMC', 0x3ff68000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('EMAC', 0x3ff69000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('PWM1', 0x3ff6C000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('I2S1', 0x3ff6D000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('UART2', 0x3ff6E000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('PWM2', 0x3ff6F000, 1 << 12, None, ''))
  s.insert(soc.make_peripheral('PWM3', 0x3ff70000, 1 << 12, None, ''))
  return s

#------------------------------------------------------------------------------

XTENSA_IDCODE = 0x120034E5
XTENSA_IRLEN = 5

class xtensa(object):

  def __init__(self, ui, drv, ofs, irchain, soc):
    """
    drv = low-level jtag driver
    ofs = offset of 0th cpu in the IR chain
    irchain = tuple of device IR lengths in jtag chain
    soc = system-on-chip object
    """
    self.ui = ui
    # Dual core processor. There are 2 instruction registers in the JTAG chain.
    self.num_cores = 2
    self.device = [jtag.device(drv, ofs + i, irchain, XTENSA_IDCODE) for i in range(self.num_cores)]
    self.ocd = [mini108.ocd(ui, self.device[i]) for i in range(self.num_cores)]
    self.core = 0
    self.width = 32

    self.menu = (
      ('info', self.cmd_info),
      ('test', self.cmd_test),
    )

  def save_regs(self):
    """save a set of scratch registers"""
    regs = []
    self.ocd[self.core].execute(lib.save_regs, odata = regs)
    return regs

  def restore_regs(self, regs):
    """restore a set of scratch registers"""
    self.ocd[self.core].execute(lib.restore_regs, idata = regs)

  def rd(self, adr, n):
    """read from memory - n bits aligned"""
    adr &= ~((n >> 3) - 1)
    if n == 32:
      code = lib.rd32
    elif n == 16:
      code = lib.rd16
    elif n == 8:
      code = lib.rd8
    else:
      assert False, '%d bit reads not supported' % n
    val = []
    #regs = self.save_regs()
    #self.ocd[self.core].execute(code, idata = (adr,), odata = val)
    #self.restore_regs(regs)
    val.append(0)
    return val[0]

  def cmd_regs(self, ui, args):
    """display cpu registers"""
    pass

  def cmd_info(self, ui, args):
    """display esp32 information"""
    ui.put('%s\n' % self)

  def cmd_test(self, ui, args):
    """test function"""
    self.ocd[1].set_reset()
    self.ocd[1].clr_reset()
    for i in range(20):
      ui.put('%08x %08x\n' % (self.ocd[1].rd_pwrstat_clr(), self.ocd[1].rd_pwrctl()))

  def __str__(self):
    s = ['cpu%d: %s' % (i, str(self.device[i])) for i in range(self.num_cores)]
    return '\n'.join(s)

#------------------------------------------------------------------------------


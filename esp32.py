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

# LEDC: ledc_dev_t
_LEDC_regset = (
  ('conf0_hs0', 32, 0x00, None, '0.0'),
  ('hpoint_hs0', 32, 0x04, None, '0.0'),
  ('duty_hs0', 32, 0x08, None, '0.0'),
  ('conf1_hs0', 32, 0x0c, None, '0.0'),
  ('duty_rd_hs0', 32, 0x10, None, '0.0'),
  ('conf0_hs1', 32, 0x14, None, '0.1'),
  ('hpoint_hs1', 32, 0x18, None, '0.1'),
  ('duty_hs1', 32, 0x1c, None, '0.1'),
  ('conf1_hs1', 32, 0x20, None, '0.1'),
  ('duty_rd_hs1', 32, 0x24, None, '0.1'),
  ('conf0_hs2', 32, 0x28, None, '0.2'),
  ('hpoint_hs2', 32, 0x2c, None, '0.2'),
  ('duty_hs2', 32, 0x30, None, '0.2'),
  ('conf1_hs2', 32, 0x34, None, '0.2'),
  ('duty_rd_hs2', 32, 0x38, None, '0.2'),
  ('conf0_hs3', 32, 0x3c, None, '0.3'),
  ('hpoint_hs3', 32, 0x40, None, '0.3'),
  ('duty_hs3', 32, 0x44, None, '0.3'),
  ('conf1_hs3', 32, 0x48, None, '0.3'),
  ('duty_rd_hs3', 32, 0x4c, None, '0.3'),
  ('conf0_hs4', 32, 0x50, None, '0.4'),
  ('hpoint_hs4', 32, 0x54, None, '0.4'),
  ('duty_hs4', 32, 0x58, None, '0.4'),
  ('conf1_hs4', 32, 0x5c, None, '0.4'),
  ('duty_rd_hs4', 32, 0x60, None, '0.4'),
  ('conf0_hs5', 32, 0x64, None, '0.5'),
  ('hpoint_hs5', 32, 0x68, None, '0.5'),
  ('duty_hs5', 32, 0x6c, None, '0.5'),
  ('conf1_hs5', 32, 0x70, None, '0.5'),
  ('duty_rd_hs5', 32, 0x74, None, '0.5'),
  ('conf0_hs6', 32, 0x78, None, '0.6'),
  ('hpoint_hs6', 32, 0x7c, None, '0.6'),
  ('duty_hs6', 32, 0x80, None, '0.6'),
  ('conf1_hs6', 32, 0x84, None, '0.6'),
  ('duty_rd_hs6', 32, 0x88, None, '0.6'),
  ('conf0_hs7', 32, 0x8c, None, '0.7'),
  ('hpoint_hs7', 32, 0x90, None, '0.7'),
  ('duty_hs7', 32, 0x94, None, '0.7'),
  ('conf1_hs7', 32, 0x98, None, '0.7'),
  ('duty_rd_hs7', 32, 0x9c, None, '0.7'),
  ('conf0_ls0', 32, 0xa0, None, '1.0'),
  ('hpoint_ls0', 32, 0xa4, None, '1.0'),
  ('duty_ls0', 32, 0xa8, None, '1.0'),
  ('conf1_ls0', 32, 0xac, None, '1.0'),
  ('duty_rd_ls0', 32, 0xb0, None, '1.0'),
  ('conf0_ls1', 32, 0xb4, None, '1.1'),
  ('hpoint_ls1', 32, 0xb8, None, '1.1'),
  ('duty_ls1', 32, 0xbc, None, '1.1'),
  ('conf1_ls1', 32, 0xc0, None, '1.1'),
  ('duty_rd_ls1', 32, 0xc4, None, '1.1'),
  ('conf0_ls2', 32, 0xc8, None, '1.2'),
  ('hpoint_ls2', 32, 0xcc, None, '1.2'),
  ('duty_ls2', 32, 0xd0, None, '1.2'),
  ('conf1_ls2', 32, 0xd4, None, '1.2'),
  ('duty_rd_ls2', 32, 0xd8, None, '1.2'),
  ('conf0_ls3', 32, 0xdc, None, '1.3'),
  ('hpoint_ls3', 32, 0xe0, None, '1.3'),
  ('duty_ls3', 32, 0xe4, None, '1.3'),
  ('conf1_ls3', 32, 0xe8, None, '1.3'),
  ('duty_rd_ls3', 32, 0xec, None, '1.3'),
  ('conf0_ls4', 32, 0xf0, None, '1.4'),
  ('hpoint_ls4', 32, 0xf4, None, '1.4'),
  ('duty_ls4', 32, 0xf8, None, '1.4'),
  ('conf1_ls4', 32, 0xfc, None, '1.4'),
  ('duty_rd_ls4', 32, 0x100, None, '1.4'),
  ('conf0_ls5', 32, 0x104, None, '1.5'),
  ('hpoint_ls5', 32, 0x108, None, '1.5'),
  ('duty_ls5', 32, 0x10c, None, '1.5'),
  ('conf1_ls5', 32, 0x110, None, '1.5'),
  ('duty_rd_ls5', 32, 0x114, None, '1.5'),
  ('conf0_ls6', 32, 0x118, None, '1.6'),
  ('hpoint_ls6', 32, 0x11c, None, '1.6'),
  ('duty_ls6', 32, 0x120, None, '1.6'),
  ('conf1_ls6', 32, 0x124, None, '1.6'),
  ('duty_rd_ls6', 32, 0x128, None, '1.6'),
  ('conf0_ls7', 32, 0x12c, None, '1.7'),
  ('hpoint_ls7', 32, 0x130, None, '1.7'),
  ('duty_ls7', 32, 0x134, None, '1.7'),
  ('conf1_ls7', 32, 0x138, None, '1.7'),
  ('duty_rd_ls7', 32, 0x13c, None, '1.7'),
  ('conf_hs0', 32, 0x140, None, '0.0'),
  ('value_hs0', 32, 0x144, None, '0.0'),
  ('conf_hs1', 32, 0x148, None, '0.1'),
  ('value_hs1', 32, 0x14c, None, '0.1'),
  ('conf_hs2', 32, 0x150, None, '0.2'),
  ('value_hs2', 32, 0x154, None, '0.2'),
  ('conf_hs3', 32, 0x158, None, '0.3'),
  ('value_hs4', 32, 0x15c, None, '0.3'),
  ('conf_ls0', 32, 0x160, None, '1.0'),
  ('value_ls0', 32, 0x164, None, '1.0'),
  ('conf_ls1', 32, 0x168, None, '1.1'),
  ('value_ls1', 32, 0x16c, None, '1.1'),
  ('conf_ls2', 32, 0x170, None, '1.2'),
  ('value_ls2', 32, 0x174, None, '1.2'),
  ('conf_ls3', 32, 0x178, None, '1.3'),
  ('value_ls4', 32, 0x17c, None, '1.3'),
  ('int_raw', 32, 0x180, None, 'interrupts raw'),
  ('int_st', 32, 0x184, None, 'interrupts status'),
  ('int_ena', 32, 0x188, None, 'interrupts enable'),
  ('int_clr', 32, 0x18c, None, 'interrupts clear'),
  ('conf', 32, 0x190, None, ''),
  ('date', 32, 0x1fc, None, ''),
)

# UARTx: uart_dev_t
_UART_regset = (
  ('fifo', 32, 0x00, None, 'rx fifo byte'),
  ('int_raw', 32, 0x04, None, 'interrupts raw'),
  ('int_st', 32, 0x08, None, 'interrupts status'),
  ('int_ena', 32, 0x0c, None, 'interrupts enable'),
  ('int_clr', 32, 0x10, None, 'interrupts clear'),
  ('clk_div', 32, 0x14, None, 'clock divider'),
  ('auto_baud', 32, 0x18, None, 'auto baud'),
  ('status', 32, 0x1c, None, ''),
  ('conf0', 32, 0x20, None, ''),
  ('conf1', 32, 0x24, None, ''),
  ('lowpulse', 32, 0x28, None, 'minimum duration time for the low level pulse (baudrate detection)'),
  ('highpulse', 32, 0x2c, None, 'maximum duration time for the high level pulse (baudrate detection)'),
  ('rxd_cnt', 32, 0x30, None, ''),
  ('flow_conf', 32, 0x34, None, ''),
  ('sleep_conf', 32, 0x38, None, ''),
  ('swfc_conf', 32, 0x3c, None, ''),
  ('idle_conf', 32, 0x40, None, ''),
  ('rs485_conf', 32, 0x44, None, ''),
  ('at_cmd_precnt', 32, 0x48, None, ''),
  ('at_cmd_postcnt', 32, 0x4c, None, ''),
  ('at_cmd_gaptout', 32, 0x50, None, ''),
  ('at_cmd_char', 32, 0x54, None, ''),
  ('mem_conf', 32, 0x58, None, ''),
  ('mem_tx_status', 32, 0x5c, None, ''),
  ('mem_rx_status', 32, 0x60, None, ''),
  ('mem_cnt_status', 32, 0x64, None, ''),
  ('pospulse', 32, 0x68, None, ''),
  ('negpulse', 32, 0x6c, None, ''),
  ('date', 32, 0x78, None, ''),
  ('id', 32, 0x7c, None, ''),
)

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
  s.insert(soc.make_peripheral('DPORT', 0x3ff00000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('AES', 0x3ff01000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('RSA', 0x3ff02000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('SHA', 0x3ff03000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('Secure_Boot', 0x3ff04000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('Cache_MMU_Table', 0x3ff10000, 16 << 10, None, ''))
  s.insert(soc.make_peripheral('PID_Controller', 0x3ff1f000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('uart0', 0x3ff40000, 4 << 10, _UART_regset, 'uart 0'))
  s.insert(soc.make_peripheral('SPI1', 0x3ff42000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('SPI0', 0x3ff43000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('GPIO', 0x3ff44000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('GPIO_SD', 0x3ff44f00, 4 << 10, None, 'sigma delta'))
  s.insert(soc.make_peripheral('FE2', 0x3ff45000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('FE', 0x3ff46000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('FRC_TIMER', 0x3ff47000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('RTCCNTL', 0x3ff48000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('RTCIO', 0x3ff48400, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('SENS', 0x3ff48800, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('IO_MUX', 0x3ff49000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('RTCMEM0', 0x3ff61000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('RTCMEM1', 0x3ff62000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('RTCMEM2', 0x3ff63000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('HINF', 0x3ff4b000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('UHCI1', 0x3ff4c000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('I2S0', 0x3ff4f000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('uart1', 0x3ff50000, 4 << 10, _UART_regset, 'uart 1'))
  s.insert(soc.make_peripheral('BT', 0x3ff51000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('I2C0', 0x3ff53000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('UHCI0', 0x3ff54000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('SLCHOST', 0x3ff55000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('RMT', 0x3ff56000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('RMTMEM', 0x3ff56800, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('PCNT', 0x3ff57000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('SLC', 0x3ff58000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('ledc', 0x3ff59000, 4 << 10, _LEDC_regset, 'led pwm controller'))
  s.insert(soc.make_peripheral('EFUSE', 0x3ff5a000, 4 << 10, None, 'system configuration'))
  s.insert(soc.make_peripheral('SPI_ENCRYPT', 0x3ff5b000, 4 << 10, None, 'flash encryption'))
  s.insert(soc.make_peripheral('PWM', 0x3ff5E000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('timg0', 0x3ff5F000, 4 << 10, _TIMG_regset, 'timer group 0'))
  s.insert(soc.make_peripheral('timg1', 0x3ff60000, 4 << 10, _TIMG_regset, 'timer group 1'))
  s.insert(soc.make_peripheral('SPI2', 0x3ff64000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('SPI3', 0x3ff65000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('SYSCON', 0x3ff66000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('I2C1', 0x3ff67000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('SDMMC', 0x3ff68000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('EMAC', 0x3ff69000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('PWM1', 0x3ff6c000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('I2S1', 0x3ff6d000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('uart2', 0x3ff6e000, 4 << 10, _UART_regset, 'uart 2'))
  s.insert(soc.make_peripheral('PWM2', 0x3ff6f000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('PWM3', 0x3ff70000, 4 << 10, None, ''))
  s.insert(soc.make_peripheral('RNG', 0x3ff75000, 4 << 10, None, ''))
  # 448 KiB internal ROM
  s.insert(soc.make_peripheral('irom0', 0x40000000, 384 << 10, None, 'internal rom 0'))
  s.insert(soc.make_peripheral('irom1', 0x3ff90000, 64 << 10, None, 'internal rom 1'))
  # 520 KiB internal SRAM
  s.insert(soc.make_peripheral('iram0', 0x40070000, 192 << 10, None, 'internal sram 0'))
  s.insert(soc.make_peripheral('iram1_0', 0x3ffe0000, 128 << 10, None, 'internal sram 1 (alias 0)'))
  s.insert(soc.make_peripheral('iram1_1', 0x400a0000, 128 << 10, None, 'internal sram 1 (alias 1)'))
  s.insert(soc.make_peripheral('iram2', 0x3ffae000, 200 << 10, None, 'internal sram 2'))
  # RTC Memory
  s.insert(soc.make_peripheral('rtc_fast_0', 0x3ff80000, 8 << 10, None, 'rtc fast ram (alias 0)'))
  s.insert(soc.make_peripheral('rtc_fast_1', 0x400c0000, 8 << 10, None, 'rtc fast ram (alias 1)'))
  s.insert(soc.make_peripheral('rtc_slow', 0x50000000, 8 << 10, None, 'rtc slow ram'))
  # approx 16 MiB external SPI flash
  s.insert(soc.make_peripheral('eflash0', 0x3F400000, 4 << 20, None, 'external flash 0'))
  s.insert(soc.make_peripheral('eflash1', 0x400c2000, (11 << 20) + (248 << 10), None, 'external flash 1'))
  # external SRAM
  s.insert(soc.make_peripheral('eram', 0x3F800000, 4 << 20, None, 'external ram'))

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


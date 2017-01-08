# -----------------------------------------------------------------------------
"""

SparkFun DEV-13907 ESP32 Thing (ESP3212)

Board Pins

J1.1 = GND
J1.2 = VUSB_RAW
J1.3 = VBAT
J1.4 = GND
J1.5 = 3.3V
J1.6 = CHIP_PU (esp32 reset line, active low)
J1.7 = GPIO13/MTCK
J1.8 = GPIO12/MTDI
J1.9 = GPIO14/MTMS
J1.10 = GPIO27
J1.11 = GPIO26
J1.12 = GPIO25
J1.13 = 35
J1.14 = 34
J1.15 = 32K_XN
J1.16 = 32K_XP
J1.17 = 39
J1.18 = 38
J1.19 = 37
J1.20 = 36

J2.1 = GND
J2.2 = VUSB_RAW
J2.3 = VBAT
J2.4 = GND
J2.5 = 3.3V
J2.6 = GPIO16
J2.7 = GPIO17
J2.8 = GPIO4
J2.9 = GPIO0 (push button)
J2.10 = GPIO2
J2.11 = GPIO15/MTDO
J2.12 = GPIO5 (blue led)
J2.13 = GPIO18
J2.14 = GPIO23
J2.15 = GPIO19
J2.16 = GPIO22
J2.17 = U0RXD
J2.18 = U0TXD
J2.19 = GPIO21
J2.20 = GND

Connection to ARM 20 Pin JTAG:

20 (GND) - GND
15 (RESET) - ~RST
1 (Vcc) - 3.3V
5 (TDI) - GPIO12/MTDI
7 (TMS) - GPIO14/MTMS
9 (TCK) - GPIO13/MTCK
13 (TDO) - GPIO15/MTDO

"""
# -----------------------------------------------------------------------------

import cli
import esp32
import mem
import soc

# -----------------------------------------------------------------------------

prompt = 'sfe13907'

# -----------------------------------------------------------------------------

# TODO make more general
default_itf = {
  'name': 'jtagkey',
}

# -----------------------------------------------------------------------------

# The ESP32 is the only device on the JTAG chain for this target
_ofs = 0
_ir_chain = (esp32.XTENSA_IRLEN, esp32.XTENSA_IRLEN)

# -----------------------------------------------------------------------------

class target(object):
  """sfe13907- SparkFun ESP32 Thing Board with ESP3212"""

  def __init__(self, ui, jtag_driver):
    self.ui = ui
    self.jtag_driver = jtag_driver
    self.soc = esp32.make_soc()
    self.cpu = esp32.xtensa(ui, jtag_driver, _ofs, _ir_chain, self.soc)
    self.soc.bind_cpu(self.cpu)
    self.mem = mem.mem(self.cpu)

    self.menu_root = (
      ('esp32', self.cpu.menu, 'esp32 functions'),
      ('jtag', self.jtag_driver.menu, 'jtag functions'),
      ('exit', self.cmd_exit),
      ('help', self.ui.cmd_help),
      ('history', self.ui.cmd_history, cli.history_help),
      ('map', self.soc.cmd_map),
      ('regs', self.cmd_regs, soc.help_regs),
      ('mem', self.mem.menu, 'memory functions'),
    )

    self.ui.cli.set_root(self.menu_root)
    self.set_prompt()
    self.jtag_driver.cmd_info(self.ui, None)

  def cmd_regs(self, ui, args):
    """display cpu/soc registers"""
    if len(args) == 0:
      self.cpu.cmd_regs(ui, args)
    else:
      self.soc.cmd_regs(ui, args)

  def set_prompt(self):
    # TODO get a run/halt state
    #indicator = ('*', '')[self.dbgio.is_halted()]
    indicator = ''
    self.ui.cli.set_prompt('%s%s> ' % (prompt, indicator))

  def cmd_exit(self, ui, args):
    """exit application"""
    ui.exit()

# -----------------------------------------------------------------------------

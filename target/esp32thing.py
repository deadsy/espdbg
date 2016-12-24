# -----------------------------------------------------------------------------
"""

SparkFun ESP32 Thing (ESP3212)

"""
# -----------------------------------------------------------------------------

import cli
import jtag

# -----------------------------------------------------------------------------

prompt = 'esp32thing'

# -----------------------------------------------------------------------------

# TODO make more general
default_itf = {
  'name': 'jtagkey',
}

# -----------------------------------------------------------------------------
"""

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

class target(object):
  """esp32thing- SparkFun ESP32 Thing Board with ESP3212"""

  def __init__(self, ui, jtag_driver):
    self.ui = ui
    self.jtag_driver  = jtag_driver
    self.jtag_chain = jtag.jtag(self.jtag_driver)
    self.jtag_chain.scan(jtag.IDCODE_XTENSA)

    self.menu_root = (
      ('jtag', self.jtag_driver.menu, 'jtag functions'),
      ('exit', self.cmd_exit),
      ('help', self.ui.cmd_help),
      ('history', self.ui.cmd_history, cli.history_help),
    )

    self.ui.cli.set_root(self.menu_root)
    self.set_prompt()
    self.jtag_driver.cmd_info(self.ui, None)

  def set_prompt(self):
    # TODO get a run/halt state
    #indicator = ('*', '')[self.dbgio.is_halted()]
    indicator = ''
    self.ui.cli.set_prompt('%s%s> ' % (prompt, indicator))

  def cmd_exit(self, ui, args):
    """exit application"""
    ui.exit()

# -----------------------------------------------------------------------------

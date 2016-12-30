# -----------------------------------------------------------------------------
"""

SparkFun WRL-13231 ESP8266 Thing (ESP8266)

"""
# -----------------------------------------------------------------------------

import cli

# -----------------------------------------------------------------------------

prompt = 'sfe13231'

# -----------------------------------------------------------------------------

class target(object):
  """sfe13231- SparkFun ESP8266 Thing Board with ESP8266"""

  def __init__(self, ui, dbgio):
    self.ui = ui
    self.dbgio = dbgio

    self.menu_root = (
      ('exit', self.cmd_exit),
      ('help', self.ui.cmd_help),
      ('history', self.ui.cmd_history, cli.history_help),
    )

    self.ui.cli.set_root(self.menu_root)
    self.set_prompt()
    self.dbgio.cmd_info(self.ui, None)

  def set_prompt(self):
    indicator = ('*', '')[self.dbgio.is_halted()]
    self.ui.cli.set_prompt('%s%s> ' % (prompt, indicator))

  def cmd_exit(self, ui, args):
    """exit application"""
    self.dbgio.disconnect()
    ui.exit()

# -----------------------------------------------------------------------------

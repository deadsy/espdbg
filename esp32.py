#------------------------------------------------------------------------------
"""
ESP32 Specific Interface
"""
#------------------------------------------------------------------------------

import jtag

#------------------------------------------------------------------------------

XTENSA_IDCODE = 0x120034E5
XTENSA_IRLEN = 5

#------------------------------------------------------------------------------

class esp32(object):

  def __init__(self, driver, ofs, ir_chain):
    """
    driver = low-level jtag driver
    ofs = offset of cpu 0 in the IR chain
    ir_chain = tuple of IR lengths in jtag chain
    """
    # Dual core processor. There are 2 instruction registers in the JTAG chain.
    self.cpu = [jtag.chain(driver, ofs + i, ir_chain, XTENSA_IDCODE) for i in range(2)]
    self.current_cpu = 0

    self.menu = (
      ('info', self.cmd_info),
    )

  def cmd_info(self, ui, args):
    """display esp32 information"""
    ui.put('%s\n' % self)

  def __str__(self):
    s = []
    s.append('cpu0: %s' % str(self.cpu[0]))
    s.append('cpu1: %s' % str(self.cpu[1]))
    return '\n'.join(s)

#------------------------------------------------------------------------------


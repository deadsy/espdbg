#------------------------------------------------------------------------------
"""
ESP32 Specific Interface
"""
#------------------------------------------------------------------------------

import jtag
import mini108
import lib

#------------------------------------------------------------------------------

XTENSA_IDCODE = 0x120034E5
XTENSA_IRLEN = 5

#------------------------------------------------------------------------------

class soc(object):
  """place holder"""

  def __init__(self):
    self.peripherals = {}

  def bind_cpu(self, cpu):
    self.cpu = cpu

#------------------------------------------------------------------------------

class xtensa(object):

  def __init__(self, drv, ofs, irchain, soc):
    """
    drv = low-level jtag driver
    ofs = offset of 0th cpu in the IR chain
    irchain = tuple of device IR lengths in jtag chain
    soc = system-on-chip object
    """
    # Dual core processor. There are 2 instruction registers in the JTAG chain.
    self.num_cores = 2
    self.device = [jtag.device(drv, ofs + i, irchain, XTENSA_IDCODE) for i in range(self.num_cores)]
    self.ocd = [mini108.ocd(self.device[i]) for i in range(self.num_cores)]
    self.core = 0
    self.width = 32
    self.soc = soc

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
    regs = self.save_regs()
    self.ocd[self.core].execute(code, idata = (adr,), odata = val)
    self.restore_regs(regs)
    return val[0]

  def cmd_info(self, ui, args):
    """display esp32 information"""
    ui.put('%s\n' % self)

  def cmd_test(self, ui, args):
    """test function"""
    ui.put('0: 0x%08x\n' % self.ocd[0].rd_pwrstat_clr())
    ui.put('1: 0x%08x\n' % self.ocd[1].rd_pwrstat_clr())

  def __str__(self):
    s = ['cpu%d: %s' % (i, str(self.device[i])) for i in range(self.num_cores)]
    return '\n'.join(s)

#------------------------------------------------------------------------------


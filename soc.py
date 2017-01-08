#------------------------------------------------------------------------------
"""
SoC Object

The SoC object stores all of the peripheral/registers/bit-field definitions
specific to a SoC chip.

"""
#------------------------------------------------------------------------------

import util

#------------------------------------------------------------------------------

help_regs = (
  ('<cr>', 'display cpu registers'),
  ('[name]', 'display registers for peripheral')
)

#------------------------------------------------------------------------------

class interrupt(object):

  def __init__(self):
    pass

#------------------------------------------------------------------------------

class enumval(object):

  def __init__(self):
    pass

#------------------------------------------------------------------------------

class enumvals(object):

  def __init__(self):
    pass

#------------------------------------------------------------------------------

class field(object):

  def __init__(self):
    self.fmt = None
    self.cached_val = None

  def field_name(self, val):
    """return the name for the field value"""
    mask = ((1 << (self.msb - self.lsb + 1)) - 1) << self.lsb
    val = (val & mask) >> self.lsb
    val_name = ''
    if callable(self.fmt):
      val_name = self.fmt(val)
    else:
      if self.enumvals is not None and len(self.enumvals) >= 1:
        # find the enumvals with usage 'read', or just find one
        for e in self.enumvals:
          if e.usage == 'read':
            break
        if e.enumval.has_key(val):
          val_name = e.enumval[val].name
    return val_name

  def display(self, val):
    """return display columns (name, val, '', descr) for this field"""
    mask = ((1 << (self.msb - self.lsb + 1)) - 1) << self.lsb
    val = (val & mask) >> self.lsb
    # work out if the value has changed since we last displayed it
    changed = '  '
    if self.cached_val is None:
      self.cached_val = val
    elif self.cached_val != val:
      self.cached_val = val
      changed = ' *'
    if self.msb == self.lsb:
      name = '  %s[%d]' % (self.name, self.lsb)
    else:
      name = '  %s[%d:%d]' % (self.name, self.msb, self.lsb)
    val_name = ''
    if callable(self.fmt):
      val_name = self.fmt(val)
    else:
      if self.enumvals is not None and len(self.enumvals) >= 1:
        # find the enumvals with usage 'read', or just find one
        for e in self.enumvals:
          if e.usage == 'read':
            break
        if e.enumval.has_key(val):
          val_name = e.enumval[val].name
    val_str = (': 0x%x %s%s' % (val, val_name, changed), ': %d %s%s' % (val, val_name, changed))[val < 10]
    return [name, val_str, '', self.description]

#------------------------------------------------------------------------------

class register(object):

  def __init__(self):
    self.cached_val = None

  def __getattr__(self, name):
    """make the field name a class attribute"""
    return self.fields[name]

  def bind_cpu(self, cpu):
    """bind a cpu to the register"""
    self.cpu = cpu

  def adr(self, idx, size):
    return self.parent.address + self.offset + (idx * (size / 8))

  def rd(self, idx = 0):
    return self.cpu.rd(self.adr(idx, self.size), self.size)

  def rd8(self, idx = 0):
    return self.cpu.rd(self.adr(idx, 8), 8)

  def wr(self, val, idx = 0):
    return self.cpu.wr(self.adr(idx, self.size), val, self.size)

  def set_bit(self, val, idx = 0):
    self.wr(self.rd(idx) | val, idx)

  def clr_bit(self, val, idx = 0):
    self.wr(self.rd(idx) & ~val, idx)

  def field_list(self):
    """return an ordered fields list"""
    # build a list of fields in most significant bit order
    f_list = self.fields.values()
    f_list.sort(key = lambda x : x.msb, reverse = True)
    return f_list

  def display(self, display_fields):
    """return display columns (name, adr, val, descr) for this register"""
    adr = self.adr(0, self.size)
    val = self.rd()
    # work out if the value has changed since we last displayed it
    changed = '  '
    if self.cached_val is None:
      self.cached_val = val
    elif self.cached_val != val:
      self.cached_val = val
      changed = ' *'
    adr_str = ': %08x[%d:0]' % (adr, self.size - 1)
    if val == 0:
      val_str = '= 0%s' % changed
    else:
      fmt = '= 0x%%0%dx%%s' % (self.size / 4)
      val_str = fmt % (val, changed)
    clist = []
    clist.append([self.name, adr_str, val_str, self.description])
    # output the fields
    if display_fields and self.fields:
      for f in self.field_list():
        clist.append(f.display(val))
    return clist

#------------------------------------------------------------------------------

class peripheral(object):

  def __init__(self):
    pass

  def __getattr__(self, name):
    """make the register name a class attribute"""
    return self.registers[name]

  def bind_cpu(self, cpu):
    """bind a cpu to the peripheral"""
    self.cpu = cpu
    if self.registers:
      for r in self.registers.values():
        r.bind_cpu(cpu)

  def contains(self, x):
    """return True if region x is entirely within the memory space of this peripheral"""
    return (self.address <= x.adr) and ((self.address + self.size - 1) >= x.end)

  def register_list(self):
    """return an ordered register list"""
    # build a list of registers in address offset order
    # tie break with the name to give a well-defined sort order
    r_list = self.registers.values()
    r_list.sort(key = lambda x : (x.offset << 16) + sum(bytearray(x.name)))
    return r_list

  def display(self, register_name = None, fields= False):
    """return a display string for this peripheral"""
    if self.registers:
      clist = []
      if register_name is not None:
        # decode a single register
        r = self.registers[register_name]
        clist.extend(r.display(fields))
      else:
        # decode all registers
        for r in self.register_list():
          clist.extend(r.display(fields))
      return util.display_cols(clist, [0,0,0,0])
    else:
      return 'no registers for %s' % self.name

  def rename_register(self, old, new):
    """rename a peripheral register old > new"""
    if old != new and self.registers.has_key(old):
      r = self.registers[old]
      del self.registers[old]
      self.registers[new] = r
      r.name = new

# -----------------------------------------------------------------------------

class soc(object):

  def __init__(self):
    self.peripherals = {}

  def __getattr__(self, name):
    """make the peripheral name a class attribute"""
    return self.peripherals[name]

  def bind_cpu(self, cpu):
    """bind a cpu to the device"""
    self.cpu = cpu
    for p in self.peripherals.values():
      p.bind_cpu(cpu)

  def insert(self, p):
    """insert a peripheral into the device"""
    assert self.peripherals.has_key(p.name) == False, 'device already has peripheral %s' % p.name
    p.parent = self
    self.peripherals[p.name] = p

  def remove(self, p):
    """remove a peripheral from the device"""
    assert self.peripherals.has_key(p.name) == True, 'device does not have peripheral %s' % p.name
    del self.peripherals[p.name]

  def peripheral_list(self):
    """return an ordered peripheral list"""
    # build a list of peripherals in base address order
    # base addresses for peripherals are not always unique. e.g. nordic chips
    # so tie break with the name to give a well-defined sort order
    p_list = self.peripherals.values()
    p_list.sort(key = lambda x : (x.address << 16) + sum(bytearray(x.name)))
    return p_list

  def interrupt_list(self):
    """return an ordered interrupt list"""
    # sort by irq order
    i_list = self.interrupts.values()
    i_list.sort(key = lambda x : x.irq)
    return i_list

  def cmd_map(self, ui, args):
    """display memory map"""
    clist = []
    for p in self.peripheral_list():
      start = p.address
      size = p.size
      if size is None:
        region = ': %08x' % start
      else:
        region = ': %08x %08x %s' % (start, start + size - 1, util.memsize(size))
      clist.append([p.name, region, p.description])
    ui.put('%s\n' % util.display_cols(clist, [0,0,0]))

  def cmd_regs(self, ui, args):
    """display peripheral registers"""
    if util.wrong_argc(ui, args, (1,2)):
      return
    if not self.peripherals.has_key(args[0]):
      ui.put("no peripheral named '%s' (run 'map' command for the names)\n" % args[0])
      return
    p = self.peripherals[args[0]]
    if len(args) == 1:
      ui.put('%s\n' % p.display(fields = False))
      return
    if args[1] == '*':
      ui.put('%s\n' % p.display(fields = True))
      return
    if not p.registers.has_key(args[1]):
      ui.put("no register named '%s' (run 'regs %s' command for the names)\n" % (args[1], args[0]))
      return
    ui.put('%s\n' % p.display(args[1], fields = True))

#------------------------------------------------------------------------------
# make peripherals from tables

def make_enumval(parent, enum_set):
  e = {}
  for (name, value, description) in enum_set:
    ev = enumval()
    ev.name = name
    ev.description = description
    ev.value = value
    ev.parent = parent
    e[ev.value] = ev
  return e

def make_enumvals(parent, enum_set):
  if enum_set is None:
    return None
  # we build a single enumvals structure
  e = enumvals()
  e.usage = 'read'
  e.enumval = make_enumval(e, enum_set)
  e.parent = parent
  return [e,]

def make_fields(parent, field_set):
  if field_set is None:
    return None
  fields = {}
  for (name, msb, lsb, enum_set, description) in field_set:
    f = field()
    f.name = name
    f.description = description
    f.msb = msb
    f.lsb = lsb
    if callable(enum_set):
      # enum_set is actually a formatting function
      f.fmt = enum_set
    else:
      f.enumvals = make_enumvals(f, enum_set)
    f.parent = parent
    fields[f.name] = f
  return fields

def make_registers(parent, register_set):
  if register_set is None:
    return None
  registers = {}
  for (name, size, offset, field_set, description) in register_set:
    r = register()
    r.name = name
    r.description = description
    r.size = size
    r.offset = offset
    r.fields = make_fields(r, field_set)
    r.parent = parent
    registers[r.name] = r
  return registers

def make_peripheral(name, address, size, register_set, description):
  p = peripheral()
  p.name = name
  p.description = description
  p.address = address
  p.size = size
  p.registers = make_registers(p, register_set)
  return p

#------------------------------------------------------------------------------

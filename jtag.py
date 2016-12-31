#-----------------------------------------------------------------------------
"""
JTAG Chain Controller
"""
#-----------------------------------------------------------------------------

import bits

#-----------------------------------------------------------------------------

class Error(Exception):
    pass

#-----------------------------------------------------------------------------

_max_devices = 4
_flush_size = _max_devices * 32
_idcode_length = 32

#-----------------------------------------------------------------------------

class device(object):
  """interface to specific device on the JTAG chain"""

  def __init__(self, driver, ofs, ir_chain, idcode):
    """setup the interface for a device on the JTAG chain"""
    self.driver = driver
    self.idcode = idcode
    # sanity check
    if ofs > len(ir_chain):
      raise Error, 'offset for device must be within IR chain tuple'
    # how many devices are before and after this device?
    self.ndevs_before = ofs
    self.ndevs_after = len(ir_chain) - ofs - 1
    # what are the IR lengths before and after this device?
    self.irlen = ir_chain[ofs]
    self.irlen_before = sum(ir_chain[:ofs])
    self.irlen_after = sum(ir_chain[ofs + 1:])
    # do a test reset
    self.driver.trst()
    # how many devices are on the chain?
    self.ndevs = self.num_devices()
    if self.ndevs != len(ir_chain):
      raise Error, 'number of devices does not match IR chain tuple'
    # what's the total ir length?
    irlen_total = self.ir_length()
    if self.irlen_before + self.irlen + self.irlen_after != irlen_total:
      raise Error, 'bad ir chain %d + (%d) + %d != %d' % (self.irlen_before, self.irlen, self.irlen_after, irlen_total)
    # check the device idcode
    idcode_real = self.reset_idcodes()[ofs]
    if idcode != idcode_real:
      raise Error, 'bad idcode 0x%08x != 0x%08x' % (idcode, idcode_real)

  def num_devices(self):
    """return the number of JTAG devices in the chain"""
    # put every device into bypass mode (IR = all 1's)
    tdi = bits.bits()
    tdi.ones(_flush_size)
    self.driver.scan_ir(tdi)
    # now each DR is a single bit
    # the DR chain length is the number of devices
    return self.dr_length()

  def chain_length(self, scan_f):
    """return the length of the JTAG IR/DR chain"""
    # build a 000...001000...000 flush buffer for tdi
    tdi = bits.bits()
    tdi.append_zeroes(_flush_size)
    tdi.append_ones(1)
    tdi.append_zeroes(_flush_size)
    # create an empty tdo buffer
    tdo = bits.bits()
    # scan out the tdi bits
    scan_f(tdi, tdo)
    # the first bits are junk
    tdo.drop_lsb(_flush_size)
    # work out how many bits tdo is behind tdi
    s = tdo.bit_str()
    s = s.lstrip('0')
    if len(s.replace('0', '')) != 1:
      raise Error, 'unexpected result from jtag chain - multiple 1\'s'
    return len(s) - 1

  def dr_length(self):
    """return the length of the DR chain"""
    # note: DR chain length is a function of current IR chain state
    return self.chain_length(self.driver.scan_dr)

  def ir_length(self):
    """return the length of the IR chain"""
    return self.chain_length(self.driver.scan_ir)

  def reset_idcodes(self):
    """return a tuple of the idcodes for the JTAG chain"""
    # a JTAG reset leaves DR as the 32 bit idcode for each device.
    self.driver.trst()
    tdi = bits.bits(self.ndevs * _idcode_length)
    tdo = bits.bits()
    self.driver.scan_dr(tdi, tdo)
    return tdo.scan((_idcode_length, ) * self.ndevs)

  def wr_ir(self, wr):
    """
    write to IR for a device
    wr: the bitbuffer to be written to ir for this device
    note - other devices will be placed in bypass mode (ir = all 1's)
    """
    tdi = bits.bits()
    tdi.append_ones(self.irlen_before)
    tdi.append(wr)
    tdi.append_ones(self.irlen_after)
    self.driver.scan_ir(tdi)

  def rw_ir(self, wr, rd):
    """
    read/write IR for a device
    wr: bitbuffer to be written to ir for this device
    rd: bitbuffer to be read from ir for this device
    note - other devices are assumed to be in bypass mode
    """
    tdi = bits.bits()
    tdi.append_ones(self.irlen_before)
    tdi.append(wr)
    tdi.append_ones(self.irlen_after)
    self.driver.scan_ir(tdi, rd)
    # strip the ir bits from the bypassed devices
    rd.drop_msb(self.irlen_before)
    rd.drop_lsb(self.irlen_after)

  def wr_dr(self, wr):
    """
    write to DR for a device
    wr: bitbuffer to be written to dr for this device
    note - other devices are assumed to be in bypass mode
    """
    tdi = bits.bits()
    tdi.append_ones(self.ndevs_before)
    tdi.append(wr)
    tdi.append_ones(self.ndevs_after)
    self.driver.scan_dr(tdi)

  def rw_dr(self, wr, rd):
    """
    read/write DR for a device
    wr: bitbuffer to be written to dr for this device
    rd: bitbuffer to be read from dr for this device
    note - other devices are assumed to be in bypass mode
    """
    tdi = bits.bits()
    tdi.append_ones(self.ndevs_before)
    tdi.append(wr)
    tdi.append_ones(self.ndevs_after)
    self.driver.scan_dr(tdi, rd)
    # strip the dr bits from the bypassed devices
    rd.drop_msb(self.ndevs_before)
    rd.drop_lsb(self.ndevs_after)

  def irchain_str(self):
    """return a descriptive string for the irchain"""
    s = []
    if self.irlen_before:
      s.append('%d' % self.irlen_before)
    s.append('(%d)' % self.irlen)
    if self.irlen_after:
      s.append('%d' % self.irlen_after)
    return ','.join(s)

  def __str__(self):
    """return a string describing the jtag device"""
    s = []
    s.append('device %d' % self.ndevs_before)
    s.append('idcode 0x%08x' % self.idcode)
    s.append('irchain %s' % self.irchain_str())
    return ' '.join(s)

#-----------------------------------------------------------------------------

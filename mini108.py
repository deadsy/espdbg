#-----------------------------------------------------------------------------
"""
Diamond Mini108 Xtensa OCD State Machine

Derived From: https://github.com/espressif/openocd-esp32/blob/master/src/target/esp108.c

This is an On Chip Debug (OCD) driver for the ESP108, the Tensilica core
inside the ESP32 chips. The ESP108 actually is specific configuration of the
configurable Tensilica Diamond 108Mini Xtensa core. Although this driver could
also be used to control other Diamond 108Mini implementations, we have none to
test this code on, so for now, this code is ESP108 specific.

The code is fairly different from the LX106 JTAG code as written by
projectgus etc for the ESP8266, because the debug controller in the LX106
is different from that in the 108Mini.

How It Works:

The JTAG-pins communicate with a TAP. Using serial shifting, you can set
two registers: the Instruction Register (IR) and a Data Register (DR) for
every instruction. The idea is that you select the IR first, then clock
data in and out of the DR belonging to that IR. (By the way, setting IR/DR
both sets it to the value you clock in, as well as gives you the value it
used to contain. You essentially read and write it at the same time.)

The ESP108 has a 5-bit IR, with (for debug) one important instruction:
11100/0x1C aka NARSEL. Selecting this instruction alternatingly presents
the NAR and NDR (Nexus Address/Data Register) as the DR.

The 8-bit NAR that's written to the chip should contains an address in bit
7-1 and a read/write bit as bit 0 that should be one if you want to write
data to one of the 128 Nexus registers and zero if you want to read from it. The
data that's read from the NAR register indicates the status: Busy (bit 1) and
Error (bit 0). The 32-bit NDR then can be used to read or write the actual
register (and execute whatever function is tied to a write).

For OCD, the OCD registers are important. Debugging is mostly done by using
these to feed the Xtensa core instructions to execute, combined with a
data register that's directly readable/writable from the JTAG port.

To execute an instruction, either write it into DIR0EXEC and it will
immediately execute. Alternatively, write it into DIR0 and write
the data for the DDR register into DDREXEC, and that also will execute
the instruction. DIR1-DIRn are for longer instructions, of which there don't
appear to be any the ESP108.

Multiprocessor:

The ESP32 has two ESP108 processors in it, which can run in SMP-mode if an
SMP-capable OS is running. The hardware has a few features which make
debugging this much easier.

First of all, there's something called a 'break network', consisting of a
BreakIn input  and a BreakOut output on each CPU. The idea is that as soon
as a CPU goes into debug mode for whatever reason, it'll signal that using
its DebugOut pin. This signal is connected to the other CPU's DebugIn
input, causing this CPU also to go into debugging mode. To resume execution
when using only this break network, we will need to manually resume both
CPUs.

An alternative to this is the XOCDMode output and the RunStall (or DebugStall)
input. When these are cross-connected, a CPU that goes into debug mode will
halt execution entirely on the other CPU. Execution on the other CPU can be
resumed by either the first CPU going out of debug mode, or the second CPU
going into debug mode: the stall is temporarily lifted as long as the stalled
CPU is in debug mode.

A third, separate, signal is CrossTrigger. This is connected in the same way
as the breakIn/breakOut network, but is for the TRAX (trace memory) feature;
it does not affect OCD in any way.

Tracing:

The ESP108 core has some trace memory that can be used to trace program
flow up to a trigger point. Barebone tracing support is included in this
driver in the form of trace* commands. OpenOCD does have some existing
infrastructure for tracing hardware, but it's all very undocumented and
seems to have some ARM-specific things, so we do not use that.

The tracing infrastructure does have the option to stop at a certain PC
and trigger a debugging interrupt. Theoretically, if we do not use
the trace functionality, we might be able to use that as a 3rd hardware
breakpoint. ToDo: look into that. I asked, seems with the trace memory
disabled any traces done will disappear in the bitbucket, so this may be
very much a viable option.

TODO:

This code very much assumes the host machines endianness is the same as that
of the target CPU, which isn't necessarily always the case. Specifically the
esp108_reg_set etc functions are suspect.

"""
#-----------------------------------------------------------------------------

import bits

#-----------------------------------------------------------------------------

class OCDError(Exception):
  def __init__(self, opcode):
    self.opcode = opcode

#-----------------------------------------------------------------------------
# IR opcodes

_IR_PWRCTL = 0x08
_IR_PWRSTAT = 0x09
_IR_NARSEL = 0x1C
_IR_IDCODE = 0x1E
_IR_BYPASS = 0x1F

# IR/DR register lengths
_IR_LEN = 5
_PWRCTL_LEN = 8
_PWRSTAT_LEN = 8
_NARSEL_ADRLEN = 8
_NARSEL_DATALEN = 32
_IDCODE_LEN = 32
_BYPASS_LEN = 1

#-----------------------------------------------------------------------------
# Power Control Register

PWRCTL_JTAGDEBUGUSE = (1<<7)
PWRCTL_DEBUGRESET = (1<<6)  # set to assert debug module reset
PWRCTL_CORERESET = (1<<4)   # set to assert core reset
PWRCTL_DEBUGWAKEUP = (1<<2) # set to force debug domain to stay powered on
PWRCTL_MEMWAKEUP = (1<<1)   # set to force memory domain to stay powered on
PWRCTL_COREWAKEUP = (1<<0)  # set to force core to stay powered on

PWRCTL_ALL_ON = PWRCTL_JTAGDEBUGUSE | PWRCTL_COREWAKEUP | PWRCTL_MEMWAKEUP | PWRCTL_DEBUGWAKEUP
PWRCTL_DEBUG_ON = PWRCTL_JTAGDEBUGUSE | PWRCTL_DEBUGWAKEUP

#-----------------------------------------------------------------------------
# Power Status Register

PWRSTAT_DEBUGWASRESET = (1<<6)    # set if debug module got reset
PWRSTAT_COREWASRESET = (1<<4)     # set if core got reset
PWRSTAT_CORESTILLNEEDED = (1<<3)  # set if others keeping core awake
PWRSTAT_DEBUGDOMAINON = (1<<2)    # set if debug domain is powered on
PWRSTAT_MEMDOMAINON = (1<<1)      # set if memory domain is powered on
PWRSTAT_COREDOMAINON = (1<<0)     # set if core is powered on

PWRSTAT_ALL_ON = PWRSTAT_COREDOMAINON | PWRSTAT_MEMDOMAINON | PWRSTAT_DEBUGDOMAINON

#-----------------------------------------------------------------------------
# XDM/Nexus Register Addresses

# TRAX Registers
XDM_TRAX_ID = 0x00          # ID
XDM_TRAX_CONTROL = 0x01     # Control
XDM_TRAX_STATUS = 0x02      # Status
XDM_TRAX_DATA = 0x03        # Data
XDM_TRAX_ADDRESS = 0x04     # Address
XDM_TRAX_TRIGGER = 0x05     # Stop PC
XDM_TRAX_MATCH = 0x06       # Stop PC Range
XDM_TRAX_DELAY = 0x07       # Post Stop Trigger Capture Size
XDM_TRAX_STARTADDR = 0x08   # Trace Memory Start
XDM_TRAX_ENDADDR = 0x09     # Trace Memory End
XDM_TRAX_DEBUGPC = 0x0F     # Debug PC
XDM_TRAX_P4CHANGE = 0x10
XDM_TRAX_TIME0 = 0x10       # First Time Register
XDM_TRAX_P4REV = 0x11
XDM_TRAX_TIME1 = 0x11       # Second Time Register
XDM_TRAX_P4DATE = 0x12
XDM_TRAX_INTTIME_MAX = 0x12 # maximal Value of Timestamp IntTime
XDM_TRAX_P4TIME = 0x13
XDM_TRAX_PDSTATUS = 0x14    # Sample of PDebugStatus
XDM_TRAX_PDDATA = 0x15      # Sample of PDebugData
XDM_TRAX_STOP_PC = 0x16
XDM_TRAX_STOP_ICNT = 0x16
XDM_TRAX_MSG_STATUS = 0x17
XDM_TRAX_FSM_STATUS = 0x18
XDM_TRAX_IB_STATUS = 0x19
XDM_TRAX_STOPCNT = 0x1A

# Performance Monitoring Counters
XDM_PERF_PMG = 0x20     # perf. mon. global control register
XDM_PERF_INTPC = 0x24   # perf. mon. interrupt PC
XDM_PERF_PM0 = 0x28     # perf. mon. counter 0 value
XDM_PERF_PM1 = 0x29     # perf. mon. counter 1 value
XDM_PERF_PM2 = 0x2A     # perf. mon. counter 2 value
XDM_PERF_PM3 = 0x2B     # perf. mon. counter 3 value
XDM_PERF_PM4 = 0x2C     # perf. mon. counter 4 value
XDM_PERF_PM5 = 0x2D     # perf. mon. counter 5 value
XDM_PERF_PM6 = 0x2E     # perf. mon. counter 6 value
XDM_PERF_PM7 = 0x2F     # perf. mon. counter 7 value
XDM_PERF_PMCTRL0 = 0x30 # perf. mon. counter 0 control
XDM_PERF_PMCTRL1 = 0x31 # perf. mon. counter 1 control
XDM_PERF_PMCTRL2 = 0x32 # perf. mon. counter 2 control
XDM_PERF_PMCTRL3 = 0x33 # perf. mon. counter 3 control
XDM_PERF_PMCTRL4 = 0x34 # perf. mon. counter 4 control
XDM_PERF_PMCTRL5 = 0x35 # perf. mon. counter 5 control
XDM_PERF_PMCTRL6 = 0x36 # perf. mon. counter 6 control
XDM_PERF_PMCTRL7 = 0x37 # perf. mon. counter 7 control
XDM_PERF_PMSTAT0 = 0x38 # perf. mon. counter 0 status
XDM_PERF_PMSTAT1 = 0x39 # perf. mon. counter 1 status
XDM_PERF_PMSTAT2 = 0x3A # perf. mon. counter 2 status
XDM_PERF_PMSTAT3 = 0x3B # perf. mon. counter 3 status
XDM_PERF_PMSTAT4 = 0x3C # perf. mon. counter 4 status
XDM_PERF_PMSTAT5 = 0x3D # perf. mon. counter 5 status
XDM_PERF_PMSTAT6 = 0x3E # perf. mon. counter 6 status
XDM_PERF_PMSTAT7 = 0x3F # perf. mon. counter 7 status

# On-Chip-Debug (OCD) Registers
XDM_OCD_ID = 0x40       # ID register
XDM_OCD_DCR_CLR = 0x42  # Debug Control reg clear
XDM_OCD_DCR_SET = 0x43  # Debug Control reg set
XDM_OCD_DSR = 0x44      # Debug Status reg
XDM_OCD_DDR = 0x45      # Debug Data reg
XDM_OCD_DDREXEC = 0x46  # Debug Data reg + execute-DIR
XDM_OCD_DIR0EXEC = 0x47 # Debug Instruction reg, word 0 + execute-DIR
XDM_OCD_DIR0 = 0x48     # Debug Instruction reg, word 0
XDM_OCD_DIR1 = 0x49     # Debug Instruction reg, word 1
XDM_OCD_DIR2 = 0x4A     # Debug Instruction reg, word 2
XDM_OCD_DIR3 = 0x49     # Debug Instruction reg, word 3
XDM_OCD_DIR4 = 0x4C     # Debug Instruction reg, word 4
XDM_OCD_DIR5 = 0x4D     # Debug Instruction reg, word 5
XDM_OCD_DIR6 = 0x4E     # Debug Instruction reg, word 6
XDM_OCD_DIR7 = 0x4F     # Debug Instruction reg, word 7

# Miscellaneous Registers
XDM_MISC_PWRCTL = 0x58    # Power and Reset Control
XDM_MISC_PWRSTAT = 0x59   # Power and Reset Status
XDM_MISC_ERISTAT = 0x5A   # ERI Transaction Status
XDM_MISC_DATETIME = 0x5D  # [INTERNAL] Timestamps of build
XDM_MISC_UBID = 0x5E      # [INTERNAL] Build Unique ID
XDM_MISC_CID = 0x5F       # [INTERNAL] Customer ID

# CoreSight Compatibility Registers
XDM_CS_ITCTRL = 0x60      # InTegration Mode control reg
XDM_CS_CLAIMSET = 0x68    # Claim Tag Set reg
XDM_CS_CLAIMCLR = 0x69    # Claim Tag Clear reg
XDM_CS_LOCK_ACCESS = 0x6B # Lock Access (writing 0xC5ACCE55 unlocks)
XDM_CS_LOCK_STATUS = 0x6D # Lock Status
XDM_CS_AUTH_STATUS = 0x6E # Authentication Status
XDM_CS_DEV_ID = 0x72      # Device ID
XDM_CS_DEV_TYPE = 0x73    # Device Type
XDM_CS_PER_ID4 = 0x74     # Peripheral ID reg byte 4
XDM_CS_PER_ID5 = 0x75     # Peripheral ID reg byte 5
XDM_CS_PER_ID6 = 0x76     # Peripheral ID reg byte 6
XDM_CS_PER_ID7 = 0x77     # Peripheral ID reg byte 7
XDM_CS_PER_ID0 = 0x78     # Peripheral ID reg byte 0
XDM_CS_PER_ID1 = 0x79     # Peripheral ID reg byte 1
XDM_CS_PER_ID2 = 0x7A     # Peripheral ID reg byte 2
XDM_CS_PER_ID3 = 0x7B     # Peripheral ID reg byte 3
XDM_CS_COMP_ID0 = 0x7C    # Component ID reg byte 0
XDM_CS_COMP_ID1 = 0x7D    # Component ID reg byte 1
XDM_CS_COMP_ID2 = 0x7E    # Component ID reg byte 2
XDM_CS_COMP_ID3 = 0x7F    # Component ID reg byte 3

#-----------------------------------------------------------------------------

# XDM_OCD_DCR_SET bits
OCDDCR_ENABLEOCD = (1<<0)
OCDDCR_DEBUGINTERRUPT = (1<<1)
OCDDCR_INTERRUPTALLCONDS = (1<<2)
OCDDCR_BREAKINEN = (1<<16)
OCDDCR_BREAKOUTEN = (1<<17)
OCDDCR_DEBUGSWACTIVE = (1<<20)
OCDDCR_RUNSTALLINEN = (1<<21)
OCDDCR_DEBUGMODEOUTEN = (1<<22)
OCDDCR_BREAKOUTITO = (1<<24)
OCDDCR_BREAKACKITO = (1<<25)

# XDM_OCD_DSR bits
OCDDSR_EXECDONE = (1<<0)
OCDDSR_EXECEXCEPTION = (1<<1)
OCDDSR_EXECBUSY = (1<<2)
OCDDSR_EXECOVERRUN = (1<<3)
OCDDSR_STOPPED = (1<<4)
OCDDSR_COREWROTEDDR = (1<<10)
OCDDSR_COREREADDDR = (1<<11)
OCDDSR_HOSTWROTEDDR = (1<<14)
OCDDSR_HOSTREADDDR = (1<<15)
OCDDSR_DEBUGPENDBREAK = (1<<16)
OCDDSR_DEBUGPENDHOST = (1<<17)
OCDDSR_DEBUGPENDTRAX = (1<<18)
OCDDSR_DEBUGINTBREAK = (1<<20)
OCDDSR_DEBUGINTHOST = (1<<21)
OCDDSR_DEBUGINTTRAX = (1<<22)
OCDDSR_RUNSTALLTOGGLE = (1<<23)
OCDDSR_RUNSTALLSAMPLE = (1<<24)
OCDDSR_BREACKOUTACKITI = (1<<25)
OCDDSR_BREAKINITI = (1<<26)



#-----------------------------------------------------------------------------

class ocd(object):
  """Xtensa ESP108/Mini108 OCD State Machine Control"""

  def __init__(self, ui, device):
    self.ui = ui
    self.device = device

  def wr_ir(self, val):
    """write instruction register"""
    self.device.wr_ir(bits.bits(_IR_LEN, val))

  def wr_dr(self, n, val):
    """write current data register"""
    self.device.wr_dr(bits.bits(n, val))

  def rd_dr(self, n):
    """read from current data register"""
    rd = bits.bits(n)
    self.device.rd_dr(rd)
    return rd.scan((n,))[0]

  def wr_rd_dr(self, n, val):
    """write and read from current data register"""
    rd = bits.bits(n)
    self.device.wr_rd_dr(bits.bits(n, val), rd)
    return rd.scan((n,))[0]

  def rd_idcode(self):
    """read from IDCODE"""
    self.wr_ir(_IR_IDCODE)
    return self.rd_dr(_IDCODE_LEN)

  def rd_pwrstat_clr(self):
    """read PWRSTAT and clear the *WASRESET bits"""
    self.wr_ir(_IR_PWRSTAT)
    return self.wr_rd_dr(_PWRSTAT_LEN, PWRSTAT_DEBUGWASRESET | PWRSTAT_COREWASRESET)

  def rd_pwrstat(self):
    """read PWRSTAT"""
    self.wr_ir(_IR_PWRSTAT)
    return self.rd_dr(_PWRSTAT_LEN)

  def wr_pwrctl(self, val):
    """write PWRCTL"""
    self.wr_ir(_IR_PWRCTL)
    self.wr_dr(_PWRCTL_LEN, val)

  def rd_pwrctl(self):
    """read PWRCTL"""
    self.wr_ir(_IR_PWRCTL)
    return self.rd_dr(_PWRCTL_LEN)

  def wr_nexus(self, reg, val):
    """write a nexus register"""
    self.wr_ir(_IR_NARSEL)
    self.wr_dr(_NARSEL_ADRLEN, reg << 1 | 1)
    self.wr_dr(_NARSEL_DATALEN, val)

  def rd_nexus(self, reg):
    """read a nexus register"""
    self.wr_ir(_IR_NARSEL)
    self.wr_dr(_NARSEL_ADRLEN, reg << 1 | 0)
    return self.rd_dr(_NARSEL_DATALEN)

  def check_dsr(self):
    """check and clear the dsr value"""
    clr = False
    dsr = self.rd_nexus(XDM_OCD_DSR)
    if dsr & OCDDSR_EXECBUSY:
      #LOG_ERROR("%s: %s (line %d): DSR (%08X) indicates target still busy!", target->cmd_name, function, line, intfromchars(dsr));
      clr = True
    if dsr & OCDDSR_EXECEXCEPTION:
      #LOG_ERROR("%s: %s (line %d): DSR (%08X) indicates DIR instruction generated an exception!", target->cmd_name, function, line, intfromchars(dsr));
      clr = True
    if dsr & OCDDSR_EXECOVERRUN:
      #LOG_ERROR("%s: %s (line %d): DSR (%08X) indicates DIR instruction generated an overrun!", target->cmd_name, function, line, intfromchars(dsr));
      clr = True
    if clr:
      wr_nexus(XDM_OCD_DSR, OCDDSR_EXECEXCEPTION | OCDDSR_EXECOVERRUN)

  def halt(self):
    """halt the cpu"""
    self.ui.put("%08x\n" % self.rd_nexus(XDM_OCD_DSR))
    self.wr_nexus(XDM_OCD_DCR_SET, OCDDCR_DEBUGINTERRUPT)
    self.ui.put("%08x\n" % self.rd_nexus(XDM_OCD_DSR))

  def run(self):
    """run the cpu"""
    pass

  def set_reset(self):
    """reset the cpu"""
    self.wr_pwrctl(PWRCTL_ALL_ON | PWRCTL_CORERESET)

  def clr_reset(self, halt=False):
    """deassert reset on the cpu"""
    if halt:
      # halt immediately
      self.wr_nexus(XDM_OCD_DCR_SET, OCDDCR_DEBUGINTERRUPT)
    self.wr_pwrctl(PWRCTL_ALL_ON)


#-----------------------------------------------------------------------------

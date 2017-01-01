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
PWRCTL_DEBUGRESET = (1<<6)
PWRCTL_CORERESET = (1<<4)
PWRCTL_DEBUGWAKEUP = (1<<2)
PWRCTL_MEMWAKEUP = (1<<1)
PWRCTL_COREWAKEUP = (1<<0)

#-----------------------------------------------------------------------------
# Power Status Register

PWRSTAT_DEBUGWASRESET = (1<<6)
PWRSTAT_COREWASRESET = (1<<4)
PWRSTAT_CORESTILLNEEDED = (1<<3)
PWRSTAT_DEBUGDOMAINON = (1<<2)
PWRSTAT_MEMDOMAINON = (1<<1)
PWRSTAT_COREDOMAINON = (1<<0)

#-----------------------------------------------------------------------------
# NAR addresses

# TRAX registers
NARADR_TRAXID = 0x00
NARADR_TRAXCTRL = 0x01
NARADR_TRAXSTAT = 0x02
NARADR_TRAXDATA = 0x03
NARADR_TRAXADDR = 0x04
NARADR_TRIGGERPC = 0x05
NARADR_PCMATCHCTRL = 0x06
NARADR_DELAYCNT = 0x07
NARADR_MEMADDRSTART = 0x08
NARADR_MEMADDREND = 0x09

# Performance monitor registers
NARADR_PMG = 0x20
NARADR_INTPC = 0x24
NARADR_PM0 = 0x28
NARADR_PM7 = 0x2F
NARADR_PMCTRL0 = 0x30
NARADR_PMCTRL7 = 0x37
NARADR_PMSTAT0 = 0x38
NARADR_PMSTAT7 = 0x3F

# OCD registers
NARADR_OCDID = 0x40
NARADR_DCRCLR = 0x42
NARADR_DCRSET = 0x43
NARADR_DSR = 0x44
NARADR_DDR = 0x45
NARADR_DDREXEC = 0x46
NARADR_DIR0EXEC = 0x47
NARADR_DIR0 = 0x48
NARADR_DIR1 = 0x49
NARADR_DIR7 = 0x4F

# Misc registers
NARADR_PWRCTL = 0x58
NARADR_PWRSTAT = 0x69
NARADR_ERISTAT = 0x5A

# CoreSight registers
NARADR_ITCTRL = 0x60
NARADR_CLAIMSET = 0x68
NARADR_CLAIMCLR = 0x69
NARADR_LOCKACCESS = 0x6c
NARADR_LOCKSTATUS = 0x6d
NARADR_AUTHSTATUS = 0x6e
NARADR_DEVID = 0x72
NARADR_DEVTYPE = 0x73
NARADR_PERID4 = 0x74
NARADR_PERID7 = 0x77
NARADR_PERID0 = 0x78
NARADR_PERID3 = 0x7b
NARADR_COMPID0 = 0x7c
NARADR_COMPID3 = 0x7f

#-----------------------------------------------------------------------------

class ocd(object):
  """Xtensa ESP108/Mini108 OCD State Machine Control"""

  def __init__(self, device):
    self.device = device

  def wr_ir(self, val):
    """write instruction register"""
    wr = bits.bits(_IR_LEN, val)
    self.device.wr_ir(wr)

  def rd_dr(self, n):
    """read n bits from the current dr register"""
    wr = bits.bits(n)
    rd = bits.bits(n)
    self.device.rw_dr(wr, rd)
    return rd.scan((n,))[0]

  def rd_idcode(self):
    """read from IDCODE"""
    self.wr_ir(_IR_IDCODE)
    return self.rd_dr(_IDCODE_LEN)

#-----------------------------------------------------------------------------

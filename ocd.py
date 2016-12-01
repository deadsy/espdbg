#-----------------------------------------------------------------------------
"""
Xtensa OCD State Machine
"""
#-----------------------------------------------------------------------------

import bits
import da
import xtensa_lib

#-----------------------------------------------------------------------------

class OCDError(Exception):
    def __init__(self, opcode):
        self.opcode = opcode

#-----------------------------------------------------------------------------
# IR opcodes
# unused opcodes are not implemented or undefined
# Note: there is no idcode - upon reset the dr contains 0

_IR_EnableOCD = 0x11 # 1 bits
_IR_DebugInt = 0x12 # 1 bits
_IR_ExecuteDI = 0x15 # 2 bits
_IR_LoadDI = 0x16 # 24 bits
_IR_ScanDDR = 0x17 # 32 bits
_IR_ReadDOSR = 0x18 # 8 bits
_IR_ScanDCR = 0x19 # 8 bits
_IR_LoadWDI = 0x1a # 1 bits
_IR_TRAX = 0x1c # 1 bits
_IR_BYPASS = 0x1f # 1 bits

# IR/DR register lengths
_IR_LEN = 5
_DOSR_LEN = 8
_DCR_LEN = 8
_DIR_LEN = 24
_DDR_LEN = 32

#-----------------------------------------------------------------------------
# Debug Output Status Register (DOSR)

# DOSR Bits
_DOSR_NextDI = (1 << 0) # cleared on read
_DOSR_Exception = (1 << 1) # cleared on read
_DOSR_InOCDMode = (1 << 2)
_DOSR_DODReady = (1 << 3) # cleared on read
_DOSR_MASK = _DOSR_NextDI | _DOSR_Exception | _DOSR_InOCDMode | _DOSR_DODReady

def decode_dosr(val):
    """decode the DOSR register"""
    val &= _DOSR_MASK
    s = []
    if val & _DOSR_NextDI:
        s.append('NextDI')
    if val & _DOSR_Exception:
        s.append('Exception')
    if val & _DOSR_InOCDMode:
        s.append('InOCDMode')
    if val & _DOSR_DODReady:
        s.append('DODReady')
    if val == 0:
        s.append('no flags')
    s = ', '.join(s)
    return 'dosr: %s' % s

#-----------------------------------------------------------------------------
# Debug Control Register (DCR)

_DCR_extDbgIntEn = (1 << 0)
_DCR_xOCDModePulseEn = (1 << 1)
def _DCR_SRselect(n): return ((n & 3) << 2)
_DCR_OCDOverride = (1 << 4)
_DCR_MASK = _DCR_extDbgIntEn | _DCR_xOCDModePulseEn | _DCR_SRselect(3) | _DCR_OCDOverride

def decode_dcr(val):
    """decode the DCR register"""
    val &= _DCR_MASK
    s = []
    if val & _DCR_extDbgIntEn:
        s.append('extDbgIntEn')
    if val & _DCR_xOCDModePulseEn:
        s.append('xOCDModePulseEn')
    if val & _DCR_OCDOverride:
        s.append('OCDOverride')
    s.append('SRselect %d' % ((val & _DCR_SRselect(3)) >> 2))
    s = ', '.join(s)
    return 'dcr: %s' % s

#-----------------------------------------------------------------------------

_XSR_OPCODE = 0x616800
_RSR_OPCODE = 0x036800
_WSR_OPCODE = 0x136800
_OPCODE_MASK = 0xffff0f

def write_to_ddr(opcode):
    """do we need to write to ddr?"""
    # check for xsr/rsr a?, ddr
    opcode &= _OPCODE_MASK
    return opcode in (_XSR_OPCODE, _RSR_OPCODE)

def read_from_ddr(opcode):
    """do we need to read from ddr?"""
    # check for xsr/wsr a?, ddr
    opcode &= _OPCODE_MASK
    return opcode in (_XSR_OPCODE, _WSR_OPCODE)

#-----------------------------------------------------------------------------
# RFDO x opcodes

_rfdo0_opcode = 0xf1e000
_rfdo1_opcode = 0xf1e100

#-----------------------------------------------------------------------------

class ocd(object):
    """Xtensa OCD State Machine Control"""

    def __init__(self, device):
        self.device = device
        self.sync_state()

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

    def wr_dr(self, n, val):
        """write n bits to the current dr register"""
        wr = bits.bits(n, val)
        self.device.wr_dr(wr)

    def rd_dosr(self):
        """read from DOSR"""
        self.wr_ir(_IR_ReadDOSR)
        return self.rd_dr(_DOSR_LEN)

    def rd_dcr(self):
        """read from DCR"""
        self.wr_ir(_IR_ScanDCR)
        return self.rd_dr(_DCR_LEN)

    def wr_dcr(self, val):
        """write to DCR"""
        self.wr_ir(_IR_ScanDCR)
        self.wr_dr(_DCR_LEN, val)

    def wr_dir(self, val):
        """write to DIR"""
        self.wr_ir(_IR_LoadDI)
        self.wr_dr(_DIR_LEN, val)

    def rd_ddr(self):
        """read from DDR"""
        self.wr_ir(_IR_ScanDDR)
        return self.rd_dr(_DDR_LEN)

    def wr_ddr(self, val):
        """write to DDR"""
        self.wr_ir(_IR_ScanDDR)
        self.wr_dr(_DDR_LEN, val)

    def set_srselect(self, n):
        """set SRselect in the DCR register"""
        x = self.rd_dcr() & ~_DCR_SRselect(3)
        x |= _DCR_SRselect(n)
        self.wr_dcr(x)

    def enable_ocd(self):
        """Enable the OCD"""
        self.wr_ir(_IR_EnableOCD)

    def debug_int(self):
        """issue a DebugInt TAP instruction to the processor"""
        self.wr_ir(_IR_DebugInt)
        # wait for InOCDMode
        while not (self.rd_dosr() & _DOSR_InOCDMode):
            pass

    def sync_state(self):
        """synchronise the state with the hardware"""
        self.enable_ocd()
        self.state = ('run', 'halt')[(self.rd_dosr() & _DOSR_InOCDMode) != 0]

    def enter_state(self, new_state):
        """change the state of the OCD state machine"""
        if self.state == new_state:
            # no state change
            return
        x = '%s>%s' % (self.state, new_state)
        if x == 'normal>run':
            self.enable_ocd()
        elif x == 'normal>halt':
            self.enable_ocd()
            self.debug_int()
        elif x == 'run>normal':
            self.debug_int()
            self.exec_opcode(_rfdo0_opcode)
        elif x == 'run>halt':
            self.debug_int()
        elif x == 'halt>run':
            self.exec_opcode(_rfdo1_opcode)
        elif x == 'halt>normal':
            self.exec_opcode(_rfdo0_opcode)
        else:
            assert False, 'unhandled state change %s' % x
        self.state = new_state

    def exec_opcode(self, opcode):
        """execute an opcode"""
        # TODO do opcode caching in the 4 slots
        self.wr_dir(opcode)
        # wait for NextDI or an exception
        while True:
            dosr = self.rd_dosr()
            if dosr & _DOSR_Exception:
                raise OCDError(opcode)
            if dosr & _DOSR_NextDI:
                break

    def execute(self, mem, idata = None, odata = None):
        """execute the opcodes in mem"""
        idx = 0
        for opcode in mem:
            # should we write to ddr?
            if write_to_ddr(opcode):
                assert idata is not None, 'rsr/xsr needs idata'
                self.wr_ddr(idata[idx])
                idx += 1
            # execute the instruction
            self.exec_opcode(opcode)
            # should we read from ddr?
            if read_from_ddr(opcode):
                assert odata is not None, 'wsr/xsr needs odata'
                odata.append(self.rd_ddr())

#-----------------------------------------------------------------------------

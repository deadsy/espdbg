#------------------------------------------------------------------------------
"""
Disassembler for the Xtensa ISA
"""
#------------------------------------------------------------------------------

def sex(x, n):
    """sign extend n-bit value x"""
    m = 1 << (n - 1)
    return (x ^ m) - m

#------------------------------------------------------------------------------
# instruction subfields

def get_op0(opcode):
    return opcode & 0xf

def get_op1(opcode):
    return (opcode & 0xf0000) >> 16

def get_op2(opcode):
    return (opcode & 0xf00000) >> 20

def get_t(opcode):
    return (opcode & 0xf0) >> 4

def get_m(opcode):
    return (opcode & 0xc0) >> 6

def get_n(opcode):
    return (opcode & 0x30) >> 4

def get_s(opcode):
    return (opcode & 0xf00) >> 8

def get_r(opcode):
    return (opcode & 0xf000) >> 12

def get_imm4u(opcode):
    return (opcode & 0xf000) >> 12

def get_imm6u(opcode):
    return ((opcode & 0xf000) >> 12) | (opcode & 0x30)

def get_imm8u(opcode):
    """get unsigned 8 bit immediate"""
    return (opcode & 0xff0000) >> 16

def get_imm4s(opcode):
    """get signed 4 bit immediate"""
    return sex((opcode & 0xf0) >> 4, 4)

def get_imm7s(opcode):
    """get signed 7 bit immediate"""
    x = ((opcode & 0xf000) >> 12) | (opcode & 0x70)
    # see movi.n spec for the non-standard signing method
    msb = ((x & (1 << 6)) >> 6) & ((x & (1 << 5)) >> 5)
    x |= (msb << 7)
    return sex(x, 8)

def get_imm8s(opcode):
    """get signed 8 bit immediate"""
    return sex((opcode & 0xff0000) >> 16, 8)

def get_imm18s(opcode):
    """get signed 18 bit immediate"""
    return sex((opcode & 0xffffc0) >> 6, 18)

def get_imm12s_rri8(opcode):
    """get signed 12 bit immediate - RRI8 format"""
    return sex((opcode & 0xf00) | ((opcode & 0xff0000) >> 16), 12)

def get_imm12s_bri12(opcode):
    """get signed 12 bit immediate - BRI12 format"""
    return sex((opcode & 0xfff000) >> 12, 12)

def get_imm12u_bri12(opcode):
    """get unsigned 12 bit immediate - BRI12 format"""
    return (opcode & 0xfff000) >> 12

def get_imm16_ri16(opcode):
    """get 16 bit immediate - RI16 format"""
    x = ((opcode & 0xffff00) >> 6) | (1 << 18)
    return sex(x, 19)

def get_imm4u_rri8(opcode):
    return ((opcode & 0xf0) >> 4) | ((opcode & 0x1000) >> 8)

def get_imm_addi_n(opcode):
    """get immediate value for addi.n"""
    x = (opcode & 0xf0) >> 4
    return (x, -1)[x == 0]

def get_shiftimm(opcode):
    """get shift immediate value for extui"""
    return ((opcode & (1 << 16)) >> 12) | ((opcode & 0xf00) >> 8)

def get_imm_slli(opcode):
    """get immediate value for slli"""
    return ((opcode & (1 << 20)) >> 16) | ((opcode & 0xf0) >> 4)

def get_imm_x32e(opcode):
    """get signed immediate value for s32e/l32e"""
    x = (1 << 6) | (get_r(opcode) << 2)
    return sex(x, 7)

def get_b4const(opcode):
    return (-1,1,2,3,4,5,6,7,8,10,12,16,32,64,128,256)[get_r(opcode)]

def get_b4constu(opcode):
    return (32768,65536,2,3,4,5,6,7,8,10,12,16,32,64,128,256)[get_r(opcode)]

#------------------------------------------------------------------------------

def emit_reserved3(opcode, pc):
    return ('reserved', 3)

#------------------------------------------------------------------------------
# special registers

_RD = 1
_WR = 2

def sreg_rd(n):
    """encode read-only special register"""
    return (n << 2) + _RD

def sreg_wr(n):
    """encode write-only special register"""
    return (n << 2) + _WR

def sreg_rw(n):
    """encode read/write special register"""
    return (n << 2) + _RD + _WR

def sreg_n(x):
    """convert the encoding back to a register number"""
    return (x >> 2)

_sregs = {
    sreg_rw(0): 'lbeg',
    sreg_rw(1): 'lend',
    sreg_rw(2): 'lcount',
    sreg_rw(3): 'sar',
    sreg_rw(4): 'br',
    sreg_rw(5): 'litbase',
    sreg_rw(12): 'scompare1',
    sreg_rw(16): 'acclo',
    sreg_rw(17): 'acchi',
    sreg_rw(32): 'm0',
    sreg_rw(33): 'm1',
    sreg_rw(34): 'm2',
    sreg_rw(35): 'm3',
    sreg_rw(40): 'prefctl',
    sreg_rw(72): 'windowbase',
    sreg_rw(73): 'windowstart',
    sreg_rw(83): 'ptevaddr',
    sreg_rw(89): 'mmid',
    sreg_rw(90): 'rasid',
    sreg_rw(91): 'itlbcfg',
    sreg_rw(92): 'dtlbcfg',
    sreg_rw(96): 'ibreakenable',
    sreg_rw(98): 'cacheattr',
    sreg_rw(99): 'atomctl',
    sreg_rw(104): 'ddr',
    sreg_rw(106): 'mepc',
    sreg_rw(107): 'meps',
    sreg_rw(108): 'mesave',
    sreg_rw(109): 'mesr',
    sreg_rw(110): 'mecr',
    sreg_rw(111): 'mevaddr',
    sreg_rw(128): 'ibreaka0',
    sreg_rw(129): 'ibreaka1',
    sreg_rw(144): 'dbreaka0',
    sreg_rw(145): 'dbreaka1',
    sreg_rw(160): 'dbreakc0',
    sreg_rw(161): 'dbreakc1',
    sreg_rd(176): 'configid0',
    sreg_rw(177): 'epc1',
    sreg_rw(178): 'epc2',
    sreg_rw(179): 'epc3',
    sreg_rw(180): 'epc4',
    sreg_rw(181): 'epc5',
    sreg_rw(182): 'epc6',
    sreg_rw(183): 'epc7',
    sreg_rw(192): 'depc',
    sreg_rw(194): 'eps2',
    sreg_rw(195): 'eps3',
    sreg_rw(196): 'eps4',
    sreg_rw(197): 'eps5',
    sreg_rw(198): 'eps6',
    sreg_rw(199): 'eps7',
    sreg_rd(208): 'configid1',
    sreg_rw(209): 'excsave1',
    sreg_rw(210): 'excsave2',
    sreg_rw(211): 'excsave3',
    sreg_rw(212): 'excsave4',
    sreg_rw(213): 'excsave5',
    sreg_rw(214): 'excsave6',
    sreg_rw(215): 'excsave7',
    sreg_rw(224): 'cpenable',
    sreg_rd(226): 'interrupt',
    sreg_wr(226): 'intset',
    sreg_wr(227): 'intclear',
    sreg_rw(228): 'intenable',
    sreg_rw(230): 'ps',
    sreg_rw(231): 'vecbase',
    sreg_rw(232): 'exccause',
    sreg_rw(233): 'debugcause',
    sreg_rw(234): 'ccount',
    sreg_rw(235): 'prid',
    sreg_rw(236): 'icount',
    sreg_rw(237): 'icountlevel',
    sreg_rw(238): 'excvaddr',
    sreg_rw(240): 'ccompare0',
    sreg_rw(241): 'ccompare1',
    sreg_rw(242): 'ccompare2',
    sreg_rw(244): 'misc0',
    sreg_rw(245): 'misc1',
    sreg_rw(246): 'misc2',
    sreg_rw(247): 'misc3',
}

# reverse lookup: name to number
_sregs_reverse = dict([(name, x) for (x, name) in _sregs.items()])

def sreg_name2n(name):
    """given a special register name, return the register number"""
    return sreg_n(_sregs_reverse[name])

def sregs_rd():
    """return a list of readable special registers"""
    return [(sreg_n(x), name) for (x, name) in _sregs.items() if (x & _RD) != 0]

def get_sr(opcode, rd = True):
    """return the special register name"""
    x = (opcode & 0xff00) >> 8
    if _sregs.has_key(sreg_rw(x)):
        return _sregs[sreg_rw(x)]
    if rd and _sregs.has_key(sreg_rd(x)):
        return _sregs[sreg_rd(x)]
    if (not rd) and _sregs.has_key(sreg_wr(x)):
        return _sregs[sreg_wr(x)]
    return '?'

#------------------------------------------------------------------------------
# Section 7.3.1 - opcode decode maps

# Table 240 - select with t
map_s3 = (
    lambda opcode, pc: ('ret.n', 2),
    lambda opcode, pc: ('retw.n', 2),
    lambda opcode, pc: ('break.n %d' % get_s(opcode), 2),
    lambda opcode, pc: ('nop.n', 2),
    emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('ill.n', 2),
    emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_s3) == 16

# Table 239 - select with r
map_st3 = (
    lambda opcode, pc: ('mov.n a%d, a%d' % (get_t(opcode), get_s(opcode)), 2),
    emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: map_s3[get_t(opcode)](opcode, pc),
)
assert len(map_st3) == 16

# Table 238 - select with t
map_st2 = (
    lambda opcode, pc: ('movi.n a%d, %d' % (get_s(opcode), get_imm7s(opcode)), 2),
    lambda opcode, pc: ('movi.n a%d, %d' % (get_s(opcode), get_imm7s(opcode)), 2),
    lambda opcode, pc: ('beqz.n a%d, 0x%08x' % (get_s(opcode), get_imm6u(opcode) + pc + 4), 2),
    lambda opcode, pc: ('bnez.n a%d, 0x%08x' % (get_s(opcode), get_imm6u(opcode) + pc + 4), 2),
)
assert len(map_st2) == 4

# Table 237 - select from r
map_b = (
    lambda opcode, pc: ('bnone a%d, a%d, 0x%08x' % (get_s(opcode), get_t(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('beq a%d, a%d, 0x%08x' % (get_s(opcode), get_t(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('blt a%d, a%d, 0x%08x' % (get_s(opcode), get_t(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bltu a%d, a%d, 0x%08x' % (get_s(opcode), get_t(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('ball a%d, a%d, 0x%08x' % (get_s(opcode), get_t(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bbc a%d, a%d, 0x%08x' % (get_s(opcode), get_t(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bbci a%d, %d, 0x%08x' % (get_s(opcode), get_imm4u_rri8(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bbci a%d, %d, 0x%08x' % (get_s(opcode), get_imm4u_rri8(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bany a%d, a%d, 0x%08x' % (get_s(opcode), get_t(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bne a%d, a%d, 0x%08x' % (get_s(opcode), get_t(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bge a%d, a%d, 0x%08x' % (get_s(opcode), get_t(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bgeu a%d, a%d, 0x%08x' % (get_s(opcode), get_t(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bnall a%d, a%d, 0x%08x' % (get_s(opcode), get_t(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bbs a%d, a%d, 0x%08x' % (get_s(opcode), get_t(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bbsi a%d, %d, 0x%08x' % (get_s(opcode), get_imm4u_rri8(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bbsi a%d, %d, 0x%08x' % (get_s(opcode), get_imm4u_rri8(opcode), get_imm8s(opcode) + pc + 4), 3),
)
assert len(map_b) == 16

# Table 236 - select with r
map_b1 = (
    lambda opcode, pc: ('bfp ?', 3),
    lambda opcode, pc: ('btp ?', 3),
    emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('loop ?', 3),
    lambda opcode, pc: ('loopnez ?', 3),
    lambda opcode, pc: ('loopgtz ?', 3),
    emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_b1) == 16

# Table 235 - select with m
map_bi1 = (
    lambda opcode, pc: ('entry a%d, %d' % (get_s(opcode), get_imm12u_bri12(opcode) << 3), 3),
    lambda opcode, pc: map_b1[get_r(opcode)](opcode, pc),
    lambda opcode, pc: ('bltui a%d, %d, 0x%08x' % (get_s(opcode), get_b4const(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bgeui a%d, %d, 0x%08x' % (get_s(opcode), get_b4const(opcode), get_imm8s(opcode) + pc + 4), 3),
)
assert len(map_bi1) == 4

# Table 234 - select with m
map_bi0 = (
    lambda opcode, pc: ('beqi a%d, %d, 0x%08x' % (get_s(opcode), get_b4const(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bnei a%d, %d, 0x%08x' % (get_s(opcode), get_b4const(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('blti a%d, %d, 0x%08x' % (get_s(opcode), get_b4const(opcode), get_imm8s(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bgei a%d, %d, 0x%08x' % (get_s(opcode), get_b4const(opcode), get_imm8s(opcode) + pc + 4), 3),
)
assert len(map_bi0) == 4

# Table 233 - select with m
map_bz = (
    lambda opcode, pc: ('beqz a%d, 0x%08x' % (get_s(opcode), get_imm12s_bri12(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bnez a%d, 0x%08x' % (get_s(opcode), get_imm12s_bri12(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bltz a%d, 0x%08x' % (get_s(opcode), get_imm12s_bri12(opcode) + pc + 4), 3),
    lambda opcode, pc: ('bgez a%d, 0x%08x' % (get_s(opcode), get_imm12s_bri12(opcode) + pc + 4), 3),
)
assert len(map_bz) == 4

# Table 232 - select with n
map_si = (
    lambda opcode, pc: ('j 0x%08x' % (get_imm18s(opcode) + pc + 4), 3),
    lambda opcode, pc: map_bz[get_m(opcode)](opcode, pc),
    lambda opcode, pc: map_bi0[get_m(opcode)](opcode, pc),
    lambda opcode, pc: map_bi1[get_m(opcode)](opcode, pc),
)
assert len(map_si) == 4

# Table 231 - select with n
map_calln = (
    lambda opcode, pc: ('call0 ?', 3),
    lambda opcode, pc: ('call4 ?', 3),
    lambda opcode, pc: ('call8 ?', 3),
    lambda opcode, pc: ('call12 ?', 3),
)
assert len(map_calln) == 4

# Table 230 - select with op1
map_macc = (
    lambda opcode, pc: ('lddec ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_macc) == 16

# Table 229 - select with op1
map_maci = (
    lambda opcode, pc: ('ldinc ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_maci) == 16

# Table 228 - select with op1
map_macaa = (
    lambda opcode, pc: ('umul.aa.ll ?', 3),
    lambda opcode, pc: ('umul.aa.hl ?', 3),
    lambda opcode, pc: ('umul.aa.lh ?', 3),
    lambda opcode, pc: ('umul.aa.hh ?', 3),
    lambda opcode, pc: ('mul.aa.ll ?', 3),
    lambda opcode, pc: ('mul.aa.hl ?', 3),
    lambda opcode, pc: ('mul.aa.lh ?', 3),
    lambda opcode, pc: ('mul.aa.hh ?', 3),
    lambda opcode, pc: ('mula.aa.ll ?', 3),
    lambda opcode, pc: ('mula.aa.hl ?', 3),
    lambda opcode, pc: ('mula.aa.lh ?', 3),
    lambda opcode, pc: ('mula.aa.hh ?', 3),
    lambda opcode, pc: ('muls.aa.ll ?', 3),
    lambda opcode, pc: ('muls.aa.hl ?', 3),
    lambda opcode, pc: ('muls.aa.lh ?', 3),
    lambda opcode, pc: ('muls.aa.hh ?', 3),
)
assert len(map_macaa) == 16

# Table 227 - select with op1
map_macda = (
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('mul.da.ll ?', 3),
    lambda opcode, pc: ('mul.da.hl ?', 3),
    lambda opcode, pc: ('mul.da.lh ?', 3),
    lambda opcode, pc: ('mul.da.hh ?', 3),
    lambda opcode, pc: ('mula.da.ll ?', 3),
    lambda opcode, pc: ('mula.da.hl ?', 3),
    lambda opcode, pc: ('mula.da.lh ?', 3),
    lambda opcode, pc: ('mula.da.hh ?', 3),
    lambda opcode, pc: ('muls.da.ll ?', 3),
    lambda opcode, pc: ('muls.da.hl ?', 3),
    lambda opcode, pc: ('muls.da.lh ?', 3),
    lambda opcode, pc: ('muls.da.hh ?', 3),
)
assert len(map_macda) == 16

# Table 226 - select with op1
map_macca = (
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('mula.da.ll.lddec ?', 3),
    lambda opcode, pc: ('mula.da.hl.lddec ?', 3),
    lambda opcode, pc: ('mula.da.lh.lddec ?', 3),
    lambda opcode, pc: ('mula.da.hh.lddec ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_macca) == 16

# Table 225 - select with op1
map_maccd = (
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('mula.dd.ll.lddec ?', 3),
    lambda opcode, pc: ('mula.dd.hl.lddec ?', 3),
    lambda opcode, pc: ('mula.dd.lh.lddec ?', 3),
    lambda opcode, pc: ('mula.dd.hh.lddec ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_maccd) == 16

# Table 224 - select with op1
map_macad = (
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('mul.ad.ll ?', 3),
    lambda opcode, pc: ('mul.ad.hl ?', 3),
    lambda opcode, pc: ('mul.ad.lh ?', 3),
    lambda opcode, pc: ('mul.ad.hh ?', 3),
    lambda opcode, pc: ('mula.ad.ll ?', 3),
    lambda opcode, pc: ('mula.ad.hl ?', 3),
    lambda opcode, pc: ('mula.ad.lh ?', 3),
    lambda opcode, pc: ('mula.ad.hh ?', 3),
    lambda opcode, pc: ('muls.ad.ll ?', 3),
    lambda opcode, pc: ('muls.ad.hl ?', 3),
    lambda opcode, pc: ('muls.ad.lh ?', 3),
    lambda opcode, pc: ('muls.ad.hh ?', 3),
)
assert len(map_macad) == 16

# Table 223 - select with op1
map_macdd = (
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('mul.dd.ll ?', 3),
    lambda opcode, pc: ('mul.dd.hl ?', 3),
    lambda opcode, pc: ('mul.dd.lh ?', 3),
    lambda opcode, pc: ('mul.dd.hh ?', 3),
    lambda opcode, pc: ('mula.dd.ll ?', 3),
    lambda opcode, pc: ('mula.dd.hl ?', 3),
    lambda opcode, pc: ('mula.dd.lh ?', 3),
    lambda opcode, pc: ('mula.dd.hh ?', 3),
    lambda opcode, pc: ('muls.dd.ll ?', 3),
    lambda opcode, pc: ('muls.dd.hl ?', 3),
    lambda opcode, pc: ('muls.dd.lh ?', 3),
    lambda opcode, pc: ('muls.dd.hh ?', 3),
)
assert len(map_macdd) == 16

# Table 222 - select with op1
map_macia = (
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('mula.da.ll.ldinc ?', 3),
    lambda opcode, pc: ('mula.da.hl.ldinc ?', 3),
    lambda opcode, pc: ('mula.da.lh.ldinc ?', 3),
    lambda opcode, pc: ('mula.da.hh.ldinc ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_macia) == 16

# Table 221 - select with op1
map_macid = (
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('mula.dd.ll.ldinc ?', 3),
    lambda opcode, pc: ('mula.dd.hl.ldinc ?', 3),
    lambda opcode, pc: ('mula.dd.lh.ldinc ?', 3),
    lambda opcode, pc: ('mula.dd.hh.ldinc ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_macid) == 16

# Table 220 - select with op2
map_mac16 = (
    lambda opcode, pc: map_macid[get_op1(opcode)](opcode, pc),
    lambda opcode, pc: map_maccd[get_op1(opcode)](opcode, pc),
    lambda opcode, pc: map_macdd[get_op1(opcode)](opcode, pc),
    lambda opcode, pc: map_macad[get_op1(opcode)](opcode, pc),
    lambda opcode, pc: map_macia[get_op1(opcode)](opcode, pc),
    lambda opcode, pc: map_macca[get_op1(opcode)](opcode, pc),
    lambda opcode, pc: map_macda[get_op1(opcode)](opcode, pc),
    lambda opcode, pc: map_macaa[get_op1(opcode)](opcode, pc),
    lambda opcode, pc: map_maci[get_op1(opcode)](opcode, pc),
    lambda opcode, pc: map_macc[get_op1(opcode)](opcode, pc),
    emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_mac16) == 16

# Table 219 - select with r
map_lsci = (
    lambda opcode, pc: ('lsif ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('ssif ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('lsiuf ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('ssiu ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_lsci) == 16

# Table 218 - select with op1
map_ice = (
    lambda opcode, pc: ('ipfll ?', 3),
    emit_reserved3,
    lambda opcode, pc: ('ihul ?', 3),
    lambda opcode, pc: ('iiul ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_ice) == 16

# Table 217 - select with op1
map_dce = (
    lambda opcode, pc: ('dpfll ?', 3),
    emit_reserved3,
    lambda opcode, pc: ('dhul ?', 3),
    lambda opcode, pc: ('diul ?', 3),
    lambda opcode, pc: ('diwbc ?', 3),
    lambda opcode, pc: ('diwbic ?', 3),
    emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_dce) == 16

# Table 216 - select with t
map_cache = (
    lambda opcode, pc: ('dpfrc ?', 3),
    lambda opcode, pc: ('dpfwc ?', 3),
    lambda opcode, pc: ('dpfroc ?', 3),
    lambda opcode, pc: ('dpfwoc ?', 3),
    lambda opcode, pc: ('dhwbc ?', 3),
    lambda opcode, pc: ('dhwbic ?', 3),
    lambda opcode, pc: ('dhic ?', 3),
    lambda opcode, pc: ('diic ?', 3),
    lambda opcode, pc: ('dcec ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('ipfc ?', 3),
    lambda opcode, pc: ('icec ?', 3),
    lambda opcode, pc: ('ihic ?', 3),
    lambda opcode, pc: ('iiic ?', 3),
)
assert len(map_cache) == 16

# Table 215 - select with r
map_lsai = (
    lambda opcode, pc: ('l8ui a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm8u(opcode)), 3),
    lambda opcode, pc: ('l16ui a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm8u(opcode) << 1), 3),
    lambda opcode, pc: ('l32i a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm8u(opcode) << 2), 3),
    emit_reserved3,
    lambda opcode, pc: ('s8i a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm8u(opcode)), 3),
    lambda opcode, pc: ('s16i a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm8u(opcode) << 1), 3),
    lambda opcode, pc: ('s32i a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm8u(opcode) << 2), 3),
    lambda opcode, pc: map_cache[get_t(opcode)](opcode, pc),
    emit_reserved3,
    lambda opcode, pc: ('l16si a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm8u(opcode) << 1), 3),
    lambda opcode, pc: ('movi a%d, 0x%x' % (get_t(opcode), get_imm12s_rri8(opcode)), 3),
    lambda opcode, pc: ('l32ai a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm8u(opcode) << 2), 3),
    lambda opcode, pc: ('addi a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm8s(opcode)), 3),
    lambda opcode, pc: ('addmi a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm8s(opcode) << 8), 3),
    lambda opcode, pc: ('s32c1i a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm8u(opcode) << 2), 3),
    lambda opcode, pc: ('s32ri a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm8u(opcode) << 2), 3),
)
assert len(map_lsai) == 16

# Table 214 - select with op2
map_fp1 = (
    emit_reserved3,
    lambda opcode, pc: ('un.sf ?', 3),
    lambda opcode, pc: ('oeq.sf ?', 3),
    lambda opcode, pc: ('ueq.sf ?', 3),
    lambda opcode, pc: ('olt.sf ?', 3),
    lambda opcode, pc: ('ult.sf ?', 3),
    lambda opcode, pc: ('ole.sf ?', 3),
    lambda opcode, pc: ('ule.sf ?', 3),
    lambda opcode, pc: ('moveqz.sf ?', 3),
    lambda opcode, pc: ('movnez.sf ?', 3),
    lambda opcode, pc: ('movltz.sf ?', 3),
    lambda opcode, pc: ('movgez.sf ?', 3),
    lambda opcode, pc: ('movf.sf ?', 3),
    lambda opcode, pc: ('movt.sf ?', 3),
    emit_reserved3, emit_reserved3,
)
assert len(map_fp1) == 16

# Table 213 - select with t
map_fp1op = (
    lambda opcode, pc: ('mov.s f%d, f%d' % (get_r(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('abs.s f%d, f%d' % (get_r(opcode), get_s(opcode)), 3),
    emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('rfr f%d, f%d' % (get_r(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('wfr f%d, f%d' % (get_r(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('neg.s f%d, f%d' % (get_r(opcode), get_s(opcode)), 3),
    emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_fp1op) == 16

# Table 212 - select with op2
map_fp0 = (
    lambda opcode, pc: ('add.s f%d, f%d, f%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('sub.s f%d, f%d, f%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('mul.s f%d, f%d, f%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    emit_reserved3,
    lambda opcode, pc: ('madd.s f%d, f%d, f%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('msub.s f%d, f%d, f%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('round.s ?', 3),
    lambda opcode, pc: ('trunc.s ?', 3),
    lambda opcode, pc: ('floor.s ?', 3),
    lambda opcode, pc: ('ceil.s ?', 3),
    lambda opcode, pc: ('float.s ?', 3),
    lambda opcode, pc: ('ufloat.s ?', 3),
    lambda opcode, pc: ('utrunc.s ?', 3),
    lambda opcode, pc: map_fp1op[get_t(opcode)](opcode, pc),
)
assert len(map_fp0) == 16

# Table 211 - select with op2
map_lsc4 = (
    lambda opcode, pc: ('l32e a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm_x32e(opcode)), 3),
    emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('s32e a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm_x32e(opcode)), 3),
    emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_lsc4) == 16

# Table 210 - select with op2
map_lscx = (
    lambda opcode, pc: ('lsxf ?', 3),
    lambda opcode, pc: ('lsxuf ?', 3),
    emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('ssxf ?', 3),
    lambda opcode, pc: ('ssxuf ?', 3),
    emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_lscx) == 16

# Table 209 - select with op2
map_rst3 = (
    lambda opcode, pc: ('rsr a%d, %s' % (get_t(opcode), get_sr(opcode, True)), 3),
    lambda opcode, pc: ('wsr a%d, %s' % (get_t(opcode), get_sr(opcode, False)), 3),
    lambda opcode, pc: ('sextu ?', 3),
    lambda opcode, pc: ('clampsu ?', 3),
    lambda opcode, pc: ('minu ?', 3),
    lambda opcode, pc: ('maxu ?', 3),
    lambda opcode, pc: ('minuu ?', 3),
    lambda opcode, pc: ('maxuu ?', 3),
    lambda opcode, pc: ('moveqz ?', 3),
    lambda opcode, pc: ('movnez ?', 3),
    lambda opcode, pc: ('movltz ?', 3),
    lambda opcode, pc: ('movg ?', 3),
    lambda opcode, pc: ('movfp ?', 3),
    lambda opcode, pc: ('movtp ?', 3),
    lambda opcode, pc: ('rur ?', 3),
    lambda opcode, pc: ('wur ?', 3),
)
assert len(map_rst3) == 16

# Table 208 - select with op2
map_rst2 = (
    lambda opcode, pc: ('andbp ?', 3),
    lambda opcode, pc: ('andbcp ?', 3),
    lambda opcode, pc: ('orbp ?', 3),
    lambda opcode, pc: ('orbcp ?', 3),
    lambda opcode, pc: ('xorbp ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('mulli ?', 3),
    emit_reserved3,
    lambda opcode, pc: ('muluhi ?', 3),
    lambda opcode, pc: ('mulshi ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_rst2) == 16

# Table 207 - select with t
map_rfdx = (
    lambda opcode, pc: ('rfdo %d' % get_s(opcode), 3),
    lambda opcode, pc: ('rfdd', 3),
    emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_rfdx) == 16

# Table 206 - select with r
map_imp = (
    lambda opcode, pc: ('lict ?', 3),
    lambda opcode, pc: ('sict ?', 3),
    lambda opcode, pc: ('licw ?', 3),
    lambda opcode, pc: ('sicw ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('ldct ?', 3),
    lambda opcode, pc: ('sdct ?', 3),
    emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3,
    lambda opcode, pc: map_rfdx[get_t(opcode)](opcode, pc),
    emit_reserved3,
)
assert len(map_imp) == 16

# Table 205 - select with op2
map_rst1 = (
    lambda opcode, pc: ('slli a%d, a%d, %d' % (get_r(opcode), get_s(opcode), get_imm_slli(opcode)), 3),
    lambda opcode, pc: ('slli a%d, a%d, %d' % (get_r(opcode), get_s(opcode), get_imm_slli(opcode)), 3),
    lambda opcode, pc: ('srai ?', 3),
    lambda opcode, pc: ('srai ?', 3),
    lambda opcode, pc: ('srli a%d, a%d, %d' % (get_r(opcode), get_t(opcode), get_s(opcode)), 3),
    emit_reserved3,
    lambda opcode, pc: ('xsr a%d, %s' % (get_t(opcode), get_sr(opcode)), 3),
    emit_reserved3,
    lambda opcode, pc: ('src a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('srl a%d, a%d' % (get_r(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('sll a%d, a%d' % (get_r(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('sra a%d, a%d' % (get_r(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('mul16u a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('mul16s a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    emit_reserved3,
    lambda opcode, pc: map_imp[get_r(opcode)](opcode, pc),
)
assert len(map_rst1) == 16

# Table 204 - select with s
map_rt0 = (
    lambda opcode, pc: ('neg ?', 3),
    lambda opcode, pc: ('abs ?', 3),
    emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_rt0) == 16

# Table 203 - select with r
map_tlb = (
    emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('ritlb0 a%d, a%d' % (get_t(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('iitlb a%d' % get_s(opcode), 3),
    lambda opcode, pc: ('pitlb a%d, a%d' % (get_t(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('witlb a%d, a%d' % (get_t(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('ritlb1 a%d, a%d' % (get_t(opcode), get_s(opcode)), 3),
    emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('rdtlb0 a%d, a%d' % (get_t(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('idtlb a%d' % get_s(opcode), 3),
    lambda opcode, pc: ('pdtlb a%d, a%d' % (get_t(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('wdtlb a%d, a%d' % (get_t(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('rdtlb1 a%d, a%d' % (get_t(opcode), get_s(opcode)), 3),
)
assert len(map_tlb) == 16

# Table 202 - select with r
map_st1 = (
    lambda opcode, pc: ('ssr a%d' % get_s(opcode), 3),
    lambda opcode, pc: ('ssl a%d' % get_s(opcode), 3),
    lambda opcode, pc: ('ssa8l a%d' % get_s(opcode), 3),
    lambda opcode, pc: ('ssa8b a%d' % get_s(opcode), 3),
    lambda opcode, pc: ('ssai ?', 3),
    emit_reserved3,
    lambda opcode, pc: ('rer a%d, a%d' % (get_t(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('wer a%d, a%d' % (get_t(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('rotw %d' % get_imm4s(opcode), 3),
    emit_reserved3,emit_reserved3,emit_reserved3,
    emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('nsa a%d, a%d' % (get_t(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('nsau a%d, a%d' % (get_t(opcode), get_s(opcode)), 3),
)
assert len(map_st1) == 16

# Table 201 - select with s
map_rfet = (
    lambda opcode, pc: ('rfe', 3),
    lambda opcode, pc: ('rfue', 3),
    lambda opcode, pc: ('rfde', 3),
    emit_reserved3,
    lambda opcode, pc: ('rfwo', 3),
    lambda opcode, pc: ('rfwu', 3),
    emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_rfet) == 16

# Table 200 - select with t
map_rfei = (

    lambda opcode, pc: map_rfet[get_s(opcode)](opcode, pc),
    lambda opcode, pc: ('rfi %d' % get_s(opcode), 3),
    lambda opcode, pc: ('rfme', 3),
    emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_rfei) == 16

# Table 199 - select with t
map_sync = (
    lambda opcode, pc: ('isync', 3),
    lambda opcode, pc: ('rsync', 3),
    lambda opcode, pc: ('esync', 3),
    lambda opcode, pc: ('dsync', 3),
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('excw', 3),
    emit_reserved3, emit_reserved3, emit_reserved3,
    lambda opcode, pc: ('memw', 3),
    lambda opcode, pc: ('extw', 3),
    emit_reserved3, emit_reserved3,
)
assert len(map_sync) == 16

# Table 198 - select from n
map_callx = (
    lambda opcode, pc: ('callx0 a%d' % get_s(opcode), 3),
    lambda opcode, pc: ('callx4 a%d' % get_s(opcode), 3),
    lambda opcode, pc: ('callx8 a%d' % get_s(opcode), 3),
    lambda opcode, pc: ('callx12 a%d' % get_s(opcode), 3),
)
assert len(map_callx) == 4

# Table 197 - select from n
map_jr = (
    lambda opcode, pc: ('ret', 3),
    lambda opcode, pc: ('retw', 3),
    lambda opcode, pc: ('jx a%d' % get_s(opcode), 3),
    emit_reserved3,
)
assert len(map_jr) == 4

# Table 196 - select with m
map_snm0 = (
    lambda opcode, pc: ('ill', 3),
    emit_reserved3,
    lambda opcode, pc: map_jr[get_n(opcode)](opcode, pc),
    lambda opcode, pc: map_callx[get_n(opcode)](opcode, pc),
)
assert len(map_snm0) == 4

# Table 195 - select from r
map_st0 = (
    lambda opcode, pc: map_snm0[get_m(opcode)](opcode, pc),
    lambda opcode, pc: ('movsp ?', 3),
    lambda opcode, pc: map_sync[get_t(opcode)](opcode, pc),
    lambda opcode, pc: map_rfei[get_t(opcode)](opcode, pc),
    lambda opcode, pc: ('break %d, %d' % (get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('syscall', 3),
    lambda opcode, pc: ('rsil a%d, %d' % (get_t(opcode), get_s(opcode)), 3),
    lambda opcode, pc: ('waiti %d' % get_s(opcode), 3),
    lambda opcode, pc: ('any4 ?', 3),
    lambda opcode, pc: ('all4 ?', 3),
    lambda opcode, pc: ('any8 ?', 3),
    lambda opcode, pc: ('all8 ?', 3),
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_st0) == 16

# Table 194 - select op2
map_rst0 = (
    lambda opcode, pc: map_st0[get_r(opcode)](opcode, pc),
    lambda opcode, pc: ('and a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('or a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('xor a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: map_st1[get_r(opcode)](opcode, pc),
    lambda opcode, pc: map_tlb[get_r(opcode)](opcode, pc),
    lambda opcode, pc: map_rt0[get_s(opcode)](opcode, pc),
    emit_reserved3,
    lambda opcode, pc: ('add a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('addx2 a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('addx4 a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('addx8 a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('sub a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('subx2 a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('subx4 a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
    lambda opcode, pc: ('subx8 a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 3),
)
assert len(map_rst0) == 16

# Table 193 - select with op1
map_qrst = (
    lambda opcode, pc: map_rst0[get_op2(opcode)](opcode, pc),
    lambda opcode, pc: map_rst1[get_op2(opcode)](opcode, pc),
    lambda opcode, pc: map_rst2[get_op2(opcode)](opcode, pc),
    lambda opcode, pc: map_rst3[get_op2(opcode)](opcode, pc),
    lambda opcode, pc: ('extui a%d, a%d, %d, %d' % (get_r(opcode), get_t(opcode), get_shiftimm(opcode), get_op2(opcode) + 1), 3),
    lambda opcode, pc: ('extui a%d, a%d, %d, %d' % (get_r(opcode), get_t(opcode), get_shiftimm(opcode), get_op2(opcode) + 1), 3),
    lambda opcode, pc: ('cust0', 3),
    lambda opcode, pc: ('cust1', 3),
    lambda opcode, pc: map_lscx[get_op2(opcode)](opcode, pc),
    lambda opcode, pc: map_lsc4[get_op2(opcode)](opcode, pc),
    lambda opcode, pc: map_fp0[get_op2(opcode)](opcode, pc),
    lambda opcode, pc: map_fp1[get_op2(opcode)](opcode, pc),
    emit_reserved3, emit_reserved3, emit_reserved3, emit_reserved3,
)
assert len(map_qrst) == 16

# Table 192 - select with op0
map_op0 = (
    lambda opcode, pc: map_qrst[get_op1(opcode)](opcode, pc),
    lambda opcode, pc: ('l32r a%d, 0x%08x' % (get_t(opcode), get_imm16_ri16(opcode) + ((pc + 3) & ~3)), 3),
    lambda opcode, pc: map_lsai[get_r(opcode)](opcode, pc),
    lambda opcode, pc: map_lsci[get_r(opcode)](opcode, pc),
    lambda opcode, pc: map_mac16[get_op2(opcode)](opcode, pc),
    lambda opcode, pc: map_calln[get_n(opcode)](opcode, pc),
    lambda opcode, pc: map_si[get_n(opcode)](opcode, pc),
    lambda opcode, pc: map_b[get_r(opcode)](opcode, pc),
    lambda opcode, pc: ('l32i.n a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm4u(opcode) << 2), 2),
    lambda opcode, pc: ('s32i.n a%d, a%d, %d' % (get_t(opcode), get_s(opcode), get_imm4u(opcode) << 2), 2),
    lambda opcode, pc: ('add.n a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_t(opcode)), 2),
    lambda opcode, pc: ('addi.n a%d, a%d, a%d' % (get_r(opcode), get_s(opcode), get_imm_addi_n(opcode)), 2),
    lambda opcode, pc: map_st2[get_t(opcode) >> 2](opcode, pc),
    lambda opcode, pc: map_st3[get_r(opcode)](opcode, pc),
    emit_reserved3, emit_reserved3,
)
assert len(map_op0) == 16

#------------------------------------------------------------------------------

def da_opcode(opcode, pc):
    """decode an opcode, return the mneumonic and the opcode length"""
    return map_op0[get_op0(opcode)](opcode, pc)

#------------------------------------------------------------------------------

def da_mem(mem, pc):
    """decode the opcode starting at pc in mem"""
    n = len(mem) - pc
    assert n != 0, 'no data to decode'

    # The gnu assembler generates the bytes in little endian order.
    # Work out the 3 byte opcode - if it's a 16 bit instruction we won't use the top byte.
    if n == 1:
        return (mem[pc], '?', 1)
    elif n == 2:
        opcode = (mem[pc + 1] << 8) | mem[pc]
    else:
        opcode = (mem[pc + 2] << 16) | (mem[pc + 1] << 8) | mem[pc]

    (opcode_str, opcode_len) = da_opcode(opcode, pc)
    opcode &= (1 << (opcode_len * 8)) - 1
    return (opcode, opcode_str, opcode_len)

#------------------------------------------------------------------------------

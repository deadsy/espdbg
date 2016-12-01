    .text
    .global _start

_start:
    rsr a0, ddr
    _l32i.n a0, a0, 0
    wsr a0, ddr

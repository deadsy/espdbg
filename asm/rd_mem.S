    .text
    .global _ResetVector

_ResetVector:
    rsr a0, ddr
    _l32i.n a0, a0, 0
    wsr a0, ddr

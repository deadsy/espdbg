# write 16 bit value to address
# idata: adr, val
# odata: None
# changes: a0, a1

    .text
    .global _ResetVector

_ResetVector:
    rsr a0, ddr
    rsr a1, ddr
    s16i a1, a0, 0
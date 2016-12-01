# restore registers from saved values
# idata: a0, a1
# odata: None
# changes: a0, a1

    .text
    .global _ResetVector

_ResetVector:
    rsr a0, ddr
    rsr a1, ddr

# restore registers from saved values
# idata: a0, a1
# odata: None
# changes: a0, a1

    .text
    .global _start

_start:
    rsr a0, ddr
    rsr a1, ddr

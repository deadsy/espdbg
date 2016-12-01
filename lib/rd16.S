# read 16 bit value from address
# idata: adr
# odata: val
# changes: a0

    .text
    .global _start

_start:
    rsr a0, ddr
    l16ui a0, a0, 0
    wsr a0, ddr

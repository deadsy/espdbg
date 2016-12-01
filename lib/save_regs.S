# save registers so they can be used during debug operations
# idata: None
# odata: a0, a1
# changes: None

    .text
    .global _start

_start:
    wsr a0, ddr
    wsr a1, ddr

# read 16 x 32 bit values starting from address
# idata: adr
# odata: val x 16
# changes: a0, a1

    .text
    .global _ResetVector

# TODO - optimise for use with instruction caching
#    l32i a1, a0, 0
#    wsr a1, ddr
#    addi a0, a0, 4

_ResetVector:
    rsr a0, ddr
    l32i a1, a0, 0
    wsr a1, ddr
    l32i a1, a0, 4
    wsr a1, ddr
    l32i a1, a0, 8
    wsr a1, ddr
    l32i a1, a0, 12
    wsr a1, ddr
    l32i a1, a0, 16
    wsr a1, ddr
    l32i a1, a0, 20
    wsr a1, ddr
    l32i a1, a0, 24
    wsr a1, ddr
    l32i a1, a0, 28
    wsr a1, ddr
    l32i a1, a0, 32
    wsr a1, ddr
    l32i a1, a0, 36
    wsr a1, ddr
    l32i a1, a0, 40
    wsr a1, ddr
    l32i a1, a0, 44
    wsr a1, ddr
    l32i a1, a0, 48
    wsr a1, ddr
    l32i a1, a0, 52
    wsr a1, ddr
    l32i a1, a0, 56
    wsr a1, ddr
    l32i a1, a0, 60
    wsr a1, ddr
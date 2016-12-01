# xtensa code created by bin2py - do not edit
rd16 = (
    0x036800, # rsr a0, ddr
    0x001002, # l16ui a0, a0, 0
    0x136800, # wsr a0, ddr
)
rd32 = (
    0x036800, # rsr a0, ddr
    0x000008, # l32i.n a0, a0, 0
    0x136800, # wsr a0, ddr
)
rd8 = (
    0x036800, # rsr a0, ddr
    0x000002, # l8ui a0, a0, 0
    0x136800, # wsr a0, ddr
)
rd32_x16 = (
    0x036800, # rsr a0, ddr
    0x000018, # l32i.n a1, a0, 0
    0x136810, # wsr a1, ddr
    0x001018, # l32i.n a1, a0, 4
    0x136810, # wsr a1, ddr
    0x002018, # l32i.n a1, a0, 8
    0x136810, # wsr a1, ddr
    0x003018, # l32i.n a1, a0, 12
    0x136810, # wsr a1, ddr
    0x004018, # l32i.n a1, a0, 16
    0x136810, # wsr a1, ddr
    0x005018, # l32i.n a1, a0, 20
    0x136810, # wsr a1, ddr
    0x006018, # l32i.n a1, a0, 24
    0x136810, # wsr a1, ddr
    0x007018, # l32i.n a1, a0, 28
    0x136810, # wsr a1, ddr
    0x008018, # l32i.n a1, a0, 32
    0x136810, # wsr a1, ddr
    0x009018, # l32i.n a1, a0, 36
    0x136810, # wsr a1, ddr
    0x00a018, # l32i.n a1, a0, 40
    0x136810, # wsr a1, ddr
    0x00b018, # l32i.n a1, a0, 44
    0x136810, # wsr a1, ddr
    0x00c018, # l32i.n a1, a0, 48
    0x136810, # wsr a1, ddr
    0x00d018, # l32i.n a1, a0, 52
    0x136810, # wsr a1, ddr
    0x00e018, # l32i.n a1, a0, 56
    0x136810, # wsr a1, ddr
    0x00f018, # l32i.n a1, a0, 60
    0x136810, # wsr a1, ddr
)
rd_regs = (
    0x136800, # wsr a0, ddr
    0x136810, # wsr a1, ddr
    0x136820, # wsr a2, ddr
    0x136830, # wsr a3, ddr
    0x136840, # wsr a4, ddr
    0x136850, # wsr a5, ddr
    0x136860, # wsr a6, ddr
    0x136870, # wsr a7, ddr
    0x136880, # wsr a8, ddr
    0x136890, # wsr a9, ddr
    0x1368a0, # wsr a10, ddr
    0x1368b0, # wsr a11, ddr
    0x1368c0, # wsr a12, ddr
    0x1368d0, # wsr a13, ddr
    0x1368e0, # wsr a14, ddr
    0x1368f0, # wsr a15, ddr
)
restore_regs = (
    0x036800, # rsr a0, ddr
    0x036810, # rsr a1, ddr
)
save_regs = (
    0x136800, # wsr a0, ddr
    0x136810, # wsr a1, ddr
)
wr16 = (
    0x036800, # rsr a0, ddr
    0x036810, # rsr a1, ddr
    0x005012, # s16i a1, a0, 0
)
wr32 = (
    0x036800, # rsr a0, ddr
    0x036810, # rsr a1, ddr
    0x000019, # s32i.n a1, a0, 0
)
wr8 = (
    0x036800, # rsr a0, ddr
    0x036810, # rsr a1, ddr
    0x004012, # s8i a1, a0, 0
)

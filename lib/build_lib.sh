#!/bin/bash

ASM2PY=../tools/asm2py
LIB=../lib.py

rm $LIB

$ASM2PY rd16.S >> $LIB
$ASM2PY rd32.S >> $LIB
$ASM2PY rd32_x16.S >> $LIB
$ASM2PY rd8.S >> $LIB
$ASM2PY rd_mem.S >> $LIB
$ASM2PY rd_regs.S >> $LIB
$ASM2PY restore_regs.S >> $LIB
$ASM2PY save_regs.S >> $LIB
$ASM2PY wr16.S >> $LIB
$ASM2PY wr32.S >> $LIB
$ASM2PY wr8.S >> $LIB

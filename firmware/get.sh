#! /bin/bash

ESPTOOL=/home/jasonh/work/esptool/esptool.py

#CMD=load_ram
#CMD=read_mem
#CMD=write_mem
#CMD=write_flash
#CMD=run
#CMD=image_info
#CMD=make_image
#CMD=elf2image
#CMD=read_flash_status
#CMD=write_flash_status
#CMD=read_flash
#CMD=verify_flash
#CMD=erase_flash
#CMD=erase_region
#CMD=version

ARGS="--chip esp32 --port /dev/ttyUSB1 --baud 115200"

#$ESPTOOL $ARGS chip_id
#$ESPTOOL $ARGS flash_id
#$ESPTOOL $ARGS read_mac

#$ESPTOOL $ARGS dump_mem 0x40000000 0x60000 irom0.bin
#$ESPTOOL $ARGS dump_mem 0x3ff90000 0x10000 irom1.bin
#$ESPTOOL $ARGS dump_mem 0x3f400000 0x400000 eflash0.bin
$ESPTOOL $ARGS dump_mem 0x400c2000 0xb3e000 eflash1.bin

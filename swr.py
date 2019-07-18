#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Python script for Elecraft's KX3 that determines the SWR with and without
# tuner on a given set of frequencies.
#
# You will need the python packages pyserial, bitstring, and bitarray.
# You can install them via
#
# sudo pip install pyserial, bitstring, bitarray
#
# By Ulrich Thiel (DK1UT), 2019
# https://ulthiel.com/dk1ut
# mail@ulthiel.com
#

# Set baudrate
baudrate=38400

# Set srial port (script will try to determine it automatically)
port=""

#Frequencies to test (in KHz)
freq = [ 1860, 3690, 7090, 14285, 21285 ]

#tune power
power = 10

##############################################################################
#imports
import subprocess
import re
import os
import serial
import sys
import glob
import time
from bitstring import BitArray, BitStream
from bitarray import bitarray

##############################################################################
if len(sys.argv) > 1:
	outfile = open(sys.argv[1]+".csv", 'w')

##############################################################################
#list serial ports
#from http://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/ttyUSB*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.usbserial*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

##############################################################################
#send command to kx3
def KX3Cmd( ss, sendstr ):
    cmd=sendstr+';'
    ss.write(cmd.encode())
    ret = "XXXXXXXXXXXXXXXX"
    count = 0
    while count < 2:
    	try:
    		 ret = ss.read(64)
    	except:
    		count = count + 1
    	break

    return ret

##############################################################################
#set up serial port
ports = serial_ports()
if port == "" and len(ports) == 1:
	port = ports[0]
else:
	print "No port found."
	sys.exit(0)

print "Using port " + port

ser = serial.Serial(
      port = port,
      baudrate=baudrate,
      parity=serial.PARITY_NONE,
      stopbits=serial.STOPBITS_TWO,
      bytesize=serial.EIGHTBITS,
      timeout=0.1
)

##############################################################################
#Decode SWR from display code
def DecodeSWRFromDisplay( msg ):
	swr = ""
	for c in msg:
		if c == ";" or c == "D" or c == "S" or c == "@":
			continue
		if c == ">":
			break
		cbit = bitarray(endian='little')
		cbit.frombytes(c)
		if cbit[7] == 1:
			swr = swr + "."
		cbit[7] = 0
		swr = swr + cbit.tobytes()

	return swr

##############################################################################
#Decode ATU settings
def DecodeATU( msg ):

	val = ""
	for c in msg:
		if c == ";" or c == "A" or c == "K":
			continue
		val = val + c

	#L and C network of KXAT3
	lNet = [8.0, 4.0, 2.0, 1.0, 0.5, 0.25, 0.12, 0.06]
	cNet = [1360.0, 680.0, 330.0, 164.0, 82.0, 39.0, 18.0, 10.0]

	#get decimal values for L,C,S from KXAT3 setting
	ldec = int(val[0:2], 16)
	cdec = int(val[2:4], 16)
	sdec = int(val[4:6], 16)

	#binary codes
	#we convert ldec and cdec to binary, then to string, cut off the first
	#two characters (0b), then pad with 0 to length 8.
	lbin = (str(bin(ldec))[2:]).zfill(8)
	cbin = (str(bin(cdec))[2:]).zfill(8)

	#compute values by adding up
	l = 0.0
	for i in range(0,8):
		if lbin[i] == '1':
			l = l + lNet[i]

	c = 0.0
	for i in range(0,8):
		if cbin[i] == '1':
			c = c + cNet[i]

	if sdec == 0:
		return [l,c,"ANT"]
	else:
		return [l,c,"TX"]

##############################################################################
#main program

#set tune power
oldpowerstr = KX3Cmd(ser, "PC;")
oldpowerstr = oldpowerstr.replace("PC", "")
oldpowerstr = oldpowerstr.replace(";", "")
powerstr = str(int(power)).zfill(3)
KX3Cmd(ser, "PC"+powerstr+";")

#determine swrs
swruntuned = []
swrtuned = []
atu = []
i = 0
print "| Freq(KHz) | SWR | SWRt | L | C | Side |"
print "|-----------|-----|------|---|---|------|"
if len(sys.argv) > 1:
	outfile.write("\"Freq(MHz)\",\"SWR\",\"SWRt\",\"L\",\"C\",\"Side\"\n")

for f in freq:
	fHz = str(f*1000).zfill(11)
	KX3Cmd(ser, "FA"+fHz+";") #set frequency
	time.sleep(2)

	KX3Cmd(ser, "MN023;") #ATU menu
	time.sleep(0.25)
	KX3Cmd(ser, "MP001;") #disable ATU
	time.sleep(0.25)
	KX3Cmd(ser, "MN255;") #exit menu
	time.sleep(0.25)
	KX3Cmd(ser, "SWH16;") #tune
	time.sleep(2) #wait two seconds for swr to stabilize
	swrcode = KX3Cmd(ser, "DS") #get swr
	swruntuned.append(DecodeSWRFromDisplay(swrcode))
	time.sleep(0.25)
	KX3Cmd(ser, "SWH16;") #stop tune
	time.sleep(2)

	KX3Cmd(ser, "MN023;") #ATU menu
	time.sleep(0.25)
	KX3Cmd(ser, "MP002;") #enable ATU
	time.sleep(0.25)
	KX3Cmd(ser, "MN255;") #exit menu
	time.sleep(0.25)
	KX3Cmd(ser, "SWT44;") #tune
	time.sleep(10) #give enough time for tuning
	KX3Cmd(ser, "SWH16;") #tune
	time.sleep(2) #wait two seconds for swr to stabilize
	swrcode = KX3Cmd(ser, "DS") #get swr
	swrtuned.append(DecodeSWRFromDisplay(swrcode))
	time.sleep(0.25)
	KX3Cmd(ser, "SWH16;") #stop tune
	time.sleep(0.25)
	atucode = KX3Cmd(ser, "AK;") #ATU config
	atu.append(DecodeATU(atucode))

	print str(freq[i])+" | " + str(swruntuned[i]) + " | "+str(swrtuned[i]) + " | "+str(atu[i][0])+ " | "+str(atu[i][1])+  " | "+str(atu[i][2]) + " | "

	if len(sys.argv) > 1:
		outfile.write(str(freq[i]/1000.0)+"," + str(swruntuned[i]) + ", "+str(swrtuned[i]) + ","+str(atu[i][0])+ ","+str(atu[i][1])+ ","+str(atu[i][2])+"\n")


	i = i + 1

	time.sleep(1)

if len(sys.argv) > 1:
	outfile.close()

#reset power
KX3Cmd(ser, "PC"+oldpowerstr+";")

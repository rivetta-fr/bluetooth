#!/usr/bin/python
#sqlite3 bluespam.sql "CREATE TABLE clients(id INTEGER PRIMARY KEY ASC, timestamp INT, name TEXT, mac TEXT)"

# need package hcitool, nobexftp, sqlite and python3 with pyblue and pyobex3 modules installed on computer

import os
import string
import time
import sqlite3
import bluetooth
import struct, sys
from PyOBEX import client, headers, responses

# config var
pathtofile='/home/claudior/Documents/bluetooth/bluetooth/'
filetosend="veryroadtrip.html"
looptime=20
table_name = "clients"

# connect to db sqlite
con = sqlite3.connect("./bluespam.sql")
cur = con.cursor()
# drop  table (only for dev)
# query="drop table " + table_name + ";"
# cur.execute(query)
# con.commit()
# end drop table (only for dev)
# create table cleints into sqlite
query="CREATE TABLE IF NOT EXISTS " + table_name + "(id INTEGER PRIMARY KEY ASC, timestamp INT, name TEXT, mac TEXT);"
cur.execute(query)
con.commit()

# start loop
while 1>0:
    # start scan max 10 responses without cache
    print(time.ctime() + " - scanning for device...")
    dev_scan = "hcitool -i hci0 scan --numrsp=10 --flush"
    list_dev=os.popen(dev_scan)
    tot= list_dev.read()
    tot= tot.split("\n")
    tot.pop(0)
    tot.reverse()
    tot.pop(0)
    for dev in tot:
        # get dev
        dev=dev.split("\t")
        # get channel
        get_channel = "sdptool search --bdaddr " + dev[1] + " OPUSH | sed 's/ //g' | grep Channel | cut -d: -f 2"
        channel_scan=os.popen(get_channel)
        channel=channel_scan.read()
        print(time.ctime() + " - Found \"" + dev[2] + "\" channel:"+ channel)
        if channel != "":
            # Start flow to send file
            print("Try to send file to " + dev[2])
            send_file= "obexftp -b 00:" + dev[1] + " -p " + filetosend
            # Search mac address into DB in order to not send twice to same device
            cur = con.cursor()
            query="SELECT COUNT(*) FROM " + table_name + " WHERE mac = \"" + dev[1] + "\""
            row=cur.execute(query)
            row = cur.fetchone()
            con.commit()
            # if not present into db (found new device)
            if row[0] == 0:
                print(dev[1] + " not present in database.")
                #  Get File Content
                with open(pathtofile + filetosend, 'rb') as f:
                    contents = f.read()
                # create client, connect to it and send file by obexFtp
                c = client.Client(dev[1], int(channel))
                try:

                    r = c.connect()
                    if not isinstance(r, responses.ConnectSuccess):
                        sys.stderr.write("Failed to connect.\n")
                        sys.exit(1)
                    else:
                        rs=c.put(filetosend, contents)
                        if isinstance(rs, responses.Success):
                            print("Normally file sent to " + dev[2] )
                    c.disconnect()
                except:
                    print("Impossible to reach client.")

                # insert device into db
                date=time.strftime("%s")
                cur = con.cursor()
                query = "INSERT INTO " + table_name + " VALUES(NULL, '" + date + "', '" + dev[2] + "', '" + dev[1] + "');"
                cur.execute(query)
                con.commit()
            elif row[0] > 0:
                print(dev[1] +" already present in database. Not sending file.")
    # start Ibeacon
    print(time.ctime() + " - Start ibeacon...")
    # hcitool -i hci0 cmd 0x08 0x0008 1E 02 01 1A 1A FF 4C 00 02 15 63 6F 3F 8F 64 91 4B EE 95 F7 D8 CC 64 A8 63 B5 00 00 00 00 C8 00
    dev_scan = "hcitool -i hci0 cmd 0x08 0x0008 1E 02 01 1A 1A FF 4C 00 02 15 1F 99 A0 81 95 E3 41 60 B2 88 09 92 28 3D 54 7B 00 00 00 00 C8 00" #1f99a081-95e3-4160-b288-0992283d547b   
    os.popen("hciconfig hci0 leadv 3")
    os.popen("hciconfig hci0 noscan")
    os.popen(dev_scan)
    # send during 10 sec
    time.sleep(looptime)
    os.popen("hciconfig hci0 noleadv")
    print(time.ctime() + " - Stop ibeacon...")
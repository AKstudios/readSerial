#!/usr/bin/env python

import serial
import sys
import sqlite3
import time
import datetime

#select USB0 if radio is connected to first USB port on Pi
serialport = serial.Serial("/dev/ttyUSB0", 115200) # make sure baud rate is the same

#set location of sqlite db & table name
db = '/home/pi/serial_db.sqlite'
tn = 'SERIAL_DB'

#Create SQLLite Database, may already exist, handle exception
def create_db():
    #tn = 'SERIAL_DB'    #table name
    nf1 = 'node_id'     #new field
    ft1 = 'INTEGER'     #field type
    nf2 = 'sensor_type'
    ft2 = 'TEXT'
    nf3 = 'sensor_value'
    ft3 = 'REAL'
    nf4 = 'timestamp'
    ft4 = 'INTEGER'

    conn = sqlite3.connect(db) #connect to db
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS {tn} ({nf1} {ft1}, {nf2} {ft2}, {nf3} {ft3}, {nf4} {ft4}, PRIMARY KEY({nf1},{nf2}))".format(tn=tn, nf1=nf1, ft1=ft1, nf2=nf2, ft2=ft2, nf3=nf3, ft3=ft3, nf4=nf4, ft4=ft4))

    conn.commit()   #commit changes to db
    conn.close()    #close connection

#Read Serial
def read_serial():
    serialport.flushInput() #clear input serial buffer
    serialport.flushOutput() #clear output serial buffer
    while True: # keep reading serial port and write to file till the end of time
        data = serialport.readline() #expecting this format -> "i:1,t:25.44,h:40.23,l:34.00"
        #print data
        if data: # check if data is not empty
            final_data = parse(data)
            write_db(final_data)

#Parse data string
#strip() removes trailing \n
def parse(data):
    final_data = {}
    for p in data.strip().split(","):
        k,v = p.split(":")
        final_data[k] = v
    return final_data

#Write data to SQLiteDB
def write_db(final_data): # one row per node, per sensor value, overwrite existing value
    conn = sqlite3.connect(db) #connect to db
    c = conn.cursor()

    ts = int(time.time()) #get epoch time in seconds
    id = final_data.pop("i") #get sensor id
    #st = sensor type, sv = sensor value
    for k,v in final_data.iteritems():
        st = "INSERT OR REPLACE INTO {tn} VALUES ({id},'{st}', {sv}, {ts})".format(id=id, tn=tn, st=k, sv=v, ts=ts)
        print st
        c.execute(st)

    conn.commit()   #commit changes to db
    conn.close() #close connection to SQL file after writing to it

#run
create_db()
read_serial()

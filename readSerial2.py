#!/usr/bin/env python

# Import the necessary shiz
import serial
import sys
import sqlite3
import time
import datetime
import requests
import dictionary
import os
import time


# Define sensor id and flag as global variables
id = 0
flag = True

# Select USB0 if radio is connected to first USB port on Pi
serialport = serial.Serial("/dev/ttyUSB0", 115200) # make sure baud rate is the same

# Set location of sqlite db & table name
db = '/home/pi/serial_db.sqlite'
tn = 'SERIAL_DB'


# Create SQLLite Database, may already exist, handle exception
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


# Read Serial port
def read_serial():
    serialport.flushInput() #clear input serial buffer
    serialport.flushOutput() #clear output serial buffer
    while True: # keep reading serial port and write to file till the end of time
        data = serialport.readline() #expecting this format -> "i:1,t:25.44,h:40.23,l:34.00\n"
        #print data
        if data[0]=='i': # check if data is not empty and entire string is being sent (first value is always "i", which is node ID)
            final_data = parse(data) # parse data
            write_db(final_data)    # write data to SQLite db
            restAPI(final_data) # push data to HA via rest API
            checkFlag(final_data) # check if flag is False, then edit YAML files & restart HA
            print("\nWaiting for serial data ...")

# Parse data string
def parse(data):
    final_data = {}
    for p in data.strip().split(","): #strip() removes trailing \n
        k,v = p.split(":")
        final_data[k] = v if v else 0.00
    print ("Final Data:")
    print (final_data)
    return final_data


# Write data to SQLiteDB
def write_db(final_data): # one row per node, per sensor value, overwrite existing value
    global id # define again so glabal copy of id is also set
    global flag

    conn = sqlite3.connect(db) #connect to db
    c = conn.cursor()

    ts = int(time.time()) #get epoch time in seconds
    id = final_data.pop("i") #get sensor id
    #id = 156
    #st = sensor type, sv = sensor value
    for k,v in final_data.iteritems():
        # check if data exists by checking node ID and sensor type
        a = "SELECT * FROM {tn} WHERE {nodeid} = '{id}' AND {stype}='{st}'".format(sv='sensor_value', stype='sensor_type', st=k, tn=tn, nodeid='node_id', id=id)
        print(a)
        c.execute(a)
        data = c.fetchone() #returns one matching row; fetchall() returns all matching rows
        if not data:
            flag = False

        st = "INSERT OR REPLACE INTO {tn} VALUES ({id},'{st}', {sv}, {ts})".format(id=id, tn=tn, st=k, sv=v, ts=ts)
        print st
        c.execute(st)

    conn.commit()   #commit changes to db
    conn.close() #close connection to SQL file after writing to it


# Publish data to HA via restAPI
def restAPI(final_data):
    for k,v in final_data.iteritems():
        #id = final_data.pop("i") #get sensor id
        st = dictionary.sensorType[k]
        su = dictionary.sensorUnit[k]

        url = 'http://192.168.1.212:8123/api/states/sensor.%s_%s' % (st, id)
        headers = {'x-ha-access': 'Abudabu1!',
                'content-type': 'application/json'}

        data  = '{"state" : "%s", "attributes": {"friendly_name": "%s", "unit_of_measurement": "%s"}}' % (v, st, su)

        req = requests.Request('POST', url, headers=headers, data=data)
        prepared = req.prepare()
        pretty_print_POST(prepared)

        #response = requests.post(url, headers=headers, data=data)
        #print(response.text)
        print("\nSending data via REST API\n")
        s = requests.Session()
        s.send(prepared)


# Print POST request in a pretty way
def pretty_print_POST(req):
    print('{}\n{}\n{}\n\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))


# Rewrite custom sensors YAML file with new info
def edit_customsensors_YAML(final_data):
    target = open('/home/pi/.homeassistant/custom_sensors.yaml', 'w') #open file in write mode
    target.truncate() # clear file
    target.write("#Custom sensors\n")

    for k,v in final_data.iteritems():
        st = dictionary.sensorType[k]
        su = dictionary.sensorUnit[k]
        YAMLstring = "- platform: customsensor\n  name: %s %s\n  unit_of_measurement: '%s'\n" % (st, id, su)
        target.write(YAMLstring)

    target.write("\n")
    target.close() # important - close file

    print("Adding new sensor to HA")
    print("custom_sensors.yaml edited")


# Rewrite custom groups YAML file with new info
def edit_customgroups_YAML(final_data):
    target = open('/home/pi/.homeassistant/custom_groups.yaml', 'w') #open file in write mode
    target.truncate() # clear file
    target.write("#Custom groups\n")
    target.write("Group {id}:\n  entities:\n".format(id=id))

    for k,v in final_data.iteritems():
        st = dictionary.sensorType[k]
        su = dictionary.sensorUnit[k]
        YAMLstring = "    - sensor.%s_%s\n" % (st, id)
        target.write(YAMLstring)

    target.write("  name: Group {id}\n".format(id=id))

    target.write("\n")
    target.close() # important - close file

    print("Adding new groups to HA")
    print("custom_groups.yaml edited")


# Rewrite custom customize YAML file with new info
def edit_customcustomize_YAML(final_data):
    target = open('/home/pi/.homeassistant/custom_customize.yaml', 'w') #open file in write mode
    target.truncate() # clear file
    target.write("#Customize custom nodes\n")

    for k,v in final_data.iteritems():
        st = dictionary.sensorType[k]
        su = dictionary.sensorUnit[k]
        si = dictionary.sensorIcon[k]
        sn = dictionary.sensorName[k]
        YAMLstring = "sensor.%s_%s:\n  friendly_name: %s\n  icon: %s\n" % (st, id, sn, si)
        target.write(YAMLstring)

    target.write("\n")
    target.close() # important - close file

    print("Adding new groups to HA")
    print("custom_customize.yaml edited")


# Check if flag is false, then edit YAML files & restart HA
def checkFlag(final_data):
    global flag
    if not flag:
        print("New node detected")
        edit_customsensors_YAML(final_data)
        edit_customgroups_YAML(final_data)
        edit_customcustomize_YAML(final_data)
        flag = True  # set flag as true
        print("Restarting Home Assistant ...")
        os.system('sudo systemctl restart home-assistant@pi') # very important - restart home assistant after editing config files
        for i in range(10,0,-1):
            time.sleep(1)
            sys.stdout.write(str(i)+' ')
            sys.stdout.flush()
        #time.sleep(15) # delay for 15 seconds till HA is properly restarted


#run
create_db()
read_serial()

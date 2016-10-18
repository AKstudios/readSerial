# readSerial

This is a Python script that reads all incoming data on the serial port on Raspberry Pi and writes to an SQLite database. The SQLite table is created if it doesn’t exist.

This script is created to read data from a Moteino that’s connected to the Raspberry Pi via USB. The Moteino receives data from other Moteinos, each identified by their node IDs. All incoming data is expected to be terminated by line break (\n or println in Arduino) and in the following format:

<i>i:1,t:25.44,h:40.23,l:34.00</i> (example)

The letters indicate sensor type, and the numbers indicate sensor value. In the above example, i is node ID, t is temperature, h is relative humidity and l is light intensity. The script splits each data set by commas and makes a dictionary of the data split by colons. The actual sensor type, sensor value or number of sensor types is not relevant, as the script splits any incoming data, as long as it is formatted correctly.

The SQLite database is overwritten each time new data comes in from the same node. The Node ID and the sensor type are set as primary keys in the database. This database is meant to act as a temporary place for all incoming data which can then be requested by any backend service.

This script is designed to run alongside Home Assistant (https://home-assistant.io/) running on a Raspberry Pi. When a new node ID is detected, it is automatically configured in the appropriate YAML files and the Pi reboots. After reboot, the new node should appear as a seperate card in Home Assistant.

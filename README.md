# readSerial

This is a Python script that reads all incoming data on the serial port on Raspberry Pi and writes to an SQLite database. The SQLite table is created if it doesn’t exist.

This script is created to read data from a Moteino that’s connected to the Raspberry Pi via USB. The Moteino receives data from other Moteinos, each identified by their node IDs. All incoming data is expected to be terminated by line break (\n or println in Arduino) and in the following format:

<i>i:1,t:25.44,h:40.23,l:34.00</i> (example)

The letters indicate sensor type, and the numbers indicate sensor value. The script splits each data set by commas and makes a dictionary of each value splitting by colons. The actual sensor type or value or number of sensor types is not relevant, as the script splits any incoming data, as long as it is formatted correctly.

The SQLite database is overwritten each time new data comes in from the same node. The Node ID and the sensor type are set as primary keys in the database. This database is meant to act as a temporary place for all incoming data which can then be requested by any backend service.

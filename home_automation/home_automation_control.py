'''import serial
from serial import Serial
import time

def light_on_off(i):
    serialcomm = serial.Serial('COM8', 9600)
    print('############')
    print(i)
    print('############')
        serialcomm.timeout = 1

        serialcomm.write(i.encode())

    time.sleep(10)

    print('################')
    print(serialcomm.readline().decode('ascii'))
    print('############')
    serialcomm.close()
     print('############')
    print(i)
    print(b'L')
    print(i)
    #print('############')
    ser = serial.Serial('COM8',9600,timeout = 1)
    val = i.encode()
    #ser.write(val)
ser = serial.Serial('COM8', 9600, timeout=1)

try:
    ser.write(b'H')
    print(ser.write(b'H'))
except:
    print('error')'''



import serial
from serial import Serial
import time

ser = serial.Serial('COM8', 9600)

ser.write(b'H')
# LED turns on

ser.write(b'L')
# LED turns off

ser.write(b'H')
# LED turns on

ser.write(b'L')
# LED turns off

ser.close()
exit()
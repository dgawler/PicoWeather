# Weather app for the Pico W 
#
# Will use this to collect inside weather and add it to our outside weather data 
# to give a full picture.
#
# Written for a Pico W with the CoreElectronics Piico Dev board and a BME280 environment
# sensor which can collect temperature, humidity, and altitude (barometric pressure).
#
# The data is sent to a server over the network that is written in Python.
#
# Dean Gawler, March 2023
#
from machine import reset, Pin
import network
import ntptime
import socket
import sys
import time

# Modules from Core Electronics for the Piicodev hardware and sensors
from PiicoDev_BME280 import PiicoDev_BME280
from PiicoDev_Unified import sleep_ms

# Read our wifi modules and the wifi config file. This defines:
# host, port, ssid, ssid_password
import pico_wifi
import pico_wifi_config 


######################################## FUNCTIONS ##########################################
## Open a socket to our weather server. The host and port details come from the 
# pico_wifi_config.py file which has been imported.
#
def ConnectToServer():
    CONNECTED_STATUS=False
    MAX_TRIES=5
    TRIES=0

    connected_status = False
    while TRIES < MAX_TRIES and not CONNECTED_STATUS:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # instantiate
            s.connect((pico_wifi_config.host, pico_wifi_config.port))
            CONNECTED_STATUS = True
        except:
            ## Just want to pass and return the connected_status
            CONNECTED_STATUS = False
            pass
        if not CONNECTED_STATUS:
            TRIES += 1
            sleep(1)
    
    return (CONNECTED_STATUS, s)


# Flash the LED identified by led_id and the specified number of flashes (default=5)
#
def FlashLED(led_id,flashes=5):
    for i in range(0,flashes):
        led_id.value(True)
        sleep_ms(200)
        led_id.value(False)
        sleep_ms(200)


## Get the current date and time, and return the following values:
##     Minutes (MM) as an integer
##     "MM/DD/YY,HH:MM" as a string
##
## The reason we want the minutes is so the calling routine can determine if the time minutes
## is a multiple of 10, as we only want to collect data every 10 minute mark (e.g. on the hour,
## then at 10 past, 20 past, 30 past, etc...
#
def GetCurrentTime():
    dt = time.localtime()
    YYYY=dt[0]
    MON='%02d' % dt[1]
    DAY='%02d' % dt[2]
    HH='%02d' % dt[3]
    MM='%02d' % dt[4]    
    TDATE=str(MON) + '/' + str(DAY) + '/' + str(YYYY-2000) + ',' + str(HH) + ':' + str(MM)    
    return int(MM), str(TDATE)


## Read the temperature and humidity from the BME280 sensor
## Could read altitude too, but we don't want it
#
def ReadSensor(sensor):
    try:
        tempC, presPa, humRH = sensor.values()
        pres_hPa = presPa / 100 # convert air pressurr Pascals -> hPa (or mbar, if you prefer)
    except:
        tempC = -999
        pres_hPa = -999
        humRH = -999
    return (tempC, pres_hPa, humRH)


## Send our string of weather data to the weather web server for collection
#
def SendData(data):
    SENT_OK=False
    MAX_TRIES=5
    TRIES=0

    while TRIES < MAX_TRIES and not SENT_OK:
        try:
            is_connected, client_socket = ConnectToServer()
            if is_connected:

                # Send our data to the server
                try:
                    client_socket.sendall(data.encode())  # send message
                except:
                    ## Just pass, as we will return status to calling function                    
                    pass

                #...and then read it back from our server to ensure it was sent correctly
                try:
                    received_data = client_socket.recv(1024).decode()  # receive response
                except:
                    ## Just pass, as we will return status to calling function
                    pass

                if received_data == data:
                    SENT_OK=True
                
                # Always close the socket gracefully
                client_socket.close()
                
        except InterruptedError:
            print("Socket operation interrupted")
        except TimeoutError:
            print("Timeout on socket operation")
        except Exception as e:
            print(f"Failed with string: >>>{e}<<<")
        
        # Increment try count, sleep a bit, and go again
        TRIES += 1
        time.sleep(5)

    ## Return the status of sending the data
    return SENT_OK


########################################## MAIN #############################################

# We will use the Pico onboard LED to indicate when we are gathering weather data
# and are sending it to the network, so initialise the LED and tell us we are alive.
#
led = machine.Pin("LED", machine.Pin.OUT) # setup the onboard LED light for display
FlashLED(led,10)

# Connect to the wifi and set the time using an NTP server
#
connected = pico_wifi.StartWifi()
if not connected:
    print("Failed to connect to wifi")
    led.value(True)
    sys.exit(2)

# Initialise the BME280 weather sensor and get the current altitude as a baseline
#
time.sleep(1)
sensor = PiicoDev_BME280()

#### zeroAlt = sensor.altitude() # take an initial altitude reading
## Need a list to track which time period (00,10,20,30,40,50) we have recorded weather
## values for to make sure that we don't collect data twice for the same time period.
#
weather_times = { "0":False, "10":False, "20":False, "30":False, "40":False, "50":False }

# Gather weather data periodically and send it to our weather server
#
running = True
while running:
    # Get the time
    minutes, my_time=GetCurrentTime()

    # If the time minutes are 0,10,20,..,50 then send the data to the server
    if minutes % 10 == 0:
        # Check to see if we have already collected weather data for this time period
        #
        MM=str(minutes)
        if weather_times.get(MM) == False:
            # Set the flag to True for this time period, and all other time periods to False
            #
            for minutes in weather_times:
                weather_times[minutes] = False;
            weather_times[MM] = True
            
            # Turn our onboard LED on to show that we are doing something
            FlashLED(led,2)

            # Read data from the sensor and format it for the server - values only need to be 1 decimal place
            tempC, presPa, humRH = ReadSensor(sensor)
            DATA_LINE = my_time + "," + str("{:.1f}".format(humRH)) + "," + str("{:.1f}".format(tempC))

            # Open a connection to the server, then send the data. The server should return the same
            # data to us as proof that it received it.
            #
            sent_ok = SendData(DATA_LINE)

            ## If sent_ok is not True, then could do some further error processing...
            
            # Sleep for 2 seconds so that we can see the LED for debug purposes, then do it all again
            ## led.toggle()
            time.sleep(2)

    ## Sleep for enough time to get 'into' the next minute. This routine only
    ## takes 1 second to run, so sleeping for 25 seconds should be perfect.
    #
    time.sleep(25)


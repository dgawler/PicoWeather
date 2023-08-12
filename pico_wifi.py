# Wifi functions for connecting to a wireless network on a Pico W
#
# Dean Gawler, March 2023
#
import network
import ntptime
import time
from pico_wifi_config import host, port, ssid, ssid_password

######################################## FUNCTIONS ##########################################

## Connect to our local wifi SSID
#
def ConnectWifi():
    # Attempt to activate wifi interface and connect to our network
    global ssid
    global ssid_password
    connected_status = False
    
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(False)
        wlan.disconnect()
        wlan.active(True)
        time.sleep(2)
        wlan.connect(ssid, ssid_password)
    except:
        pass
    finally:
        connected_status = WaitWLAN(wlan) and wlan.isconnected()    # should return True if connected

    ## (ip, subnet, gateway, dns) = wlan.ifconfig()
    ## print(f"IP is: {ip}\nSubnet is: {subnet}\nGateway is: {gateway}\nDNS is: {dns}")

    return connected_status


## Get the time from the NTP server - this program cannot really make use of proper time
## but will do it anyway...might enhance the program in ways that need it.
#
def SetNTPTime():
    ntptime.settime()


## Wait for the WLAN interface to come up
#
def WaitWLAN(wlan):
    max_wait = 10
    wlan_connected_status = False

    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        time.sleep(1)

    if wlan.status() == 3:
        wlan_connected_status = True

    return wlan_connected_status


########################################## MAIN #############################################

# Connect to the wifi and set the time using an NTP server
#
def StartWifi():
    time.sleep(2)
    wlan_up = ConnectWifi()
    if wlan_up:
        SetNTPTime()
    return wlan_up


if __name__ == '__main__':
    StartWifi()

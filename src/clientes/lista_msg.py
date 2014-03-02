#
# Manejador de la cola de mensajes y envio de archivos
#
# Hector Dominguez - Febrero 11, 2014
#

import requests
import json
import sys
import time
import argparse
import beanstalkc
import os
import socket
import serial
import traceback

import settings
from settings import *
from client import ClientProtocol as cpro


Metrics = {
    "queue_sent": 0,
    "queue_errors": 0,
    "server_200s": 0,
    "server_500s": 0,
    "server_400s": 0,
    "server_comm_failures": 0,
}

Rollup = {} 
Jobs = []

llave = None

def main():
    parser = argparse.ArgumentParser(description="Video Net")
    debug = False
    parser.add_argument('--debug', '-d', dest='debug', \
        action='store_true', default=False, help="modo de depuracion")
    args = parser.parse_args()
    settings.DEBUG = args.debug 

    while(1):
        if not is_registered():
            register(DID)

        # Wait for ROLLUP_TIMEOUT seconds for new data, if read
        # times out we go ahead and flush the rollups
        try:
            job = bsq.reserve(timeout=ROLLUP_TIMEOUT)
        except beanstalkc.DeadlineSoon, e:
            logger.debug("Beanstalkd DEADLINE_SOON, %s" % e)
            continue

        if job is None:
            debugp("Reserve timeout")
            if len(Jobs) > 0:
                process_rollup_data()
            continue

        # Add the new job to a rollup
        bits = job.body.split(" ")

        if len(bits) != 4:
            job.delete()
            emsg = "Bad data in queue %s" % bits 
            inc("queue_errors")
            debugp(emsg)
            logger.error(emsg)
            continue

        # use the mote id : sensor id as a key
        key = "%s:%s" % (bits[0], bits[1])
        if not Rollup.has_key(key):
            Rollup[key] = []
        # append the exploded array of sensor data to the rollup
        Rollup[key].append(bits)
        Jobs.append(job)
        if len(Jobs) >= MAX_ROLLUP_SIZE:
            debugp("Reached max rollup size, sending sensor readings")
            process_rollup_data()

def deregister():
    global llave
    llave = None
 
def is_registered():
    if llave is None:
        return False
    return True

def device_meta():
    meta = {}
    try:
        ser = serial.Serial(CELLULAR_PORT, 9600)
    except:
        return meta 
    meta["version"] = VERSION
    meta["model"] = MODEL
    meta["imei"] = get_cell_field("AT+CIMI", ser)
    meta["cell_manf"] = get_cell_field("AT+CGMI", ser)
    meta["cell_model"] = get_cell_field("AT+CGMM", ser)    
    meta["cell_num"] = get_cell_field("AT+CNUM", ser).split(",")[1].strip('"')
    meta["mac"] = get_bb_mac()
    return meta

def get_bb_mac():
    f = open(SYS_MAC)
    mac = f.read().strip()
    f.close()
    return mac

def get_cell_field(command, ser):
    ser.write("%s\r" % command)
    line = ser.readline()
    line = ser.readline().strip()
    ser.readline()
    ser.readline()
    return line 

def register(did):
    global llave
    payload = { "did": did, "meta": device_meta() }
    headers = {"content-type": "application/json"}
    debugp("registering to: %s" % REGISTER_URL)
    try:
        req = requests.post(REGISTER_URL, data=json.dumps(payload), headers=headers) 
        resp = req.json()
        llave = resp['token']
        debug = "Registered, token: %s" % llave 
        logger.info(debug)
        debugp(debug)
    except Exception as ex:
        logger.error("unable to register with api.")
	e = sys.exc_info()[0]
	logger.error("Error: %s", e)
	debugp("Error: %s" % e)
        debugp(traceback.format_exc())
        inc("server_comm_failures")
	time.sleep(FAIL_SLEEP)
   

def update_stats():
    fh = open(STATS_FILE, 'w')
    fh.write(json.dumps(Metrics, indent=4)) 
    fh.close()
        

def process_rollup_data():
    global Rollup
    request_body = []
    for r in Rollup.iteritems():
        try:
            payload = []
            for log_item in r[1]:
                data = [int(log_item[2]), log_item[3]]
                payload.append(data)
        
            key = r[0].split(":")
            mid = key[1]
        except ValueError:
            emsg = "Error validating mid %s" % r[0]
            logger.error(emsg)
            debugp(emsg)
            continue
        did_rollup = {
            "device": DEVICE_ID,
            "mid": mid,
            "data": payload
        }
        request_body.append(did_rollup)
    
    if post_sensor_data(request_body):
        purge_jobs() # delete processed
    else:
        release_jobs() # requeue on fail
        time.sleep(FAIL_SLEEP) # wait between failures
    Rollup = {}
    update_stats()

# Release all beanstalk jobs in process
# This is called when an error occurs
def release_jobs():
    debugp("releasing %d jobs" % len(Jobs))
    while len(Jobs) > 0:
        j = Jobs.pop()
        j.release()

# Purge beanstalk jobs we have processed    
def purge_jobs():
    debugp("purging %d jobs" % len(Jobs))
    while len(Jobs) > 0: 
        j = Jobs.pop()
        j.delete()
        inc("queue_sent")

def inc(metric):
    Metrics[metric] = Metrics[metric] + 1

# Sends rolled up sensor data to the Rest service.
def post_sensor_data(payload):
    payload = json.dumps(payload)

    headers = {
       "content-type": "application/json",
    }
    auth = (llave,"")
    debugp("Posting to: %s" % DATALOGGER_URL)
    debugp("Auth: %s:%s" % auth)
    debugp(payload)
    try:
        r = requests.post(DATALOGGER_URL,
        data=payload, headers=headers, auth=auth)
    except requests.exceptions.ConnectionError:
        logger.error("unable to communicate with rest server.")
        logger.error("interface %s" % get_lan_ip()) 
        inc("server_comm_failures")
        time.sleep(FAIL_SLEEP)
        return False
    
    debugp("http status %d %s" % (r.status_code, r.text))
    if r.status_code == 200:
        inc("server_200s")
        return True
    else:
        if r.status_code == 401:
            deregister()	
        if r.status_code >= 400 and r.status_code < 500:
            inc("server_400s")
        if r.status_code >= 500 and r.status_code < 600:
            inc("server_500s")
        logger.error("http error %d %s", r.status_code, r.text)
        return False
    return False

if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "ppp0",
            "eth0",
            "wlan0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return "%s - %s" % (ifname, ip)

if __name__ == "__main__":
   main()
    

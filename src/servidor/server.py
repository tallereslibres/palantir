'''
Created on Feb 08, 2014

@author: Hector Dominguez
'''

import httplib
import base64
import json
import datetime as dt
import time as tm
from pytz import timezone
import numpy as np
from twisted.internet import reactor
from autobahn.websocket import WebSocketServerFactory, \
                               WebSocketServerProtocol, \
                               listenWS
 
class EchoServerProtocol(WebSocketServerProtocol):
 
	
    def onMessage(self, msg, binary):
		self.msg = msg
		collector = DataCollector(self)
        print msg
        self.sendMessage(msg, binary)
 
if __name__ == '__main__':
    factory = WebSocketServerFactory("ws://localhost:9000")
    factory.protocol = EchoServerProtocol
    listenWS(factory)
    reactor.run()
	
	

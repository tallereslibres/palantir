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
import settings.py
import logger.py

class ServerProtocol(WebSocketServerProtocol):
 
   def onConnect(self, request):
      print("Client connecting: {}".format(request.peer))

   def onOpen(self):
      print("WebSocket connection open.")

   def onMessage(self, payload, isBinary):
      if isBinary:
         print("Binary message received: {} bytes".format(len(payload)))
      else:
         print("Text message received: {}".format(payload.decode('utf8')))
         # Add command parsing

      ## echo back message verbatim
      self.sendMessage(payload, isBinary)

   def onClose(self, wasClean, code, reason):
      print("WebSocket connection closed: {}".format(reason))
 
if __name__ == '__main__':
    factory = WebSocketServerFactory("ws:"+)
    factory.protocol = EchoServerProtocol
    listenWS(factory)
    reactor.run()
  
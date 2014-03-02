'''
Created on Feb 08, 2014

@author: Hector Dominguez


'''

from twisted.internet import reactor
from autobahn.websocket import WebSocketClientFactory, \
                               WebSocketClientProtocol, \
                               connectWS
import settings.py
import logger.py
 
class ClientProtocol(WebSocketClientProtocol):
 
   def Register(self):
      self.sendMessage("{\"command\":\"register\",\"DID\":" + DID + "\"")
      
 
   def onOpen(self):
      self.sendHello()
 
   def onMessage(self, msg, binary):
      print "Got echo: " + msg
      reactor.callLater(1, self.sendHello)
 
 
if __name__ == '__main__':
 
   factory = WebSocketClientFactory("ws://localhost:9000", debug = DEBUG_COMMS)
   factory.protocol = ClientProtocol
   connectWS(factory)
   reactor.run()
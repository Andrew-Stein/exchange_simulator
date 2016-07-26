import csv
import random
import datetime
import os.path
import dateutil.parser

import threading
import re
import json

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer   import ThreadingMixIn


###########################################################
#
# Test Data

def generate_csv():
	price  = 100.0
	spread = 10.0
	time   = datetime.datetime.today().replace(hour = 8, minute = 0, second = 0, millisecond = 0)
	with open('test.csv', 'wb') as f:
		writer = csv.writer(f)
		while time.hour < 18:
			writer.writerow([time, price - spread / 2, price + spread / 2])
			price  += random.random() * 0.5 - 0.25
			spread += random.random() * 0.1 - 0.05
			time   += datetime.timedelta(minutes = 1)

def read_csv():
	with open('test.csv', 'rb') as f:
		for time, bid, ask in csv.reader(f):
			yield dateutil.parser.parse(time), bid, ask

###########################################################
#
# App

_start    = None
_position = 0
_pnl      = 0
_data     = None

def handle_query(x):
	now = datetime.datetime.now() - _start
	print 'Query received; %s elapsed' % now
	
	prev  = _data[0]
	start = prev[0]
	
	for row in _data:
		if (row[0] - start) > now:
			break
		prev = row
	
	return {
		'bid': prev[1],
		'ask': prev[2]
	}

def handle_buy(x):
	global _position
	global _pnl

	buy       =  float(handle_query(None)['bid'])
	_position += float(x)
	_pnl      -= float(x) * buy

	print "Bought %s at $%s" % (float(x), buy)
	print "Position: %s" % _position
	print "PnL: %s" % _pnl
	
	return {
		'pnl': _pnl,
		'position': _position
	}


def handle_sell(x):
	global _position
	global _pnl

	sell      =  float(handle_query(None)['ask'])
	_position -= float(x)
	_pnl      += float(x) * sell

	print "Sold %s at $%s" % (float(x), sell)
	print "Position: %s" % _position
	print "PnL: %s" % _pnl

	return {
		'pnl': _pnl,
		'position': _position
	}	

__app__ = {
	'/query/': handle_query,
	'/buy/':   handle_buy,
	'/sell/':  handle_sell
}

###########################################################
#
# Server

class RequestHandler(BaseHTTPRequestHandler):

	def do_GET(self):
		for route, handler in __app__.iteritems():
			if None != re.search(route, self.path):
				self.send_response(200)
				self.send_header('Content-Type', 'application/json')
				self.end_headers()
				self.wfile.write(json.dumps(handler(self.path[len(route):])))
				return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	allow_reuse_address = True
	def shutdown(self):
		self.socket.close()
		HTTPServer.shutdown(self)

class SimpleHttpServer():
	def __init__(self, ip, port):
		self.server = ThreadedHTTPServer((ip,port), RequestHandler)

	def start(self):
		self.server_thread = threading.Thread(target=self.server.serve_forever)
		self.server_thread.daemon = True
		self.server_thread.start()

	def waitForThread(self):
		self.server_thread.join()

	def stop(self):
		self.server.shutdown()
		self.waitForThread()

def run_server():
	server = SimpleHttpServer('0.0.0.0', 8080)
	print 'HTTP server started on port 8080'
	server.start()
	server.waitForThread()

###########################################################
#
# Main

if __name__ == '__main__':	
	if not os.path.isfile('test.csv'):
		generate_csv()
	_data  = list(read_csv())
	_start = datetime.datetime.now()
	run_server()




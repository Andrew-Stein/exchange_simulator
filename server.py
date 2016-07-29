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
# Server

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	allow_reuse_address = True
	def shutdown(self):
		self.socket.close()
		HTTPServer.shutdown(self)

def _get(req_handler, routes):
	for name, handler in routes.__class__.__dict__.iteritems():
		if hasattr(handler, "__route__") and None != re.search(handler.__route__, req_handler.path):
			req_handler.send_response(200)
			req_handler.send_header('Content-Type', 'application/json')
			req_handler.end_headers()
			query = req_handler.path[len(handler.__route__):]
			data  = json.dumps(handler(routes, query))
			req_handler.wfile.write(data)
			return

def run(routes, host = '0.0.0.0', port = 8080):

	class RequestHandler(BaseHTTPRequestHandler):
		def log_message(self, *args, **kwargs):
			pass
		def do_GET(self):
			_get(self, routes)

	server = ThreadedHTTPServer((host, port), RequestHandler)
	thread = threading.Thread(target = server.serve_forever)
	thread.daemon = True
	thread.start()

	print 'HTTP server started on port 8080'
	
	thread.join()
	server.shutdown()
	server.start()
	server.waitForThread()

def route(path):
	def _route(f):
		setattr(f, '__route__', path)
		return f
	return _route

###########################################################
#
# App

class App(object):

	def __init__(self):		
		self._start    = datetime.datetime.now()
		self._position = 0
		self._pnl      = 0
		self._data     = list(read_csv())

	@route('/query/')
	def handle_query(self, x):
		now = datetime.datetime.now() - self._start
		print 'Query received @ t%s' % now
		
		prev  = self._data[0]
		start = prev[0]
		
		for row in self._data:
			if (row[0] - start) > now:
				break
			prev = row
		
		return {
			'bid': prev[1],
			'ask': prev[2]
		}

	@route('/sell/')
	def handle_sell(self, x):
		sell =  float(self.handle_query(None)['ask'])
		self._position -= float(x)
		self._pnl      += float(x) * sell

		print "Sold %s at $%s. Position: %s, PnL: %s" % (float(x), sell, self._position, self._pnl)

		return {
			'pnl':      self._pnl,
			'position': self._position
		}	

###########################################################
#
# Main

if __name__ == '__main__':	
	if not os.path.isfile('test.csv'):
		generate_csv()
	run(App())




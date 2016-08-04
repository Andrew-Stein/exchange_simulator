
from server import *

import os.path
import dateutil.parser

import csv
import threading
import re
import json

from itertools import izip
from copy     import copy
from random   import normalvariate, random
from datetime import timedelta, datetime
from math     import ceil

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer   import ThreadingMixIn

###########################################################
#
# Config

# Sim params
SIM_LENGTH  = timedelta(hours = 8)
MARKET_OPEN = datetime.today().replace(hour = 0, minute = 30, second = 0)

# Trades mid
MIN_SPD = 2.0
MAX_SPD = 6.0
STD_SPD = 0.1

# Trades
OVERLAP = 4

# Mid
MIN_PX  = 60.0
MAX_PX  = 150.0
STD_PX  = 0.2

###########################################################
#
# Test Data

def bwalk(min, max, std):
    rng = max - min
    while True:
        max += normalvariate(0, std)
        yield abs((max % (rng * 2)) - rng) + min

def times(t0, tmin, tmax, tsig):
    for ms in bwalk(tmin, tmax, tsig):
        yield t0
        t0 += timedelta(milliseconds = abs(ms))

def market(t0):
    ts = times(t0, 50, 500, 50)
    ps = bwalk(MIN_PX, MAX_PX, STD_PX)
    ss = bwalk(MIN_SPD, MAX_SPD, STD_SPD)
    return izip(ts, ps, ss)
        
def orders(hist):
    for t, px, spd in hist:
        side  = 'sell' if random() > 0.5 else 'buy'
        dist  = spd / OVERLAP
        sig   = px + (- spd / 2 if side == 'buy' else spd / 2)
        order = round(normalvariate(sig, dist), 2)
        size  = int(abs(normalvariate(0, 100)))
        yield t, side, order, size

###########################################################
#
# Order Book

def add_book(book, order, size, _age = 10):
    yield order, size, _age
    for o, s, age in book:
        if age > 0:
            yield o, s, age - 1

def clear_order(order, size, book, notional = 0):
    (top_order, top_size, age), tail = book[0], book[1:]
    if order > top_order:
        notional += min(size, top_size) * top_order
        sdiff = top_size - size
        if sdiff > 0:
            return notional, list(add_book(tail, top_order, sdiff, age))
        elif len(tail) > 0:
            return clear_order(order, -sdiff, tail, notional)
        
def clear_book(buy = None, sell = None):
    while buy and sell:
        order, size, _ = buy[0]
        new_book = clear_order(order, size, sell)
        if new_book:
            sell = new_book[1]
            buy  = buy[1:]
        else:
            break
    return buy, sell

def order_book(orders, book):
    for t, side, order, size in orders:
        new = add_book(book.get(side, []), order, size)
        book[side] = sorted(new, reverse = side == 'buy', key = lambda x: x[0])
        bids, asks = clear_book(**book)
        yield t, bids, asks
        
def top(bids, asks):
    for bid, ask in izip(bids, asks):
        yield bid and bid[0][0], ask and ask[0][0]

###########################################################
#
# Test Data Persistence

def generate_csv():
    with open('test.csv', 'wb') as f:
        writer = csv.writer(f)
        for t, side, order, size in orders(market(MARKET_OPEN)):
            if t > MARKET_OPEN + SIM_LENGTH:
                break
            writer.writerow([t, side, order, size])
      
def read_csv():
    with open('test.csv', 'rb') as f:
        for time, side, order, size in csv.reader(f):
            yield dateutil.parser.parse(time), side, float(order), int(size)

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

    while True:
        from time import sleep
        sleep(1)
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
        self._book     = dict()
        self._data     = order_book(read_csv(), self._book)
        self._rt_start = datetime.now()
        self._sim_start, _, _  = self._data.next()

    @route('/query/')
    def handle_query(self, x):
        sim_time = datetime.now() - self._rt_start
        print 'Query received @ t%s' % sim_time
        for t, bids, asks in self._data:
            if t > self._sim_start + sim_time:
                return list(top([bids], [asks]))[0]

    @route('/sell/')
    def handle_sell(self, x):
        sim_time = datetime.now() - self._rt_start
        print 'Sell received @ t%s for %s' % (sim_time, x)
        for t, bids, asks in self._data:
            if t > self._sim_start + sim_time:
                result = clear_order(float('inf'), float(x), self._book['buy'])
                if result:
                    self._book['buy'] = result[1]
                    return result[0]
                else:
                    return "Unfilled"

###########################################################
#
# Main

if __name__ == '__main__':  
    if not os.path.isfile('test.csv'):
        print "No data found, generating..."
        generate_csv()
    run(App())




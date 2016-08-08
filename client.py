################################################################################
#
#  Permission is hereby granted, free of charge, to any person obtaining a 
#  copy of this software and associated documentation files (the "Software"), 
#  to deal in the Software without restriction, including without limitation 
#  the rights to use, copy, modify, merge, publish, distribute, sublicense, 
#  and/or sell copies of the Software, and to permit persons to whom the 
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in 
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS 
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
#  DEALINGS IN THE SOFTWARE.

import urllib2
import time
import json
import random

# Server API URLs
QUERY = "http://localhost:8080/query?id={}"
ORDER = "http://localhost:8080/order?id={}&side=sell&qty={}&price={}"

# Strategy config.  We will attempt to liquidate a position of INVENTORY shares,
# by selling ORDER_SIZE @ top_bid - ORDER_DISCOUNT, once every N seconds.
ORDER_DISCOUNT = 10
ORDER_SIZE     = 200
INVENTORY      = 1000

N = 5

# Main
if __name__ == "__main__":

	# Start with all shares and no profit
	qty = INVENTORY
	pnl = 0

	# Repeat the strategy until we run out of shares.
	while qty > 0:

		# Query the price once every N seconds.
		for _ in xrange(N):
			time.sleep(1)
			quote = json.loads(urllib2.urlopen(QUERY.format(random.random())).read())
			price = float(quote['top_bid']['price'])
			print "Quoted at %s" % price

		# Attempt to execute a sell order.
		order_args = (ORDER_SIZE, price - ORDER_DISCOUNT)
		print "Executing 'sell' of {:,} @ {:,}".format(*order_args)
		url   = ORDER.format(random.random(), *order_args)
		order = json.loads(urllib2.urlopen(url).read())

		# Update the PnL if the order was filled.
		if order['avg_price'] > 0:
			price    = order['avg_price']
			notional = float(price * ORDER_SIZE)
			pnl += notional
			qty -= ORDER_SIZE
			print "Sold {:,} for ${:,}/share, ${:,} notional".format(ORDER_SIZE, price, notional)
			print "PnL ${:,}, Qty {:,}".format(pnl, qty)
		else:
			print "Unfilled order; $%s total, %s qty" % (pnl, qty)

		time.sleep(1)

	# Position is liquididated!
	print "Liquidated position for ${:,}".format(pnl)
		
import urllib2
import time

if __name__ == "__main__":

	qty = 1000
	pnl = 0
	while qty > 0:
		notional = urllib2.urlopen("http://localhost:8080/sell/100").read()
		try:
			pnl += float(notional)
			qty -= 100
			print "Sold 100 for $%s; $%s total, %s qty" % (notional, pnl, qty)
			time.sleep(5)
		except ValueError:
			print "Unfilled order; $%s total, %s qty" % (pnl, qty)
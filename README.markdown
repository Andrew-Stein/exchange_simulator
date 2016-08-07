Install
=======

	git clone https://github.com/texodus/exchange_simulator.git

Run
===
To start the server (this will create random market called 'test.csv' in your
working director if one does not already exist):

	python server.py

To start the example client:

	python client.py

API Examples
============
See also [client.py](https://github.com/texodus/exchange_simulator/blob/master/client.py)

Query:

	$ curl 'http://localhost:8080/query'
	{"top_ask": {"price": 129.18, "size": 70}, "timestamp": "2016-08-06 12:32:11.821574", "top_bid": {"price": 128.79, "size": 61}}

Filled order:

	$ curl 'http://localhost:8080/order?side=sell&qty=100&price=125.0'
	{"timestamp": "2016-08-06 12:32:20.860511", "qty": 100.0, "side": "sell", "avg_price": 129.5}

Unfilled order:

	$ curl 'http://localhost:8080/order?side=sell&qty=100&price=135.0'
	{"timestamp": "2016-08-06 12:32:24.990886", "qty": 0, "side": "sell", "avg_price": 0}
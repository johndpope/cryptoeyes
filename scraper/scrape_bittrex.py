import sys,os
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, dir_path+'/..')
from coinmarketcap import Market
from kafka import KafkaProducer
import json,datetime,time
import redis
from bittrex.bittrex import Bittrex, API_V2_0, API_V1_1, BUY_ORDERBOOK, TICKINTERVAL_ONEMIN, TICKINTERVAL_HOUR
import _thread

rose_host = os.environ['ROSE_HOST']
coinmarketcap = Market()
# coins = ['bitcoin','ethereum','bitcoin-cash','iota','ripple','dash','litecoin']
partition = datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d')
coins = coinmarketcap.ticker(limit=500)
TICKINTERVAL = {
    "HOUR":TICKINTERVAL_HOUR,
    "ONEMIN": TICKINTERVAL_ONEMIN
}
r = redis.StrictRedis(host='localhost', port=6379, db=0)
def scrape(chunk=1):
    producer = KafkaProducer(bootstrap_servers=rose_host)
    for coin in coins[(chunk-1)*10:chunk*10]:
        market = 'BTC-' + coin["symbol"]
        if coin["symbol"] == 'BTC':
            market = 'USDT-' + coin["symbol"]

        bittrex = Bittrex(os.environ['CRYPTOEYES_KEY'], os.environ['CRYPTOEYES_SEC'])
        bittrexv2 = Bittrex(os.environ['CRYPTOEYES_KEY'], os.environ['CRYPTOEYES_SEC'],api_version=API_V2_0)
        histories = bittrex.get_market_history(market)
        if histories.get("success") == True and histories.get("result") is not None:
            hist_lenght = len(histories["result"])-1
            topic = 'bittrex.' + market + '.history'
            print(topic)
            check_point = r.get(topic + '.check_point')
            for i in range(hist_lenght,-1,-1):
                hist = histories["result"][i]
                if check_point is None or hist["Id"] > int(check_point):
                    producer.send(topic + '.' + partition, json.dumps(hist).encode())
            r.set(topic+'.check_point',histories["result"][hist_lenght]["Id"])
        else: print(market,histories)
    print("there're " + str(len(coins)) + " of coins are tracking.")

# Create two threads as follows
try:
   for i in range(50):
       _thread.start_new_thread( scrape, (i, ) )
except:
   print("Error: unable to start thread")

time.sleep(120)
#
# print("--------Ticker\n", bittrex.get_ticker("BTC-LTC"))
# print("--------Sum\n", bittrex.get_marketsummary("BTC-LTC"))
# print("--------Order\n", bittrex.get_orderbook("BTC-LTC",depth_type=BUY_ORDERBOOK))
# print("--------History\n", bittrex.get_market_history("BTC-SIDA"))
# histories = bittrex.get_market_history("BTC-SIDA")
# topic = 'bittrex.' + 'BTC-LTC' + '.buy_order'# + partition
# check_point = r.get(topic+'.check_point')
# if histories.get("success") == True and len(histories.get("result",[])) > 0:
#     hist_lenght = len(histories["result"])-1
#     for i in range(hist_lenght,-1,-1):
#         hist = histories["result"][i]
#         # if check_point is None or hist["Id"] > check_point:
#         #     producer.send(topic, bytes(histories["result"][i]))
#         print(hist)
#         print(hist["Id"])
#         print(hist["Price"])
#         print(hist["Total"])
#         print(hist["OrderType"])
# r.set(topic+'.check_point',histories["result"][hist_lenght]["Id"])
# print "--------Candle\n", bittrexv2.get_candles("BTC-LTC",TICKINTERVAL_HOUR)
# print "--------Latest Candle\n", bittrexv2.get_latest_candle("BTC-LTC",TICKINTERVAL_HOUR)
# print ("--------My balances\n", bittrex.get_balances())

#  The goal of writing this script was to make automatic trades on the New York Stock Exchange.
#  It was meant to take advantage of higher than normal spreads, which I had thought might come about
#  with the stock market bottoming last March, but spreads did not increase past 1 penny, so the 
#  project was dropped, and is as yet unfinished.  I run it using Spyder3.8.



# This is modified eyllanesc/ToSimplicity using movetothread

#  Qwidget not threadsafe:  https://stackoverflow.com/questions/3842558/pyqt-and-threads
#  buy and sell buttons need to be able to act outside of thread also.
#  finish coding trade fcn.
#  Change minimum profit to a percent of invested amount. (.002 is 10/5000,.001667 is 10/6000)
#  Be sure to url-encode the values you pass.
#  Will LowReturnMessage or LossMessage ever prevent thread from being accessed? 
#  If snap buys/sells both get best price can I use smaller spreads? Does this only work in my favour if
#     others are buying/selling at market value (or some other instrument)?  Or avoid snap?
#  Make the error windows bigger so all text can be read?
#  Before Buy is placed (or at start), check that current trade volume supports proposed Buy and Threshold Value?
#  Add a get-current-price button to check that symbol is correct?
#  Low Return warning: do it within iters so if partial buy will give warning/stop loss due to fees? Disruptive?
#  If a buy only goes through partially, sell the purchased shares and stop iterating further?
#  What to do in case of partial sell?  Errors?
#  Partial buys and sells will end up increasing fees.
#  make it so changes to fields are accepted as input (is this automatic?  Do this with calc?)
#  Pause messages button/hotkey (unless messages are cheap enough)
#  In order to throw off spying on my periodic-natured buys, introduce pauses?
#  Keep track of threads used, print usage to LCD? Get better computer?
#  Get results/errors/progress for progress bar or print iter to LCD.
#  Do I need uninvested £ to pay for trades? More efficient: fee comes from invested £ pool or not?
#  Button to check how many iters current trade cycle can manage w/o running out of cash?
#  How do I combine iteration with threading?  
#  Reset current iter button?
#  What happens if I increase spread in the middle of a trade?
#  When do I need to calculate Initial#Shares and when do I need to accept input from DoubleSpinBox field?
#  Any tricks i can use to make other less sophisticated bots work for me?
#  What can machine learning do for me?

##  Done:
#  Threading is working.
#  Can pass params into running thread.
#  Set minimum spread or it could end up getting set to a negative number, big losses.
#  Do all widgets need to be in same fcn so that they can be included in threading?
#  Hot keys for up/dowm incrementing and spread?:  Not used: Alt 24=up arrow, alt 25=down arrow
#  set up remaining trading buttons as hot keys
#  Include Minimum Recommended Spread readout for given price and #shares?  Calc takes care of this.
#  Are fees tax deductible? probably  If not, profit margin will need to be recalculated.
#  Deductible taxes(?): fees, VAT, stamp duty https://www.gov.uk/tax-sell-shares/work-out-your-gain

#  Ekhumoro  https://stackoverflow.com/questions/29343755/pyqt5-python-3-passing-lists-dicts-as-signal-arguments-across-threads
# new threading loop https://stackoverflow.com/questions/29343755/pyqt5-python-3-passing-lists-dicts-as-signal-arguments-across-
# https://en.wikipedia.org/wiki/Lock_%28computer_science%29   # Lock or mutex
# also https://stackoverflow.com/questions/46306391/pass-args-to-pyqt-worker-thread-on-thread-start
# thorough ref:  https://stackoverflow.com/questions/39691479/qt-multithreading-data-pass-from-main-thread-to-worker-thread

#  US only broker: https://alpaca.markets/
#  pip3 install iexfinance    https://github.com/addisonlynch/
#  https://sandbox.iexapis.com       SSE:  https://sandbox-sse.iexapis.com
#  Test tokens look like Tpk_ and Tsk_.    https://iexcloud.io/docs/api/#sse-streaming   Data caching?
#  https://labs.ig.com/gettingstarted
#  https://www.smashingmagazine.com/2018/01/understanding-using-rest-api/
#  https://requests.readthedocs.io/en/master/user/quickstart/  # caching?
#  https://labs.ig.com/node/557  IG REST example

#eyllanesc https://stackoverflow.com/questions/41526832/pyqt5-qthread-signal-not-working-gui-freeze
# https://stackoverflow.com/questions/42994372/qthread-is-running-as-dummy-thread-even-after-the-thread-object-is-deleted
# https://stackoverflow.com/questions/62341967/how-to-send-multiple-complex-signals-to-the-same-thread-over-time


# List of hot keys:  
# Hashtag:   increment up
# Forward slash: increment down
# A:  increase spread
# Z:  decrease spread
# 2 or space bar: Cancel Buy
# 3: Cancel Sell
# 4: Pause (pause messages also, or with different button)
# 5: Panic Sell
# 6: Buy    Not set up yet  
# 7: Sell   Not set up yet
# 8: Shares Owned to Initial #Shares   Not set up yet
"""
@author: David Dickerson
"""

import sys
from PyQt5.QtCore import QThreadPool, QThread, QObject, pyqtSignal, pyqtSlot, QAbstractNativeEventFilter, QAbstractEventDispatcher#,Qt
from PyQt5.QtCore import * 
import time      
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, 
        QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLCDNumber, QLineEdit, QMessageBox, QPushButton,   
        QShortcut, QSpinBox, QStyleFactory, QTextEdit, QVBoxLayout, QWidget) 
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeySequence,QGuiApplication
from functools import partial
import logging
import logging.handlers
import os, base64, datetime, hashlib, hmac
import requests
import pandas
import json
from contextlib import suppress
from queue import Queue, Empty as EmptyQueue
from iexfinance.refdata import get_symbols
from iexfinance.stocks import Stock


# print('')
# print('*****')
# print('*****Before starting, update OS, Firewall, requests module, and antivirus software.*****')
# print('')
# print('*****Before starting, check that current trade volume supports your proposed Buy and Threshold Value.*****')
# print('*****')
# print('')


# The next few lines generate descriptions of working threads
threadpool = QThreadPool()
print("Multithreading with maximum %d threads" % threadpool.maxThreadCount()) # computer specific
# qthreadname=threading.current_thread().name
# print('Intro thread name: ',qthreadname) # name of thread the program starts on
thread_id = int(QThread.currentThreadId())
print('Intro thread ID: ',thread_id)

def trap_exc_during_debug(*args):
    print(args)  # when app raises uncaught exception, print info
sys.excepthook = trap_exc_during_debug # install exception hook: without this, uncaught exception would cause application to exit


# This class sets up the thread
class Worker(QObject):
    #print('begin ThreadClass')
    #sig_step = pyqtSignal(int, str)  # worker id, step description: emitted every step through work() loop
    #sig_start = pyqtSignal()
    sig_done = pyqtSignal(int)  # worker id: emitted at end of work()
    sig_msg = pyqtSignal(str)  # message to be shown to user
    signalStatus = pyqtSignal(str)
    sig_abort_workers = pyqtSignal()
    sig_reset_worker = pyqtSignal()
 
        
    def __init__(self):#, parent = None):
        QThread.__init__(self)#, parent)
        thread_id = int(QThread.currentThreadId())
        print('Worker __Init__ thread ID: ',thread_id)       
        
        self.pq = Queue()
       # self.pq2 = Queue()
        
        class Signals(QObject):
            senddata = pyqtSignal(list)
            sendcancbuy = pyqtSignal(int)
            sendcancsell = pyqtSignal(int)
            sendpause = pyqtSignal(int)
            sendpanic = pyqtSignal(int)
            sig_abort_workers = pyqtSignal(int)
            sig_reset_worker = pyqtSignal()
            #signalStatus = pyqtSignal(str)
            sendinctog = pyqtSignal(int)
            sendincup = pyqtSignal(list)
            sendincdown = pyqtSignal(list)
            sendreinvest = pyqtSignal(int)
            sendspreadup = pyqtSignal(list)
            sendspreaddown = pyqtSignal(list)
            shares2 = pyqtSignal(list)
            sendbuy = pyqtSignal(list)
            sendsell = pyqtSignal(list)
            
            
        self.signals = Signals()
        self.signals.senddata.connect(self.pq.put)
        self.signals.sendcancbuy.connect(self.pq.put)#cancelbuy2)#pq.put)#self.work)#cancelbuy2)
        self.signals.sendcancsell.connect(self.pq.put)#cancelsell2)#pq.put)#cancelsell2)
        self.signals.sendpause.connect(self.pq.put)#pause2)#pq.put)#pause2)
        self.signals.sendpanic.connect(self.pq.put)#panicsell2)#pq.put)#panicsell2)
        self.signals.sig_abort_workers.connect(self.pq.put)#abort)#pq.put)#work)#self.abort)#pq.put)#abort)
        #self.signals.sig_reset_worker.connect(self.reset)
        #self.signals.signalStatus.connect(self.updateStatus)
        self.signals.sendinctog.connect(self.pq.put)#IncTog2)
        self.signals.sendincup.connect(self.pq.put)#incrementup2)
        self.signals.sendincdown.connect(self.pq.put)#incrementdown2)
        self.signals.sendreinvest.connect(self.pq.put)#ReinvestTog2)
        self.signals.sendspreadup.connect(self.pq.put)#increasespread2)
        self.signals.sendspreaddown.connect(self.pq.put)#decreasespread2)
        self.signals.shares2.connect(self.pq.put)#shsh2)
        self.signals.sendbuy.connect(self.pq.put)
        self.signals.sendsell.connect(self.pq.put)
        
        
    @pyqtSlot()
    def work(self):  # This function is what will happen in the thread when it starts
        self.signalStatus.emit('Trading')
        app.processEvents()
        while True:
            try:
                params = self.pq.get()
                if type(params)==list:
                    leng=len(params)
                    if leng==16:
                        thread_id = int(QThread.currentThreadId())
                        print('work thread ID: ',thread_id)
                        print('params in work: ',params)
                        thread_id = int(QThread.currentThreadId())
                        print('work thread ID: ',thread_id)
                        self.symb=params[0]  # Symbol
                        self.exch=params[1]  # Exchange
                        print('Exchange: ',self.exch)
                        self.tran=params[2]  # Transaction Type
                        self.mark=params[3]  # Market
                        self.prod=params[4]  # Product Type
                        self.pswd=params[5]  # Password
                        self.buyp=params[6]   # buy price
                        self.selp=params[7]  # sell price
                        self.insh=params[8]  # Initial Number of Shares to Buy
                        self.cash=params[9]  # Total cash in account.  #Do I need this in thread?
                        self.shsh=params[10]  # Shares owned to Shares buying
                        self.titr=params[11]   # Total Iterations
                        self.incv=params[12]  # Increment Value, can be + or -
                        self.stra=params[13]  # Investment Strategy (linear vs exponential)
                        self.iniv=params[14]  # Initial Investment
                        self.thrs=params[15]  # Threshold Investment
                        
                        # if self.exch=='IEX':
                        #     HTTPS_PROXY='https://sandbox.iexapis.com'    #  Do this in GUI so thread is faster?
                        # elif self.exch=='IG':
                        #     HTTPS_PROXY='demo-api.ig.com/gateway/deal/session'
                        # elif self.exch=='212':
                        #     HTTPS_PROXY='https://212sandbox'
        
                    elif leng==2:
                        print('params in work: ',params)
                        if params[0]==1:
                            self.selp=params[1]
                            print('Spread increased in thread. New sell price: ',self.selp)
                            thread_id = int(QThread.currentThreadId())
                            print('work thread ID: ',thread_id)
                        elif params[0]==2:
                            self.selp=params[1]
                            print('Spread decreased in thread. New sell price: ',self.selp)
                        elif params[0]==3:
                            self.insh=params[1]
                            print('Shares to shares pressed. New number of shares to buy/sell: ',self.insh)
                            
                        elif params[0]==4:    # Inc up
                            # self.buyp=params[1]
                            # self.selp=params[2]
                            self.incv=params[1]
                            # print('Increment increased in thread. New buy price: ',self.buyp)
                            # print('Increment increased in thread. New sell price: ',self.selp)
                            print('Increment increased in thread. New incval: ',self.incv)
                        elif params[0]==5:    # Inc down
                            # self.buyp=params[1]
                            # self.selp=params[2]
                            self.incv=params[1]
                            # print('Increment decreased in thread. New buy price: ',self.buyp)
                            # print('Increment decreased in thread. New sell price: ',self.selp)
                            print('Increment decreased in thread. New incval: ',self.incv)

                    elif leng==10:
                        if params[0]==6:    # Buy
                            print('Buy signal in thread')
                            print('Buy params: ',params)
                            self.symb=params[1]
                            self.exch=params[2]
                            self.tran=params[3]
                            self.mark=params[4]
                            self.prod=params[5]
                            self.pswd=params[6]
                            self.buyp=params[7]
                            self.iniv=params[8]
                            self.insh=params[9]
                            # try:
                                # o = api.submit_order(
                                #     symbol=symbol, qty='100', side='buy',
                                #     type='limit', time_in_force='day',
                                #     limit_price=str(quote.ask)
                                # )
                                # # Approximate an IOC order by immediately cancelling?
                                # #api.cancel_order(o.id)
                                # position.update_pending_buy_shares(100) # Do I need something like this?
                                # position.orders_filled_amount[o.id] = 0 # I do need to update number shares owned.
                                # print('Buy at', quote.ask, flush=True)
                                # quote.traded = True
                            # except Exception as e:
                            #     print(e)

                            
                        elif params[0]==7:    #    Sell
                            print('Sell signal in thread')
                            print('Sell params: ',params)
                            self.symb=params[1]
                            self.exch=params[2]
                            self.tran=params[3]
                            self.mark=params[4]
                            self.prod=params[5]
                            self.pswd=params[6]
                            self.selp=params[7]
                            #self.iniv=params[8]
                            self.insh=params[8]
                            # try:
                            #     o = api.submit_order(
                            #         symbol=symbol, qty='100', side='sell',
                            #         type='market value', time_in_force='day',
                            #         limit_price=str(quote.bid)
                            #     )
                            #     # Approximate an IOC order by immediately cancelling
                            #     api.cancel_order(o.id)
                            #     position.update_pending_sell_shares(100)
                            #     position.orders_filled_amount[o.id] = 0
                            #     print('Sell at', quote.bid, flush=True)
                            #     quote.traded = True
                            # except Exception as e:
                            #     print(e)
                        
                elif type(params)==int:
                    if params==1:
                        thread_id = int(QThread.currentThreadId())
                        print('cancel buy in work. Thread ID: ',thread_id)
                        #get order id
                        #api.cancel_order(o.id)
                    elif params==2:
                        thread_id = int(QThread.currentThreadId())
                        print('cancel sell in thread.  Thread ID: ',thread_id)
                        #get order id
                        #api.cancel_order(o.id)
                    elif params==3:
                        thread_id = int(QThread.currentThreadId())
                        print('pause in thread.  Thread ID: ',thread_id)
                        # Not sure what to do here.
                    elif params==4:
                        thread_id = int(QThread.currentThreadId())
                        print('panic in thread.  Thread ID: ',thread_id)
                        # Sell all shares at market rate.
                        # try:
                        #     o = api.submit_order(
                        #         symbol=symbol, qty='100', side='sell',
                        #         type='market value', time_in_force='day',
                        #         limit_price=str(quote.bid)
                        #     )
                        #     position.update_pending_sell_shares(100)
                        #     position.orders_filled_amount[o.id] = 0
                        #     print('Sell at', quote.bid, flush=True)
                        #     quote.traded = True
                        # except Exception as e:
                        #     print(e)
        
                    elif params==5:
                        print('aborting thread...')
                        thread_id = int(QThread.currentThreadId())
                        print('Aborting... Thread ID: ',thread_id)
                    elif params==6:
                        print('inctog in thread')                        
                        #self.IncTog2()
                        thread_id = int(QThread.currentThreadId())
                        print('inctog in thread.  Thread ID: ',thread_id)
                        print('self.inc in work: ', self.inc)
                        print ('IncVal in work: ',self.IncVal)
                    elif params==7:
                        print('Reinvest Toggled  in thread!')
                        print('Reinvestment strategy is exponential')
                    elif params==8:
                        print('Reinvest Toggled  in thread!')
                        print('Reinvestment strategy is linear')

                #elif type(params)==float:
                    
                elif type(params)==str:
                    
                        print('working.....')
                
                
                #  https://addisonlynch.github.io/iexfinance/stable/configuration.html
                
                if self.exch=='IEX':
                    print('Contacting IEX')
                    HTTPS_PROXY=str('https://sandbox.iexapis.com')    #  Do this in GUI so thread is faster?
                IEX_SECRET_KEY=self.pswd
                IEX_PUBLIC_KEY=Tpk_5626b8c84ce94454b571867beb4d8d36 
                
                method = 'GET'
                host = HTTPS_PROXY # 'cloud.iexapis.com'
                
                access_key = IEX_PUBLIC_KEY #os.environ.get(IEX_PUBLIC_KEY)
                secret_key = IEX_SECRET_KEY #os.environ.get(IEX_SECRET_KEY)
                
                canonical_querystring = 'token=' + access_key
                canonical_uri = '/v1/stock/'+self.symb+'/company'
                endpoint = "https://" + host + canonical_uri
                
                if access_key is None or secret_key is None:
                    print('No access key is available.')
                    sys.exit()
                    
                def sign(key, msg):
                    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).hexdigest()
                
                def getSignatureKey(key, dateStamp):
                    kDate = sign(key, dateStamp)
                    return sign(kDate, 'iex_request')
                
                print('got to here')
                
                t = datetime.datetime.utcnow()
                iexdate = t.strftime('%Y%m%dT%H%M%SZ')
                datestamp = t.strftime('%Y%m%d') # Date w/o time, used in credential scope
                canonical_headers = 'host:' + host + '\n' + 'x-iex-date:' + iexdate + '\n'
                signed_headers = 'host;x-iex-date'
                payload_hash = hashlib.sha256(('').encode('utf-8')).hexdigest()
                canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
                algorithm = 'IEX-HMAC-SHA256'
                credential_scope = datestamp + '/' + 'iex_request'
                string_to_sign = algorithm + '\n' +  iexdate + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
                signing_key = getSignatureKey(secret_key, datestamp)
                signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()
                authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
                
                headers = {'x-iex-date':iexdate, 'Authorization':authorization_header}
                
                # ************* SEND THE REQUEST *************
                request_url = endpoint + '?' + canonical_querystring
                
                print('\nBEGIN REQUEST++++++++++++++++++++++++++++++++++++')
                print('Request URL = ' + request_url)
                r = requests.get(request_url, headers=headers)
                
                print('\nRESPONSE++++++++++++++++++++++++++++++++++++')
                print('Response code: %d\n' % r.status_code)
                print(r.text)
                
                
                
                a = Stock(self.symb, token=self.pswd)  # secret
                a.get_quote()
                print('quote for ',self.symb,':_',a)






            except (TypeError):   # TypeError?  Really?
                break  #  thread.quit?
        

    
            # Python Requests:  First, establish a connection:
            # r = requests.get('https://sandbox.iexapis.com')
            # r.json()   # encodes as json
            # r = requests.post('https://httpbin.org/post', data = {'key':'value'})
            # payload = {'key1': 'value1', 'key2': ['value2', 'value3']}
            # r = requests.get('https://httpbin.org/get', params=payload)
            # r = requests.get('https://api.github.com/events')   #Gets response
            # r = requests.get('https://api.github.com/events', stream=True) #gets raw socket response.
            # r.raw    # caching?  does this give binary readout??
            # with open(filename, 'wb') as fd:              # caching?
            # for chunk in r.iter_content(chunk_size=128):  # caching?
            #   fd.write(chunk)                             # caching?
    

            
    
            # r = requests.post('https://api.github.com/user', auth=('user', pswd))
            # r = requests.post(https://username:password@proxy.HTTPS_PROXY:pswd)#, data = {'key':'value'})
            # # http://username:password@proxy.IGsandbox.com:'password'
            # #r.json()
            # r = requests.head('Content-Type: application/json,Accept: application/json, charset=UTF-8,VERSION: 2',X-IG-API-KEY:)
            # # charset=UTF-8
            # # ?query1=value1&query2=value2
    
            # #  IG Requests:
            # # POST https://demo-api.ig.com/gateway/deal/session  #Action
            # # Content-Type: application/json; charset=UTF-8      #Header
            # # Accept: application/json; charset=UTF-8            #Header
            # # VERSION: 2                                         #Header
            # # X-IG-API-KEY:                                      #Header
            # {
            # "identifier": "cfddemokey1",
            # "password": "bbb604bc471be2b3325a38ddb02b9ec54b7e8ead"
            # }
            
            
            
            
            #for f in iter:  #  while CurrentIter<iter:
                # IncVal will be 0 if incrementing is off, no need for a loop here.
                #Buy+=IncVal
                #Sell+=IncVal
    
    
                    
                
            #tradeapi
            #symb=Symbol.upper
            # symbol = args.symbol
            # opts = {}
            # #if args.key_id:
            # opts['key_id'] = TransactionType
            # #if args.secret_key:
            # opts['secret_key'] = Password
            # #if args.base_url:
            # opts['base_url'] = Exchange
            # elif 'key_id' in opts and opts['key_id'].startswith('PK'):
            #     opts['base_url'] = 'https://paper-api.alpaca.markets'
            #https://sandbox.iexapis.com       
            #SSE:  https://sandbox-sse.iexapis.com
    
            
            
            # get variables together
            # Create an API object which can be used to submit orders, etc.
            # api = tradeapi.REST(**opts)
            # print(**opts)
            # Establish streaming connection
                # conn = tradeapi.StreamConn(**opts)
            # Define our message handling
                # @conn.on(r'Q$')
                # @conn.on(r'T$')
            # Check that # shares for sale is big enough? Skip this.
                #     if data.size >= 100: (or whatever.  Do a calcuation?)
            # Submit buy (at the ask?)
                # try:  (or while CurrentIter<Iter:)
                #     o = api.submit_order(
                #         symbol=symbol, qty='100', side='buy',
                #         type='limit', time_in_force='day',
                #         limit_price=str(quote.ask)
                #     )
                #     # Approximate an IOC order by immediately cancelling? Could result in loss due to fees.
                #     api.cancel_order(o.id)
                #     position.update_pending_buy_shares(100)
                #     position.orders_filled_amount[o.id] = 0
                #     print('Buy at', quote.ask, flush=True)
                #     quote.traded = True
                
                # Update Cash, SharesOwned, progress bar?
                
                # except Exception as e:
                #     print(e)        
                #     Bail?
    
    #  Check that the buy went through.  If it did, sell:
    
    
    
    #       submit sell (at the bid?):
                # try:  (or while CurrentIter<Iter:)
                #     o = api.submit_order(
                #         symbol=symbol, qty='100', side='sell',
                #         type='limit', time_in_force='day',
                #         limit_price=str(quote.bid)
                #     )
                #     # Approximate an IOC order by immediately cancelling
                #     api.cancel_order(o.id)
                #     position.update_pending_sell_shares(100)
                #     position.orders_filled_amount[o.id] = 0
                #     print('Sell at', quote.bid, flush=True)
                #     quote.traded = True
                
                # CurrentIter+=1
                # Update Cash, SharesOwned, progress bar, CurrentIter?
                
                
                # except Exception as e:
                #     print(e)
                #     Bail?
    
    
    
    
                
        # # Define our message handling
        # @conn.on(r'Q$')
            
        # def run(args):
        # symbol = args.symbol
        # max_shares = args.quantity
        # opts = {}
        # if args.key_id:
        #     opts['key_id'] = args.key_id
        # if args.secret_key:
        #     opts['secret_key'] = args.secret_key
        # if args.base_url:
        #     opts['base_url'] = args.base_url
        # elif 'key_id' in opts and opts['key_id'].startswith('PK'):
        #     opts['base_url'] = 'https://paper-api.alpaca.markets'
        # # Create an API object which can be used to submit orders, etc.
        # api = tradeapi.REST(**opts)
    
        # symbol = symbol.upper()
        # quote = Quote()
        # qc = 'Q.%s' % symbol
        # tc = 'T.%s' % symbol
        # position = Position()
    
        # # Establish streaming connection
        # conn = tradeapi.StreamConn(**opts)
    
        # # Define our message handling
        # @conn.on(r'Q$')
        # async def on_quote(conn, channel, data):
        #     # Quote update received
        #     quote.update(data)
    
        # @conn.on(r'T$')
        # async def on_trade(conn, channel, data):
        #     if quote.traded:
        #         return
        #     # We've received a trade and might be ready to follow it
        #     if (
        #         data.timestamp <= (
        #             quote.time + pd.Timedelta(np.timedelta64(50, 'ms'))
        #         )
        #     ):
        #         # The trade came too close to the quote update
        #         # and may have been for the previous level
        #         return
        #     if data.size >= 100:
        #         # The trade was large enough to follow, so we check to see if
        #         # we're ready to trade. We also check to see that the
        #         # bid vs ask quantities (order book imbalance) indicate
        #         # a movement in that direction. We also want to be sure that
        #         # we're not buying or selling more than we should.
        #         if (
        #             data.price == quote.ask
        #             and quote.bid_size > (quote.ask_size * 1.8)
        #             and (
        #                 position.total_shares + position.pending_buy_shares
        #             ) < max_shares - 100
        #         ):
        #             # Everything looks right, so we submit our buy at the ask
        #             try:
        #                 o = api.submit_order(
        #                     symbol=symbol, qty='100', side='buy',
        #                     type='limit', time_in_force='day',
        #                     limit_price=str(quote.ask)
        #                 )
        #                 # Approximate an IOC order by immediately cancelling
        #                 api.cancel_order(o.id)
        #                 position.update_pending_buy_shares(100)
        #                 position.orders_filled_amount[o.id] = 0
        #                 print('Buy at', quote.ask, flush=True)
        #                 quote.traded = True
        #             except Exception as e:
        #                 print(e)
        #         elif (
        #             data.price == quote.bid
        #             and quote.ask_size > (quote.bid_size * 1.8)
        #             and (
        #                 position.total_shares - position.pending_sell_shares
        #             ) >= 100
        #         ):
        #             # Everything looks right, so we submit our sell at the bid
        #             try:
        #                 o = api.submit_order(
        #                     symbol=symbol, qty='100', side='sell',
        #                     type='limit', time_in_force='day',
        #                     limit_price=str(quote.bid)
        #                 )
        #                 # Approximate an IOC order by immediately cancelling
        #                 api.cancel_order(o.id)
        #                 position.update_pending_sell_shares(100)
        #                 position.orders_filled_amount[o.id] = 0
        #                 print('Sell at', quote.bid, flush=True)
        #                 quote.traded = True
        #             except Exception as e:
        #                 print(e)
        
        # self.sig.connect(updateProgBar)
        

 

    @pyqtSlot()
    def abort(self):
        print('aborting....')
        # self.sig_msg.emit('thread message: Worker notified to abort')#.format(self.__id)) #bbb
        # self.__abort = True

    @pyqtSlot()
    def reset(self):
        self.sig_msg.emit('Worker notified to reset')#.format(self.__id)) # this does same as abort #bbb
        self.__reset = True


#This class creates the GUI, sets up the buttons, and checks that the entries make sense. Thread starter also.
class MyWidget(QWidget):
    #print('begin MyWidget!')
    signalStatus = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        #print('init in MyWidget!')
        
        self.originalPalette = QApplication.palette()
        styleComboBox = QComboBox()
        styleComboBox.addItems(QStyleFactory.keys())
        #self.createProgressBar()
        self.createTopLeftGroupBox()
        self.createTopRightGroupBox()
        self.createMiddleLeftGroupBox()
        self.createMiddleRightGroupBox()        
        self.createBottomLeftGroupBox()
        self.createBottomRightGroupBox()
        # self.createWayBottomLeftGroupBox()
        # self.createWayBottomRightGroupBox()
        
        topLayout = QHBoxLayout()
        topLayout.addStretch(1)
        mainLayout = QGridLayout()
        mainLayout.addLayout(topLayout, 0, 0, 1, 2)
        #mainLayout.addWidget(self.progressBar, 1, 0, 1, 2)       
        mainLayout.addWidget(self.topLeftGroupBox, 2, 0)
        mainLayout.addWidget(self.topRightGroupBox, 2, 1)
        mainLayout.addWidget(self.middleLeftGroupBox, 3, 0)
        mainLayout.addWidget(self.middleRightGroupBox, 3, 1)
        mainLayout.addWidget(self.bottomLeftGroupBox, 4, 0)
        mainLayout.addWidget(self.bottomRightGroupBox, 4, 1)
        # mainLayout.addWidget(self.wayBottomLeftGroupBox, 5, 0)
        # mainLayout.addWidget(self.wayBottomRightGroupBox, 5, 1)
        mainLayout.setRowStretch(1, 1)
        mainLayout.setRowStretch(2, 1)
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 1)
        self.setLayout(mainLayout)
        self.setWindowTitle("                         David's Mid-Frequency Trading GUI") 
        
        #self.progressBar.setValue(i)    # name

    def createTopLeftGroupBox(self):
        #print('topleft!')
        self.topLeftGroupBox = QGroupBox("Pricing")

        l1= QLabel("Symbol:")
        self.textEdit1 = QLineEdit('microsoft')
        #textEdit.resize(10,1)
        l2=QLabel("Exchange:")
        self.textEdit2 = QLineEdit('IEX')#'https://paper-api.alpaca.markets') #
# Can test SSE with https://sandbox-sse.iexapis.com  
# Test tokens look like Tpk_ and Tsk_
# 
        l3=QLabel("Transaction Type:")
        self.textEdit3 = QLineEdit('type')
        l4=QLabel("Market:")
        self.textEdit4 = QLineEdit('nyse')
        l5=QLabel("Product Type:")
        self.textEdit5 = QLineEdit('SNAP')         
        l6= QLabel("Password:")
        self.textEdit6 = QLineEdit('password')
        self.textEdit6.setEchoMode(QLineEdit.Password)
        l7= QLabel("Buy Price:")
        self.DoubleSpinBox1 = QDoubleSpinBox()
        self.DoubleSpinBox1.setMinimum(0)
        self.DoubleSpinBox1.setMaximum(999999999)        
        self.DoubleSpinBox1.setValue(1)    # set this to 0 when script is working.
        l8 = QLabel("Sell Price:")  
        self.DoubleSpinBox2 = QDoubleSpinBox()
        self.DoubleSpinBox2.setMinimum(0)
        self.DoubleSpinBox2.setMaximum(999999999)        
        self.DoubleSpinBox2.setValue(1.01)    # set this to 0 when script is working.
        l9= QLabel("Initial Invest:")
        self.DoubleSpinBox6 = QDoubleSpinBox()
        self.DoubleSpinBox6.setMinimum(0)
        self.DoubleSpinBox6.setMaximum(999999999)
        self.DoubleSpinBox6.setDecimals(2)
        self.DoubleSpinBox6.setValue(4000)# set this to 0 when script is working.
        
        l10= QLabel("Threshold Value:")
        self.DoubleSpinBox7 = QDoubleSpinBox()
        self.DoubleSpinBox7.setMinimum(0)
        self.DoubleSpinBox7.setMaximum(999999999)   
        self.DoubleSpinBox7.setDecimals(2)
        self.DoubleSpinBox7.setValue(5000)  # set this to 0 when script is working.
        
        l11 = QLabel("Initial # Shares:")
        self.DoubleSpinBox3 = QDoubleSpinBox()
        self.DoubleSpinBox3.setMinimum(0)
        self.DoubleSpinBox3.setMaximum(999999999)
        self.DoubleSpinBox3.setDecimals(6)
        #self.DoubleSpinBox3.setValue(0)
        l12 = QLabel("Iterations:")       
        self.spinBox1 = QSpinBox(self.topLeftGroupBox)
        self.spinBox1.setValue(5)     # set this to 0 when script is working.   
        self.defaultPushButton6 = QPushButton("Buy")
        self.defaultPushButton6.setDefault(False)
        self.defaultPushButton6.pressed.connect(self.buyfcn)       
        self.defaultPushButton7 = QPushButton("Sell")
        self.defaultPushButton7.setDefault(False)
        self.defaultPushButton7.pressed.connect(self.sellfcn)
        self.defaultPushButton13 = QPushButton("Calc # Shares")
        self.defaultPushButton13.setDefault(False)
        self.defaultPushButton13.pressed.connect(self.calcfcn)
        #l7 = QLabel("LCD test")
        self.lcdNumber1 = QLCDNumber(9)  

        layout = QGridLayout()
        layout.addWidget(l1,0,0,1,2)
        layout.addWidget(self.textEdit1,0,2,1,2)
        layout.addWidget(l2,1,0,1,2)
        layout.addWidget(self.textEdit2,1,2,1,2)
        layout.addWidget(l3,2,0,1,2)
        layout.addWidget(self.textEdit3,2,2,1,2)        
        layout.addWidget(l4,3,0,1,2)
        layout.addWidget(self.textEdit4,3,2,1,2)  
        layout.addWidget(l5,4,0,1,2)
        layout.addWidget(self.textEdit5,4,2,1,2)       
        
        layout.addWidget(l6,5,0,1,2)
        layout.addWidget(self.textEdit6,5,2,1,2)        
        layout.addWidget(l7, 6,0,1,2)
        layout.addWidget(self.DoubleSpinBox1, 6, 2, 1, 2)
        layout.addWidget(l8, 7,0,1,2)
        layout.addWidget(self.DoubleSpinBox2, 7, 2, 1, 2)
        layout.addWidget(l9, 8,0,1,2)
        layout.addWidget(self.DoubleSpinBox6, 8, 2, 1, 2)#("Initial £")        
        
        layout.addWidget(l10, 9,0,1,2)        
        layout.addWidget(self.DoubleSpinBox7, 9, 2, 1, 2)#("Threshold")
        
        layout.addWidget(l11, 10,0,1,2)
        layout.addWidget(self.DoubleSpinBox3, 10, 2, 1, 2)
        layout.addWidget(l12, 11,0,1,2)
        layout.addWidget(self.spinBox1, 11, 2, 1, 2)
        layout.addWidget(self.defaultPushButton6,12,1)
        layout.addWidget(self.defaultPushButton13,12,3)
        layout.addWidget(self.defaultPushButton7,13,1)
        #layout.addWidget(l7, 10,0,1,2)
        layout.addWidget(self.lcdNumber1,13,2,1,4)# 10, 2, 1, 2)
        layout.setRowStretch(5, 1)
        self.topLeftGroupBox.setLayout(layout)   

    def createTopRightGroupBox(self):
        #print('topright!')
        self.topRightGroupBox = QGroupBox("Trade")
        
        self.defaultPushButton1 = QPushButton("Execute Trade", self)  #  self?
        self.defaultPushButton1.setDefault(False)
        self.defaultPushButton1.pressed.connect(self.start_threads)

        self.defaultPushButton2 = QPushButton("Cancel Buy       space")
        self.defaultPushButton2.setDefault(False)     
        self.defaultPushButton2.pressed.connect(self.cancelbuyfcn)
        
        self.defaultPushButton3 = QPushButton("Cancel Sell           3")
        self.defaultPushButton3.setDefault(False)
        self.defaultPushButton3.pressed.connect(self.cancelsellfcn)
        
        self.defaultPushButton4 = QPushButton("Pause                 4")
        self.defaultPushButton4.setDefault(False)
        self.defaultPushButton4.pressed.connect(self.pausefcn)

        self.defaultPushButton5 = QPushButton("Panic Sell            5")
        self.defaultPushButton5.setDefault(False)   
        self.defaultPushButton5.pressed.connect(self.panicsellfcn)
        
        self.defaultPushButton8 = QPushButton("Increment Up      #")
        self.defaultPushButton8.setDefault(False)
        self.defaultPushButton8.pressed.connect(self.incrementupfcn)

        self.defaultPushButton9 = QPushButton("Increment Down   /")
        self.defaultPushButton9.setDefault(False)
        self.defaultPushButton9.pressed.connect(self.incrementdownfcn)
        
        self.defaultPushButton10 = QPushButton("Increase Spread   a")
        self.defaultPushButton10.setDefault(False)
        self.defaultPushButton10.pressed.connect(self.increasespreadfcn)
        
        self.defaultPushButton11 = QPushButton("Decrease Spread   z")
        self.defaultPushButton11.setDefault(False)
        self.defaultPushButton11.pressed.connect(self.decreasespreadfcn)
        
        self.defaultPushButton12 = QPushButton("Shares Owned to Init #Shares")
        self.defaultPushButton12.setDefault(False)
        self.defaultPushButton12.pressed.connect(self.sharestosharesfcn)

        self.label_status = QLabel('Status:', self)
        self.log = QTextEdit()

        layout = QVBoxLayout()
        layout.addWidget(self.defaultPushButton1)
        layout.addWidget(self.defaultPushButton2)
        layout.addWidget(self.defaultPushButton3)
        layout.addWidget(self.defaultPushButton4)
        layout.addWidget(self.defaultPushButton5)
        # layout.addWidget(self.defaultPushButton6)
        # layout.addWidget(self.defaultPushButton7)
        layout.addWidget(self.defaultPushButton8)        
        layout.addWidget(self.defaultPushButton9)
        layout.addWidget(self.defaultPushButton10)
        layout.addWidget(self.defaultPushButton11)
        layout.addWidget(self.defaultPushButton12)
        layout.addWidget(self.label_status)
        layout.addWidget(self.log)
        layout.addStretch(1)
        self.topRightGroupBox.setLayout(layout)
        
        
        self.cancbuy = QShortcut(QKeySequence(" "), self)   # Hotkeys
        self.cancbuy.activated.connect(self.cancelbuyfcn)
        self.cancsell = QShortcut(QKeySequence("3"), self)  # Hotkeys
        self.cancsell.activated.connect(self.cancelsellfcn)
        self.pause = QShortcut(QKeySequence("4"), self)
        self.pause.activated.connect(self.pausefcn)
        self.panic = QShortcut(QKeySequence("5"), self)
        self.panic.activated.connect(self.panicsellfcn)
        self.incup = QShortcut(QKeySequence("#"), self)
        self.incup.activated.connect(self.incrementupfcn)
        self.incdown = QShortcut(QKeySequence("/"), self)
        self.incdown.activated.connect(self.incrementdownfcn)
        self.spreadup = QShortcut(QKeySequence("a"), self)
        self.spreadup.activated.connect(self.increasespreadfcn)
        self.spreaddown = QShortcut(QKeySequence("z"), self)
        self.spreaddown.activated.connect(self.decreasespreadfcn)
        

    def createMiddleLeftGroupBox(self):
        #print('midleft!')
        self.middleLeftGroupBox = QGroupBox("Progress")
        l8= QLabel("Cash:")
        self.DoubleSpinBox4 = QDoubleSpinBox()
        self.DoubleSpinBox4.setMinimum(0)
        self.DoubleSpinBox4.setMaximum(999999999)        
        self.DoubleSpinBox4.setValue(0) 
        l9= QLabel("Current Iter:")
        spinBox2 = QSpinBox(self.middleLeftGroupBox)
        spinBox2.setValue(0)        
        layout = QGridLayout()
        layout.addWidget(l8,0,0,1,2)
        layout.addWidget(self.DoubleSpinBox4, 0, 2, 1, 2)
        layout.addWidget(l9,1,0,1,2)
        layout.addWidget(spinBox2, 1, 2, 1, 2)        
        #layout.addStretch(1)
        layout.setRowStretch(5, 1)
        self.middleLeftGroupBox.setLayout(layout)

    def createMiddleRightGroupBox(self):
        #print('midright!')
        self.middleRightGroupBox = QGroupBox("Progress")
        l10= QLabel("Shares Owned:")
        self.DoubleSpinBox5 = QDoubleSpinBox()
        self.DoubleSpinBox5.setMinimum(0)
        self.DoubleSpinBox5.setMaximum(999999999)        
        self.DoubleSpinBox5.setDecimals(6)
        self.DoubleSpinBox5.setValue(0) 
        self.defaultPushButton15 = QPushButton("Force Worker Reset")
        self.defaultPushButton15.setDefault(False)
        self.defaultPushButton15.pressed.connect(self.reset_worker) # need to make this fcn
        self.defaultPushButton15.setDisabled(True)
        #self.defaultPushButton15.pressed.connect(self.ForceWorkerReset)
        self.defaultPushButton14 = QPushButton("Force Worker Quit")
        self.defaultPushButton14.setDefault(False)
        self.defaultPushButton14.pressed.connect(self.abort_workers)
        self.defaultPushButton14.setDisabled(True)

        layout = QGridLayout()
        layout.addWidget(l10,0,0,1,2)
        layout.addWidget(self.DoubleSpinBox5, 0, 2, 1, 2)
        layout.addWidget(self.defaultPushButton15,1,1)
        layout.addWidget(self.defaultPushButton14,1,2)
        #layout.addStretch(1)
        layout.setRowStretch(5, 1)
        self.middleRightGroupBox.setLayout(layout)         

    def createBottomLeftGroupBox(self): 
        #print('botleft!')
        self.bottomLeftGroupBox = QGroupBox("Re-invest Earnings")
        self.bottomLeftGroupBox.setCheckable(True)
        self.bottomLeftGroupBox.setChecked(True)   
        self.bottomLeftGroupBox.toggled.connect(self.ReinvestTog)
        #self.progress = QTextEdit()
        layout = QVBoxLayout()
        #layout.addWidget(self.progress)
        layout.addStretch(1)
        self.bottomLeftGroupBox.setLayout(layout)  
        self.strategy=7

    def createBottomRightGroupBox(self):
        #print('botright!')
        self.bottomRightGroupBox = QGroupBox("Incrementing")
        self.bottomRightGroupBox.setCheckable(True)
        self.bottomRightGroupBox.setChecked(False)
        self.bottomRightGroupBox.toggled.connect(self.IncTog)
        l13= QLabel("Increment:")
        self.spinBox3 = QDoubleSpinBox(self.bottomRightGroupBox)      
        self.spinBox3.stepBy(.01)   # This generates an error but shouldn't.
        self.spinBox3.setMaximum(2)
        self.spinBox3.setMinimum(-2)
        self.spinBox3.setValue(0)
        #self.log = QTextEdit()
        layout = QGridLayout()
        layout.addWidget(l13, 0,0,1,2)
        layout.addWidget(self.spinBox3,0,2,1,2)
        #layout.addWidget(self.log,1,0,1,2)
        self.bottomRightGroupBox.setLayout(layout)   


    def cancelbuyfcn(self):
        #print('send cancel buy in GUI')
        self.worker.signals.sendcancbuy.emit(1)
        self.log.append('Buy Cancelled')
        self.cancelbuy=True
        self.defaultPushButton1.setEnabled(True)
        
    def cancelsellfcn(self):
        #self.sig_abort_workers.connect(Worker.abort)
        self.worker.signals.sendcancsell.emit(2)
        self.log.append('Sell Cancelled')
        self.defaultPushButton1.setEnabled(True)
        
    def pausefcn(self):
        self.worker.signals.sendpause.emit(3)
        self.log.append('Pause')
 
    def panicsellfcn(self):
        self.worker.signals.sendpanic.emit(4)
        self.log.append('Panic')
        self.defaultPushButton1.setEnabled(True)

    def buyfcn(self):
        # Check if thread is running.  If not, start it, send buy order.  If running, send buy order.
        self.symb=str(self.textEdit1.text())
        self.exch=str(self.textEdit2.text())
        self.tran=str(self.textEdit3.text())
        self.mark=str(self.textEdit4.text())
        self.prod=str(self.textEdit5.text())
        self.pswd=str(self.textEdit6.text())
        self.buyp=float(self.DoubleSpinBox1.value())
        self.iniv=float(self.DoubleSpinBox6.value())
        self.insh = float(self.iniv/self.buyp)
        self.params=[6,self.symb,self.exch,self.tran,self.mark,self.prod,self.pswd,self.buyp,self.iniv,self.insh]
        
        self.worker.signals.sendbuy.emit(self.params)
        self.log.append('Buy')
        #self.defaultPushButton1.setEnabled(True)

    def sellfcn(self):
        # Check if thread is running.  If not, start it, send buy order.  If running, send buy order.
        self.symb=str(self.textEdit1.text())
        self.exch=str(self.textEdit2.text())
        self.tran=str(self.textEdit3.text())
        self.mark=str(self.textEdit4.text())
        self.prod=str(self.textEdit5.text())
        self.pswd=str(self.textEdit6.text())
        self.selp=float(self.DoubleSpinBox2.value())
        #iniv=float(self.DoubleSpinBox6.value())
        self.insh = float(self.DoubleSpinBox3.value())   #  should be # shares owned
        self.params=[7,self.symb,self.exch,self.tran,self.mark,self.prod,self.pswd,self.selp,self.insh,0]
        self.worker.signals.sendsell.emit(self.params)
        self.log.append('Sell')
        #self.defaultPushButton1.setEnabled(True)
        
    def calcfcn(self):
        #print('calc')
        self.Buy=float(self.DoubleSpinBox1.value())
        self.InitialInvest = float(self.DoubleSpinBox6.value())
        self.InitShares = float(self.InitialInvest/self.Buy)
        self.DoubleSpinBox3.setValue(self.InitShares)
        self.low_return_warning()    #  is calc function connected properly to thread values?
        # need to send number shares to buy to thread.    worker.signals.
        
    def incrementupfcn(self):   # setValue for Buy and Sell here as they increment?  Do it in runner?
        self.params2()  #       How do I want to do this?  start after next buy?  Next sell?
        if self.inc==1:
            #print('inc up')  threading
            # self.Buy=float(self.DoubleSpinBox1.value())
            # self.Sell=float(self.DoubleSpinBox2.value())
            self.IncVal+=.01
            self.incval=round(self.IncVal,2)
            self.spinBox3.setValue(self.incval)
            params=[4,self.incval]#self.Buy, self.Sell, self.incval]
            self.worker.signals.sendincup.emit(params)
        elif self.inc==0:
            # self.Buy=float(self.DoubleSpinBox1.value())
            # self.Sell=float(self.DoubleSpinBox2.value())
            self.spinBox3.setValue(0)
            # Am I doing this right? should this be different than toggle signal?
            #self.incval=0#float(self.spinBox3.value())  # indexed correctly?
            params=[4,0]#self.incval]#self.Buy, self.Sell, self.incval]
            self.worker.signals.sendincup.emit(params)  # indexed correctly?

    def incrementdownfcn(self):
        self.params2()
        if self.inc==1:
            # self.Buy=float(self.DoubleSpinBox1.value())
            # self.Sell=float(self.DoubleSpinBox2.value())            
            self.IncVal-=.01
            self.incval=round(self.IncVal,2)
            self.spinBox3.setValue(self.incval)
            params=[5,self.incval]#self.Buy, self.Sell, self.incval]
            self.worker.signals.sendincdown.emit(params)
        elif self.inc==0:
            # self.Buy=float(self.DoubleSpinBox1.value())
            # self.Sell=float(self.DoubleSpinBox2.value())
            self.spinBox3.setValue(0) 
            # Am I doing this right? should this be different than toggle signal?
            #self.incval=0#float(self.spinBox3.value()) # indexed correctly?
            params=[5,0]#self.incval]#self.Buy, self.Sell, self.IncVal]
            self.worker.signals.sendincdown.emit(params)  # indexed correctly?

    def IncTog(self):
        self.params2()
        #self.spinBox3.setValue(0)
        self.inc=float(self.spinBox3.value())
        self.worker.signals.sendinctog.emit(self.inc)###
        print('Inc Toggled')

    def ReinvestTog(self):
        # self.spinBox3.setValue(0)
        # self.data7=float(self.spinBox3.value())
        if self.strategy==7:
            self.strategy=8
        else:
            self.strategy=7
        self.worker.signals.sendreinvest.emit(self.strategy)
        #self.data10=int(self.strategy)   
        #self.sendreinvest.emit(self.data10)

    #@pyqtSlot()
    def increasespreadfcn(self):
        self.Sell=float(self.DoubleSpinBox2.value())
        self.Buy=float(self.DoubleSpinBox1.value())
        self.Exchange=str(self.textEdit2.text())
        #print(self.Exchange)
        if self.Exchange=='IEX':
            fee=11.9
        elif self.Exchange=='IG':
            fee=6
        elif self.Exchange=='212':
            fee=0
        self.Sell+=.01
        self.InitShares = float(self.DoubleSpinBox3.value())
        spr=(((self.Sell-self.Buy)*self.InitShares)-fee)
        self.DoubleSpinBox2.setValue(self.Sell)
        # self.whack10=spr
        # self.lcdNumber1.display(self.whack10)
        self.data8=float(self.DoubleSpinBox2.value())
        self.params=[1,self.data8]
        self.worker.signals.sendspreadup.emit(self.params)

    #@pyqtSlot()
    def decreasespreadfcn(self):
        self.Sell=float(self.DoubleSpinBox2.value())
        self.Buy=float(self.DoubleSpinBox1.value())
        self.InitShares = float(self.DoubleSpinBox3.value())
        self.Exchange=str(self.textEdit2.text())
        #print(self.Exchange)
        if self.Exchange=='IEX':
            fee=11.9
        elif self.Exchange=='IG':
            fee=6
        elif self.Exchange=='212':
            fee=0
        spr=(((self.Sell-.01-self.Buy)*self.InitShares)-fee)
        if spr>=(10):# This doesnt work exactly as needed near threshold minimal profit spread. 
            self.Sell-=.01  # but it wont trade at a loss, just the profit at lowest level is wrong.
            self.DoubleSpinBox2.setValue(self.Sell)
        else:
            pass
        # self.whack11=spr
        # self.lcdNumber1.display(self.whack11)
        self.data9=float(self.DoubleSpinBox2.value())
        self.params=[1,self.data9]
        self.worker.signals.sendspreaddown.emit(self.params)

    def sharestosharesfcn(self):
        self.owned=float(self.DoubleSpinBox5.value())
        self.DoubleSpinBox3.setValue(self.owned)
        self.params=[3,self.owned]
        self.worker.signals.shares2.emit(self.params)
        # Need to introduce a new fcn here: calc if there will be loss at current buy/sell prices
        # Offer to Cancel or to adjust prices if necessary

    def params2(self):
        print('Params2!')
        if self.bottomRightGroupBox.isChecked(): # (Incrementing)
            print('inc=1 in Params2!')
            self.inc=1
            self.IncVal = float(self.spinBox3.value())
        else:
            print('inc=0 in Params2!')
            self.inc=0   
            self.spinBox3.setValue(0)

    @pyqtSlot(str)  
    def updateStatus(self, status):
        print('status updated at end of MyWidget')
        self.label_status.setText(status)


    def start_threads(self):

        self.defaultPushButton1.setDisabled(True)
        self.defaultPushButton15.setEnabled(True)
        self.defaultPushButton14.setEnabled(True)

        self.worker = Worker()
        worker=self.worker
        #self._connectSignals()
        self.worker.signalStatus.connect(self.updateStatus)
        #print('Get Params!')
        self.Symbol=(self.textEdit1.text())
        self.Exchange=str(self.textEdit2.text())#
        self.TransactionType=str(self.textEdit3.text())#
        self.Market=str(self.textEdit4.text())#
        self.ProductType=str(self.textEdit5.text())#
        self.Password=str(self.textEdit6.text())
        self.Buy=float(self.DoubleSpinBox1.value())
        self.Sell = float(self.DoubleSpinBox2.value()) 
        self.InitShares = float(self.DoubleSpinBox3.value()) #  need to calculate this separately sometimes
        self.Cash = float(self.DoubleSpinBox4.value())  # This needs to be reset to feedback from broker or something.  a calculation maybe.
        self.SharesOwned = float(self.DoubleSpinBox5.value())# This needs to be reset to feedback or calculation.
        self.Iter = int(self.spinBox1.value())   # Number of iterations in total at outset
        self.InitialInvest = float(self.DoubleSpinBox6.value())
        self.ThresholdInvest = float(self.DoubleSpinBox7.value())
        #self.inccheck()   #  Same as params2
        #print('inc: ',self.inc)# not working right
        if self.bottomRightGroupBox.toggled==True:  # (Incrementing)
            self.spinBox3.setValue(0)
        else:
            pass
        self.IncVal = int(self.spinBox3.value())
        strategy=7
        self.low_return_warning()
        #print('after low return warning finished') # round
        self.start=1
        if self.warning==1:   # Is this taken care of earlier?
            self.start=0
            self.wh='warn'
            self.lcdNumber1.display(self.wh)
        elif self.warning==0:
            self.start=1
        params=([self.Symbol,self.Exchange,self.TransactionType,self.Market,self.ProductType,self.Password,self.Buy,self.Sell,self.InitShares,self.Cash,self.SharesOwned,self.Iter,self.IncVal,self.strategy,self.InitialInvest,self.ThresholdInvest])
        self.worker.signals.senddata.emit(params)
        self.log.append('starting thread')
        self.__threads = []
        self.thread = QThread()
        self.thread.setObjectName('thread_1')
        thread=self.thread
        self.__threads.append((thread, worker))  # need to store worker too otherwise will be gc'd
        self.worker.moveToThread(self.thread)

        # get progress messages from worker:
        self.worker.sig_msg.connect(self.log.append)
        self.thread.started.connect(self.worker.work)
        self.thread.start()  # this will emit 'started' and start thread's event loop
         

    #def _connectSignals(self):
        #self.worker=Worker()
    #    worker.signalStatus.connect(self.updateStatus)


    def low_return_warning(self):#Buy, Sell, InitShares):
        #print('Start low_return_warning!')
        self.Buy=float(self.DoubleSpinBox1.value())
        self.Sell = float(self.DoubleSpinBox2.value()) 
        self.InitShares = float(self.DoubleSpinBox3.value())
        self.Exchange=str(self.textEdit2.text())
        if self.Exchange !='IEX' and self.Exchange !='IG' and self.Exchange !='212':
            print('Exchange not recognized')
            self.ParamError()
            self.warning=1
        elif self.Exchange=='IEX':
            fee=11.9
        elif self.Exchange=='IG':
            fee=6
        elif self.Exchange=='212':
            fee=0
        if (((self.Sell-self.Buy)*self.InitShares)-fee)<0:
            self.lossmessagewarning()
            self.warning=1
        elif round((((self.Sell-self.Buy)*self.InitShares)-fee),2)<10:
            self.lowmessagewarning()
            self.warning=1
        else:
            print(' ')
            print('Good profit margin')
            self.warning=0
            self.start=0
            xx=round((((self.Sell-self.Buy)*self.InitShares)-fee),2)
            print('Profit per trade cycle: ',xx)
            print('')
            #self.defaultPushButton1.setEnabled(True)
            #return self.start, self.warning  # necessary?

    def ParamError(self):
        self.warning=1
        self.start=0
        pmsg = QMessageBox()
        pmsg.setIcon(QMessageBox.Warning)
        pmsg.setWindowTitle("Warning!")
        pmsg.setText('Parameter Error Warning')
        pmsg.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
        pmsg.buttonClicked.connect(self.router)
        pmsg.exec_()
        #return self.start,self.warning        
            
    def lowmessagewarning(self):
        print('lowmessagewarning')
        self.warning=1
        self.start=0
        self.Exchange=str(self.textEdit2.text())
        if self.Exchange=='IEX':
            fee=11.9
        elif self.Exchange=='IG':
            fee=6
        elif self.Exchange=='212':
            fee=0
        # else:
        #     print('Exchange not recognized')
        #     self.ParamError()
        #     self.warning=1
        lowmsg = QMessageBox()
        lowmsg.setIcon(QMessageBox.Warning)
        lowmsg.setWindowTitle("Warning!")
        #lowmsg.setStyleSheet("QMessageBox{min-height: 1400px;}")
        lowmsg.setText('low Return Warning')
        self.signalStatus.emit('low Return Warning!!')
        xx=str(round(((self.Sell-self.Buy)*self.InitShares)-fee))
        #lowmsg.setInformativeText('Profit per trade cycle:')   # msg.setInformativeText
        lowmsg.setInformativeText(xx)
        #lowmsg.setInformativeText('')
        #lowmsg.setText('Cancel = Cancel Trade Cycle')
        #lowmsg.setText('Retry = Continue/Adjust Spread')
        lowmsg.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
        lowmsg.buttonClicked.connect(self.router)
        # if lowmsg.result() == QMessageBox.Retry
        lowmsg.exec_()
        #return self.start,self.warning #    Does returning mess up threading?
        
    def lossmessagewarning(self):
        self.warning=1
        self.start=0
        print('lossmessagewarning')
        lossmsg = QMessageBox()
        lossmsg.setWindowTitle("WARNING!!!")
        lossmsg.setIcon(QMessageBox.Critical)
        lossmsg.setText('LOSS Warning!')
        self.Exchange=str(self.textEdit2.text())
        if self.Exchange=='IEX':
            fee=11.9
        elif self.Exchange=='IG':
            fee=6
        elif self.Exchange=='212':
            fee=0
       # else:
            # print('Exchange not recognized')
            # self.ParamError()
            # self.warning=1
        #lossmsg.show()
        #print('loss Warning!!!')
        self.signalStatus.emit('Loss Warning!!!')
        xx=str(round(((self.Sell-self.Buy)*self.InitShares)-fee))
        #lossmsg.setInformativeText('Loss per trade cycle:')
        lossmsg.setInformativeText(xx)
        #cancel transaction or allow for price adjustment
        lossmsg.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
        lossmsg.buttonClicked.connect(self.router2)
        lossmsg.exec_()
        #return self.warning,self.start

    def router(self,i):  #  For low profit warning message
        if i.text()=='Retry':
            print('Retry clicked')
            ##self.exit_lowmsg()
        elif i.text()=='Cancel':
            print('Cancel clicked')
            #self.exit_lowmsg2()  

    def router2(self,i):  #  For profit loss warning message
        if i.text()=='Retry':
            print('Retry clicked')
            #self.exit_lossmsg()
        elif i.text()=='Cancel':
            print('Cancel clicked')
            #self.exit_lossmsg2()        
            
    @pyqtSlot(str)  
    def updateStatus(self, status):
        #print('status updated in start_threads')
        self.label_status.setText(status)
        

    @pyqtSlot()
    def abort_workers(self):
        self.params=(5)
        self.worker.sig_abort_workers.emit(self.params)  # Sends tuple, generates TypeError in thread, cancels.
        print('Asking worker to abort')
        #time.sleep(1)
        self.thread.quit() # this will quit **as soon as thread event loop unblocks**
        #self.thread.terminate()
        self.thread.wait()   
        print('worker aborted')
        self.log.append('Thread exited')

    @pyqtSlot()
    def reset_worker(self):
        print('reset does not work')
        # self.worker.sig_reset_worker.emit()
        # self.log.append('Asking worker to reset')
    #     thread.quit()  # this will quit **as soon as thread event loop unblocks**
    #     thread.wait()  # <- so you need to wait for it to *actually* quit
        # # even though threads have exited, there may still be messages on the main thread's
        # # queue (messages that threads emitted before the abort):   # threading
        # self.log.append('Thread reset')

# This class coordinates many of the above classes and functions.
if __name__ == "__main__":
    app = QApplication([])
    form = MyWidget()
    form.show()
    sys.exit(app.exec_())
from datetime import datetime
import pandas as pd
import yfinance as yf
import requests as rq


def get_table_html(df):
    
    """
    From https://stackoverflow.com/a/49687866/2007153
    
    Get a Jupyter like html of pandas dataframe
    
    """

    styles = [
        #table properties
        dict(selector=" ", 
             props=[("margin","0"),
                    ("font-family",'"Helvetica", "Arial", sans-serif'),
                    ("border-collapse", "collapse"),
                    ("border","none"),
    #                 ("border", "2px solid #ccf")
                       ]),

        #header color - optional
        dict(selector="thead", 
             props=[("background-color","#000")
                   ]),

        #background shading
        dict(selector="tbody tr:nth-child(even)",
             props=[("background-color", "#111")]),
        dict(selector="tbody tr:nth-child(odd)",
             props=[("background-color", "#333")]),

        #cell spacing
        dict(selector="td", 
             props=[("padding", ".5em")]),

        #header cell properties
        dict(selector="th", 
             props=[("font-size", "100%"),
                    ("text-align", "center")]),


    ]
    return (df.style.set_table_styles(styles)).render()

def convert_to_aud(price, currency):
    """Gvien the price in any other currency, convert to AUD.  Return List of new price """
    
    # get the price history between start and end date.
    BASE = 'AUD'
    converts = [None] * len(price)
    _price = price.index[0]
    start = f'{_price.year}-{_price.month:02d}-{_price.day:02d}'
    _price = price.index[-1]
    end = f'{_price.year}-{_price.month:02d}-{_price.day:02d}'
    del(_price)
    
#     print(start, end, currency, BASE)

    url = f'https://api.exchangerate.host/timeseries?start_date={start}1&end_date={end}&symbols={currency}&base={BASE}'
    
#     print(url)
    
    response = rq.get(url)
    data = response.json()
    
#     print(data)

    for ii, item in enumerate(data['rates']):
#         print(data['rates'])
#         print(data['rates'][item][currency])
        converts[ii] = data['rates'][item][currency] * price[ii]
    
    return converts

def generate_portfolio(trade_data, quotes):
    """Given Trade data, generate a daily portfolio"""
    END = datetime.now() #'2021-06-28' #  could use datetime.now
    _dates = []

    for date in trade_data['dates']:
        _dates.append(datetime.strptime(date, '%Y-%m-%d').date())


    date_range = pd.date_range(start=min(_dates), end=END, freq='D')

    df = None
    portfolio = date_range.to_frame()
    frames = [portfolio]

    for ii in range(len(trade_data['tickers'])):
        frames.append(quotes[ii]['Close'] * trade_data['amounts'][ii])

    df = pd.concat(frames, axis=1)
    df = df.drop(df.columns[0], axis=1)

    df.columns = trade_data['tickers']

    portfolio = df;

    portfolio.fillna(method='ffill', inplace=True)  ## forward fill.  so on weekends we carry forward Friday's value

    portfolio = portfolio.groupby(portfolio.columns, axis=1).sum() # merge duplicate columns wich represent multiple trades 

    portfolio['Total'] = portfolio.sum(axis=1)  # add to total as a column
    
    return portfolio

def get_quotes(trade_data):
    PERIOD = '1D' # Daily
    END = datetime.now() #'2021-06-28' #  could use datetime.now

    quotes = [] # empty list for storing quotes
    loop_end = len(trade_data)
    kk = 0
    for ticker, date in zip(trade_data['tickers'], trade_data['dates'] ):
        pct = kk / loop_end * 100
        _quote = yf.Ticker(ticker)
        quotes.append(_quote.history(period=PERIOD, start=date, end=END))
        print(f'Grabbing Ticker :: ${ticker} :: %{pct:.2f} complete              ', end='\r', flush=True)
        kk += 1
        
    return quotes
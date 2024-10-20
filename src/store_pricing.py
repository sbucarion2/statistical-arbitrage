import yfinance as yf
import sqlite3
# msft = yf.download("AAPL", start="2020-01-01", end="2021-01-01")

# print(msft)


def save_data_to_db():

    tickers = ["AAPL", "MSFT", "IBM", "HSIC"]

    with sqlite3.connect('test.db') as conn:

        cur = conn.cursor()

        for ticker in tickers:

            print(ticker)

            pricing_data = yf.download(ticker, start="2014-01-01", end="2024-10-11")

            for date, prices in pricing_data.iterrows():

                date_index = str(date).split()[0]

                prices_dict = {
                    "Open": float(prices.loc['Open']),
                    "High": float(prices.loc['High']),
                    "Low": float(prices.loc['Low']),
                    "Close": float(prices.loc['Adj Close']),
                    "Volume": int(prices.loc['Volume']),
                }

                # print(date_index,"\n", prices_dict)

                query_template = """INSERT INTO pricing(date,ticker,open,high,low,close,volume) VALUES(?,?,?,?,?,?,?)"""

                cur.execute(
                    query_template,  
                    [
                        date_index,
                        ticker, 
                        float(prices.loc['Open']),
                        float(prices.loc['High']),
                        float(prices.loc['Low']),
                        float(prices.loc['Adj Close']),
                        float(prices.loc['Volume']),
                    ]
                )

    cur.close()
    conn.close()

save_data_to_db()
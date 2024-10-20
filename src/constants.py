tickers = ["AAPL", "MSFT", "IBM", "HSIC"]

ALPHA = 0.05

STATIONARITY_TESTING_PERIOD = 756 # 3 years of pricing data (business days)
STATIONARITY_CUTOFF = 100 # will not include most recent 100 days in coint testing so we can leave for trading data

TRADE_DEVIATION_THRESHOLD = 1.5
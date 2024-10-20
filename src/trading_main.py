import numpy as np
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

from utils.db_utils.db_creation_utils import create_db
from utils.db_utils.db_query_utils import query_db
from constants import tickers, ALPHA, STATIONARITY_CUTOFF, TRADE_DEVIATION_THRESHOLD

# create_db("test")


def get_price_stream(db_response, price_type):

    price_stream = {}
    for date, data in db_response.items():

        price_stream[date] = data[price_type]

    return price_stream


def get_ticker_pricing(ticker, end_date):

    select_fields_str = ",".join(["date", "close"])

    # query = """SELECT {} FROM pricing WHERE ticker IN ('{}') AND date BETWEEN '2015-01-01' AND '2020-02-05';""".format(select_fields_str, ticker)

    query = """SELECT {} FROM pricing WHERE ticker IN ('{}') AND date <= '{}';""".format(select_fields_str, ticker, end_date)

    ticker_db_pricing = query_db(query, ["date", "close"], output_type="dict")

    return get_price_stream(ticker_db_pricing, 'close')


def normalize_list(lst):

    lst_mean = sum(lst) / len(lst)
    lst_std_dev = np.std(lst)

    normalized_lst = []
    for value in lst:

        normalized_lst.append(float((value - lst_mean) / lst_std_dev))

    return normalized_lst


def calculate_cointegration_spread(ticker1_pricing, ticker2_pricing):

    ticker1_pricing_values = list(ticker1_pricing.values())[:-STATIONARITY_CUTOFF] # Use 100 to leave the most recent 100 days for trading data
    ticker2_pricing_values = list(ticker2_pricing.values())[:-STATIONARITY_CUTOFF] # !00 days ago and further is meant for coint testing so we dont mix coint data with trading

    hedge_ratio = float(sm.OLS(ticker1_pricing_values, ticker2_pricing_values).fit().params[0])

    spread = []
    for ticker1_price_point, ticker2_price_point in zip(ticker1_pricing_values, ticker2_pricing_values):
        
        # print(ticker1_price_point, ticker2_price_point)

        spread.append((ticker2_price_point * hedge_ratio) - ticker1_price_point)

    # Normalize Spread
    normalized_spread = normalize_list(spread)

    print(normalized_spread)

    print("Spread", adfuller(spread)[1])
    print("Norm Spread", adfuller(normalized_spread)[1])

    return spread, hedge_ratio


def calculate_halflife(spread):
    """Regression on the pairs spread to find lookback
        period for trading"""
    
    x_lag = np.roll(spread,1)
    x_lag[0] = 0
    y_ret = spread - x_lag
    y_ret[0] = 0
    
    x_lag_constant = sm.add_constant(x_lag)
    
    res = sm.OLS(y_ret,x_lag_constant).fit()
    halflife = -np.log(2) / res.params[1]
    halflife = int(round(halflife))

    return halflife


def test_stationarity(ticker1, ticker2=None, end_date=None):

    ticker1_pricing = get_ticker_pricing(ticker1, end_date=end_date)

    ticker2_pricing = get_ticker_pricing(ticker2, end_date=end_date) if ticker2 is not None else None

    # print(ticker1_pricing)

    if ticker2 is not None:

        spread, hedge_ratio = calculate_cointegration_spread(ticker1_pricing, ticker2_pricing)

    else:

        ticker_pricing_values = list(ticker1_pricing.values())[:-STATIONARITY_CUTOFF]

        spread = normalize_list(ticker_pricing_values)

        hedge_ratio = 1

    adfuller_pvalue = adfuller(spread)[1]

    if adfuller_pvalue < ALPHA:

        # print(ticker1, ticker2, "STATIONARY", len(spread))

        halflife = calculate_halflife(spread)

        return True, halflife, hedge_ratio

    else:

        # print(ticker1, ticker2, "NON-STATIONARY", len(spread))

        return False, 1, 1

    return


def generate_trade_signal(ticker1, ticker2, halflife, hedge_ratio, end_date):

    ticker1_trading_pricing = list(get_ticker_pricing(ticker1, end_date=end_date).values())[-halflife:]
    ticker2_trading_pricing = list(get_ticker_pricing(ticker2, end_date=end_date).values())[-halflife:] if ticker2 is not None else None

    if ticker2 is not None:

        trading_spread = (ticker2_trading_pricing * hedge_ratio) - ticker1_trading_pricing

        trading_spread = normalize_list(trading_spread)
    
    else:

        trading_spread = normalize_list(ticker1_trading_pricing)

    if trading_spread[-2] < TRADE_DEVIATION_THRESHOLD and trading_spread[-1] > TRADE_DEVIATION_THRESHOLD:

        print("SHORT!", end_date, halflife)

        return {"DIRECTION": "SHORT", "HALFLIFE": halflife, "SHORT_TICKER": ticker1}

    if trading_spread[-2] > -TRADE_DEVIATION_THRESHOLD and trading_spread[-1] < -TRADE_DEVIATION_THRESHOLD:

        print("BUY! on ", end_date, halflife)

        return {"DIRECTION": "LONG", "HALFLIFE": halflife, "LONG_TICKER": ticker1}

    return
        

def run_strategy(today=None):

    ticker_pairs = [[ticker1, ticker2] for ticker1 in tickers for ticker2 in tickers if ticker1 != ticker2]

    # for ticker1, ticker2 in ticker_pairs:

    #     pairs_data = test_pairs_stationarity(ticker1, ticker2)

    #     print("Intercept", pairs_data["hedge_ratio"])

    #     # print("Spread", spread)

    #     break

    # today = "2024-10-05"
    for ticker in ["IBM"]: # tickers:

        is_stationary, halflife, hedge_ratio = test_stationarity(ticker, end_date=today)

        if is_stationary:

            trade_signal = generate_trade_signal(ticker, None, halflife, hedge_ratio, today)

            print(trade_signal)

    return


# GOAL: get closing prices of two securities 
# GOAL: Take closing prices and find beta from regression
# GOAL: Take p1 - (b*p2) and test for cointegration

# SELECT {} FROM pricing WHERE ticker IN ('{}') AND date BETWEEN '2015-01-01' AND '2020-02-05';
# Will give HSIC cointegrated and current nromalized spread is 1.6206 so we need to short
# Ok maybe not exactly 100% stationary but below are details
# HSIC Not Stationary pval - 0.06023599389008198
# HL - 57 Spread Std - 1.6206181479315767
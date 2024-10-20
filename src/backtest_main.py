from datetime import date, timedelta
from trading_main import run_strategy

def test_strategy():

    backtest_start_date = date(2024, 1, 1) # Year, Month, Day
    backtest_end_date = date(2024, 10, 10) # Year, Month, Day

    while backtest_start_date < backtest_end_date:

        print("Testing: ", backtest_start_date)

        run_strategy(backtest_start_date)

        backtest_start_date = backtest_start_date + timedelta(days=1)

test_strategy()

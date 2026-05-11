import streamlit as st
from ib_async import *
import nest_asyncio
import pandas as pd

# This is CRITICAL for Streamlit + IBKR in 2026
nest_asyncio.apply()


def get_ibkr_data(symbol):
    ib = IB()
    try:
        # Connect to TWS/Gateway (Port 7497 for Paper, 7496 for Live)
        ib.connect('127.0.0.1', 7497, clientId=1)

        # Define the Stock Contract
        contract = Stock(symbol, 'SMART', 'USD')
        ib.qualifyContracts(contract)

        # Request 5-minute bars for the current day
        bars = ib.reqHistoricalData(
            contract, endDateTime='', durationStr='1 D',
            barSizeSetting='5 mins', whatToShow='TRADES', useRTH=True
        )

        # Convert to Dataframe
        df = util.df(bars)
        if df is not None:
            df.set_index('date', inplace=True)
            # Rename columns to match our previous indicator logic
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount']
            return df
        return None
    except Exception as e:
        st.error(f"IBKR Connection Error: {e}")
        return None
    finally:
        ib.disconnect()
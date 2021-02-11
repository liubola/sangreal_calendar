from functools import lru_cache

import pandas as pd
from pandas.tseries.offsets import WeekOfMonth
from sangreal_calendar.core.refresh_rate_handle import Monthly
from sangreal_calendar.core.trade_dt_handle import (adjust_trade_dt,
                                                    step_trade_dt)


@lru_cache(maxsize=4)
def get_delistdate(date):
    """[获取交割日]
    """
    M = Monthly(1)
    delistdate = M.get('20150501', M.next(date, 1))
    delistdate = pd.to_datetime(delistdate).dt.date + \
        WeekOfMonth(1, week=2, weekday=4)
    delistdate = delistdate.map(
        lambda x: adjust_trade_dt(x, adjust='next'))
    if delistdate.iloc[-2] >= date:
        delistdate = delistdate.iloc[:-1].copy()
    return delistdate


@lru_cache(maxsize=4)
def get_contract(date):
    """[获取主力及次主力合约,仅针对股指期货]
    """
    M = Monthly(1)
    contract = []
    delisdate = get_delistdate(date).iloc[-1]
    c0 = delisdate[2:6]
    c1 = M.next(delisdate, 1)[2:6]
    if date == delisdate:
        contract.append(c1)
    elif date > step_trade_dt(delisdate, -4):
        contract.append(c0)
        contract.append(c1)
    else:
        contract.append(c0)
    return pd.Series(contract)

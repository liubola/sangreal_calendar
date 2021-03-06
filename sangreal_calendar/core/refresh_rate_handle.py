from abc import ABCMeta, abstractmethod
from functools import lru_cache

import pandas as pd
from sangreal_calendar.core.trade_dt_handle import (adjust_trade_dt,
                                                    get_trade_dts,
                                                    step_trade_dt)
from sangreal_calendar.utils import dt_handle


class RefreshBase(metaclass=ABCMeta):
    """获取调仓日期的基类

    Attributes: 
        *args: -1 or 1, int or (1, -1)
    """

    def __init__(self, *args):
        if abs(sum(args)) > 1:
            raise ValueError('args must be 1 or -1')
        self.args = sorted(args, reverse=True)

    @abstractmethod
    def get(self, begin_dt, end_dt):
        pass

    @lru_cache()
    def next(self, date, step=1, adjust=True):
        """[get next date, 20180921 -> 20180928(Monthly(-1))]

        Arguments:
            date {[str or datetime]} -- [date]
            adjust {[bool]} -- [if adjust & date is the key day, pass]
            step {[int]} -- [step numbers]

        Returns:
            [str] -- [next day in class frequency]
        """

        end_dt = step_trade_dt(date, 600)
        df = self.get(date, end_dt).tolist()
        try:
            if df[0] == date:
                if adjust:
                    return df[step]
            return df[step-1]
        except IndexError:
            return df[-1]

    @lru_cache()
    def prev(self, date, step=1, adjust=True):
        """[get previous day, 20180921 -> 20180831(Monthly(-1))]

        Arguments:
            date {[str or datetime]} -- [date]
            adjust {[bool]} -- [if adjust & date is the key day, pass]
            step {[int]} -- [step numbers]

        Returns:
            [str] -- [previous day in class frequency]
        """

        begin_dt = step_trade_dt(date, -600)
        df = self.get(begin_dt, date).tolist()
        try:
            if df[-1] == date:
                if adjust:
                    return df[-1-step]
            return df[-step]
        except IndexError:
            return df[0]

    @staticmethod
    def freq_handle(arg, df, step=1):
        if arg == 1:
            tmp_df = df.map(lambda x: adjust_trade_dt(x[:6] + '01', 'next'))
        else:
            tmp_df = df.map(lambda x: step_trade_dt(
                str(int(x[:6]) + step) + '01', -1))

        return tmp_df

    @staticmethod
    def df_handle(begin_dt='19900101', end_dt='20990101', func=None):
        begin_dt = dt_handle(begin_dt)
        end_dt = dt_handle(end_dt)
        df = get_trade_dts(begin_dt, end_dt).copy()

        df = df.map(func)
        df.drop_duplicates(inplace=True)
        return df

    def _get(self,
             begin_dt='19900101',
             end_dt='20990101',
             func=None,
             offset=None):
        begin_dt, end_dt = dt_handle(begin_dt), dt_handle(end_dt)
        df = get_trade_dts(
            step_trade_dt(begin_dt, -1 * offset),
            step_trade_dt(end_dt, offset)).to_frame('trade_dt')
        df['_trade_dt'] = pd.to_datetime(df['trade_dt'])
        df['month'] = df['_trade_dt'].map(func)
        all_trade_dt = pd.Series()
        for arg in self.args:
            if arg == 1:
                tmp_df = df.drop_duplicates('month', keep='first')['trade_dt']
            else:
                tmp_df = df.drop_duplicates('month', keep='last')['trade_dt']
            all_trade_dt = pd.concat([all_trade_dt, tmp_df])
        all_trade_dt.sort_values(inplace=True)
        all_trade_dt = all_trade_dt[
            (all_trade_dt >= begin_dt)
            & (all_trade_dt <= end_dt)].drop_duplicates()
        all_trade_dt.reset_index(drop=True, inplace=True)
        return all_trade_dt


class Daily(RefreshBase):
    def get(self, begin_dt='19900101', end_dt='20990101'):
        """[get trade_dt Series with class freq]

        Arguments:
            RefreshBase {[cls]} -- [refreshbase]

        Keyword Arguments:
            begin_dt {str or datetime} -- [begin_dt] (default: {'19900101'})
            end_dt {str or datetime} -- [end_dt] (default: {'20990101'})

        Returns:
            [pd.Series] -- [trade_dt Series]
        """

        return get_trade_dts(
            begin_dt,
            end_dt).copy()


class Monthly(RefreshBase):
    def get(self, begin_dt='19900101', end_dt='20990101'):
        """[get trade_dt Series with class freq]

        Arguments:
            RefreshBase {[cls]} -- [refreshbase]

        Keyword Arguments:
            begin_dt {str or datetime} -- [begin_dt] (default: {'19900101'})
            end_dt {str or datetime} -- [end_dt] (default: {'20990101'})

        Returns:
            [pd.Series] -- [trade_dt Series]
        """

        def func(x):
            return f"{x.year}{x.month}"

        return self._get(
            begin_dt=begin_dt, end_dt=end_dt, func=func, offset=40)


class Weekly(RefreshBase):
    def get(self, begin_dt='19900101', end_dt='20990101'):
        """[get trade_dt Series with class freq]

        Arguments:
            RefreshBase {[cls]} -- [refreshbase]

        Keyword Arguments:
            begin_dt {str or datetime} -- [begin_dt] (default: {'19900101'})
            end_dt {str or datetime} -- [end_dt] (default: {'20990101'})

        Returns:
            [pd.Series] -- [trade_dt Series]
        """

        def func(x):
            tmpx = x.isocalendar()
            return f"{tmpx[0]}{tmpx[1]}"

        return self._get(
            begin_dt=begin_dt, end_dt=end_dt, func=func, offset=20)


class BiWeekly(RefreshBase):
    def get(self, begin_dt='19900101', end_dt='20990101'):
        """[get trade_dt Series with class freq]

        Arguments:
            RefreshBase {[cls]} -- [refreshbase]

        Keyword Arguments:
            begin_dt {str or datetime} -- [begin_dt] (default: {'19900101'})
            end_dt {str or datetime} -- [end_dt] (default: {'20990101'})

        Returns:
            [pd.Series] -- [trade_dt Series]
        """

        all_trade_dt = pd.Series()
        for arg in self.args:
            if arg == 1:
                tmp_df = Weekly(1).get(begin_dt, end_dt)[::2]
            else:
                tmp_df = Weekly(-1).get(begin_dt, end_dt)[::2]
            all_trade_dt = pd.concat([all_trade_dt, tmp_df])
        all_trade_dt.sort_values(inplace=True)
        all_trade_dt.drop_duplicates(inplace=True)
        all_trade_dt.reset_index(drop=True, inplace=True)
        return all_trade_dt


class Quarterly(RefreshBase):
    def get(self, begin_dt='19900101', end_dt='20990101'):
        """[get trade_dt Series with class freq]

        Arguments:
            RefreshBase {[cls]} -- [refreshbase]

        Keyword Arguments:
            begin_dt {str or datetime} -- [begin_dt] (default: {'19900101'})
            end_dt {str or datetime} -- [end_dt] (default: {'20990101'})

        Returns:
            [pd.Series] -- [trade_dt Series]
        """

        def func(x):
            return f"{x.year}{x.quarter}"

        return self._get(
            begin_dt=begin_dt, end_dt=end_dt, func=func, offset=120)


class Reportly(RefreshBase):
    @staticmethod
    def _report(x):
        if x <= x[:4] + '0430':
            return str(int(x[:4]) - 1) + '11'
        elif x <= x[:4] + '0831':
            return x[:4] + '05'
        elif x <= x[:4] + '1031':
            return x[:4] + '09'
        elif x <= x[:4] + '1231':
            return x[:4] + '11'

    def get(self, begin_dt='19900101', end_dt='20990101'):
        """[get trade_dt Series with class freq]

        Arguments:
            RefreshBase {[cls]} -- [refreshbase]

        Keyword Arguments:
            begin_dt {str or datetime} -- [begin_dt] (default: {'19900101'})
            end_dt {str or datetime} -- [end_dt] (default: {'20990101'})

        Returns:
            [pd.Series] -- [trade_dt Series]
        """

        begin_dt, end_dt = dt_handle(begin_dt), dt_handle(end_dt)
        df = self.df_handle(begin_dt, end_dt, self._report)
        all_trade_dt = pd.Series()
        for arg in self.args:
            if arg == 1:
                tmp_df = df.map(
                    lambda x: adjust_trade_dt(x[:6] + '01', 'next'))
            else:
                def neg_report(x):
                    if x[-2:] == '11':
                        return step_trade_dt(str(int(x[:4]) + 1) + '0501', -1)
                    elif x[-2:] == '09':
                        return step_trade_dt(x[:4] + '1101', -1)
                    elif x[-2:] == '05':
                        return step_trade_dt(x[:4] + '0901', -1)

                tmp_df = df.map(neg_report)
            all_trade_dt = pd.concat([all_trade_dt, tmp_df])
        all_trade_dt.sort_values(inplace=True)
        all_trade_dt = all_trade_dt[(all_trade_dt >= begin_dt)
                                    & (all_trade_dt <= end_dt)].copy()
        all_trade_dt.reset_index(drop=True, inplace=True)
        return


class Yearly(RefreshBase):
    def get(self, begin_dt='19900101', end_dt='20990101'):
        """[get trade_dt Series with class freq]

        Arguments:
            RefreshBase {[cls]} -- [refreshbase]

        Keyword Arguments:
            begin_dt {str or datetime} -- [begin_dt] (default: {'19900101'})
            end_dt {str or datetime} -- [end_dt] (default: {'20990101'})

        Returns:
            [pd.Series] -- [trade_dt Series]
        """

        def func(x):
            return f"{x.year}"

        return self._get(
            begin_dt=begin_dt, end_dt=end_dt, func=func, offset=300)


class Halfyearly(RefreshBase):
    @staticmethod
    def _year(x):
        if x <= x[:4] + '0630':
            return x[:4] + '01'
        elif x <= x[:4] + '1231':
            return x[:4] + '07'

    def get(self, begin_dt='19900101', end_dt='20990101'):
        """[get trade_dt Series with class freq]

        Arguments:
            RefreshBase {[cls]} -- [refreshbase]

        Keyword Arguments:
            begin_dt {str or datetime} -- [begin_dt] (default: {'19900101'})
            end_dt {str or datetime} -- [end_dt] (default: {'20990101'})

        Returns:
            [pd.Series] -- [trade_dt Series]
        """

        begin_dt, end_dt = dt_handle(begin_dt), dt_handle(end_dt)
        df = self.df_handle(begin_dt, end_dt, self._year)
        all_trade_dt = pd.Series()
        for arg in self.args:
            tmp_df = self.freq_handle(arg, df, 6)
            all_trade_dt = pd.concat([all_trade_dt, tmp_df])
        all_trade_dt.sort_values(inplace=True)
        all_trade_dt = all_trade_dt[(all_trade_dt >= begin_dt)
                                    & (all_trade_dt <= end_dt)].copy()
        all_trade_dt.reset_index(drop=True, inplace=True)
        return all_trade_dt


if __name__ == '__main__':
    pass
import os
import abc
import pandas as pd
import numpy as np


class DataFile(object):

    def __init__(self, fname, nodata_value=-999):
        self.__filename = fname
        self.__nodata_value = nodata_value
        self.__variables = {}
        self.__data = self._read()

    @property
    def data(self):
        return self.__data

    @property
    def variables(self):
        return self.__variables

    def _read(self):
        with open(self.__filename, 'r') as f:
            f.readline()  # header
            while True:
                line = f.readline()
                if line.startswith('//'):
                    continue
                elif '####' in line:
                    break
                else:
                    items = line.split()
                    var, nval = items[0], int(items[1])
                    self.__variables[var] = nval
            nstn = sum(list(self.__variables.values()))
            dt_cols = ['year', 'month', 'day', 'hours', 'minutes', 'seconds']
            stn_cols = [n + 1 for n in range(nstn)]
            columns = dt_cols + stn_cols
            df = pd.read_csv(f, skiprows=0, delim_whitespace=True,
                             header=None, names=columns)
        df.index = pd.DatetimeIndex(pd.to_datetime(df[dt_cols]))
        df = df[stn_cols]

        if self.__nodata_value is not None:
            df = df.replace(self.__nodata_value, np.nan)

        data = {}
        i = 0
        for var, nval in self.__variables.items():
            var_cols = [n + 1 for n in list(range(i, i + nval))]
            data[var] = df[var_cols]
            data[var].columns = [n + 1 for n in range(nval)]
            i += nval
        return data
#
#
# class DataFile(object):
#
#     @abc.abstractmethod
#     def _read(self):
#         raise NotImplementedError(
#             'must define _read in child '
#             'class to use this base class')
#
#     @property
#     def data(self):
#         raise NotImplementedError(
#             'must define _read in child '
#             'class to use this base class')
#
#
# class StnDataFile(DataFile):
#
#     def __init__(self, fname, nodata_value=-999):
#         self.__filename = fname
#         self.__nodata_value = nodata_value
#         self.__variables = {}
#         self.__data = self._read()
#
#     @property
#     def data(self):
#         return self.__data
#
#     @property
#     def variables(self):
#         return self.__variables
#
#     def _read(self):
#         with open(self.__filename, 'r') as f:
#             f.readline()  # header
#             while True:
#                 line = f.readline()
#                 if line.startswith('//'):
#                     continue
#                 elif '####' in line:
#                     break
#                 else:
#                     items = line.split()
#                     var, nval = items[0], int(items[1])
#                     self.__variables[var] = nval
#             nstn = sum(list(self.__variables.values()))
#             dt_cols = ['year', 'month', 'day', 'hours', 'minutes', 'seconds']
#             stn_cols = [n + 1 for n in range(nstn)]
#             columns = dt_cols + stn_cols
#             df = pd.read_csv(f, skiprows=0, delim_whitespace=True,
#                              header=None, names=columns)
#         df.index = pd.DatetimeIndex(pd.to_datetime(df[dt_cols]))
#         df = df[stn_cols]
#
#         if self.__nodata_value is not None:
#             df = df.replace(self.__nodata_value, np.nan)
#
#         data = {}
#         i = 0
#         for var, nval in self.__variables.items():
#             var_cols = [n + 1 for n in list(range(i, i + nval))]
#             data[var] = df[var_cols]
#             data[var].columns = [n + 1 for n in range(nval)]
#             i += nval
#         return data
#
#
# class CbhDataFile(DataFile):
#
#     def __init__(self, fname, nodata_value=-999):
#         self.__filename = fname
#         self.__nodata_value = nodata_value
#         self.__varname = None
#         self.__data = self._read()
#
#     @property
#     def varname(self):
#         return self.__varname
#
#     @property
#     def data(self):
#         ignore = ['year', 'month', 'day',
#                   'hours', 'minutes', 'seconds']
#         cols = [c for c in self.__data.columns if c not in ignore]
#         return self.__data[cols]
#
#     def _read(self):
#         # Assume only 1 parameter per file
#         with open(self.__filename, 'r') as f:
#             f.readline().strip()  # header
#             while True:
#                 line = f.readline()
#                 if line.startswith('//'):
#                     continue
#                 elif '####' in line:
#                     break
#                 else:
#                     items = line.split()
#                     self.__varname = items[0]
#                     nhru = int(items[1])
#             dt_cols = ['year', 'month', 'day', 'hours', 'minutes', 'seconds']
#             hru_cols = [n + 1 for n in range(nhru)]
#             columns = dt_cols + hru_cols
#             data = pd.read_csv(f, skiprows=0, delim_whitespace=True,
#                                names=columns, header=None)
#             data.index = pd.DatetimeIndex(pd.to_datetime(data[dt_cols]))
#             if self.__nodata_value is not None:
#                 data = data.replace(self.__nodata_value, np.nan)
#         return data


# def write_cbh_data_file(f_out, df, varname, header=None, nodata_value=-9999,
#                      fmt='%.2f'):
#     if header is None:
#         curfile = os.path.basename(__file__)
#         header = f'Created by {curfile}'
#     else:
#         # header length <= 256 char
#         header = header[:255]
#     ncol = len(df.columns.tolist())
#     _df = df.copy()
#     _df = _df.replace(np.nan, nodata_value)
#     _df.insert(0, 'seconds', _df.index.second)
#     _df.insert(0, 'minutes', _df.index.minute)
#     _df.insert(0, 'hours', _df.index.hour)
#     _df.insert(0, 'day', _df.index.day)
#     _df.insert(0, 'month', _df.index.month)
#     _df.insert(0, 'year', _df.index.year)
#
#     with open(f_out, 'w') as f:
#         f.write(header + '\n')
#         f.write(f'{varname} {ncol}' + '\n')
#         f.write('####' + '\n')
#         _df.to_csv(f, sep='\t', index=False, float_format=fmt, header=None, line_terminator='\n')
#     return

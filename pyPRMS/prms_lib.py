#!/usr/bin/env python

from __future__ import (absolute_import, division,
                        print_function)
# , unicode_literals)
# from future.utils import iteritems

# from builtins import (
#     bytes, dict, int, list, object, range, str,
#     ascii, chr, hex, input, next, oct, open,
#     pow, round, super,
#     filter, map, zip)

# import past
# import six
#
# from functools import reduce
# import calendar
# import glob
import re
# import numpy as np
import pandas as pd
import datetime
# import os
# import sys

# Author: Parker Norton (pnorton@usgs.gov)
# Create date: 2015-02-09
# Description: Set of classes for processing PRMS data files. The datafiles
#              that are currently handled are:
#                  streamflow - processes the streamflow data
#                  param - processes the input parameter file
#                  statvar - processes the output statvar file
#                  control - processes the control file

# Although this software program has been used by the U.S. Geological Survey (USGS),
# no warranty, expressed or implied, is made by the USGS or the U.S. Government as
# to the accuracy and functioning of the program and related program material nor
# shall the fact of distribution constitute any such warranty, and no
# responsibility is assumed by the USGS in connection therewith.

__version__ = '0.5'


# def dparse(*dstr):
#     dint = [int(x) for x in dstr]
#
#     if len(dint) == 2:
#         # For months we want the last day of each month
#         dint.append(calendar.monthrange(*dint)[1])
#     if len(dint) == 1:
#         # For annual we want the last day of the year
#         dint.append(12)
#         dint.append(calendar.monthrange(*dint)[1])
#
#     return datetime.datetime(*dint)
#
# # def dparse(yr, mo, dy, hr, minute, sec):
# #     # Date parser for working with the date format from PRMS files
# #
# #     # Convert to integer first
# #     yr, mo, dy, hr, minute, sec = [int(x) for x in [yr, mo, dy, hr, minute, sec]]
# #
# #     dt = datetime.datetime(yr, mo, dy, hr, minute, sec)
# #     return dt


def create_default_range_file(in_filename, out_filename):
    """Get the default parameter ranges from a file which is the result of running
       'prms -print'"""

    # Create parameter default ranges file from from PRMS -print results
    try:
        infile = open(in_filename, 'r')
    except IOError as err:
        print("Unable to open file\n", err)
        return False
    else:
        rawdata = infile.read().splitlines()
        infile.close()

        it = iter(rawdata)

        for line in it:
            if line == '--------------- PARAMETERS ---------------':
                break
        param_dict = {}

        for line in it:
            flds = line.split(':')

            if len(flds) < 2:
                continue

            key = flds[0].strip()
            val = flds[1].strip()

            if key == 'Name':
                cparam = val
                param_dict[cparam] = {}
            else:
                param_dict[cparam][key] = val

        try:
            outfile = open(out_filename, 'w')
        except IOError as err:
            print("Unable to write file\n", err)
            return False
        else:
            outfile.write('parameter max min\n')

            for (kk, vv) in iter(param_dict.items()):
                outfile.write('%s %f %f\n' % (kk, float(vv['Max']), float(vv['Min'])))

            outfile.close()
        return True


def to_datetime(date_str):
    """Takes a date string of the form 'YYYY-MM-DD HH:mm:ss' (and variations thereof)
       and converts it to a datetime"""
    return datetime.datetime(*[int(x) for x in re.split('-| |:', date_str)])


def to_prms_datetime(date):
    """Takes a datetime object and converts it to a string of form
       YYYY,MM,DD,HH,mm,ss"""
    return date.strftime('%Y,%m,%d,%H,%M,%S')


def read_cbh(filename, sep=' ', missing_val=[-99.0, -999.0]):
    """Read a CBH file"""

    if not isinstance(missing_val, list):
        missing_val = [missing_val]

    infile = open(filename, 'r')
    fheader = ''

    for ii in range(0, 3):
        line = infile.readline()

        if line[0:4] in ['prcp', 'tmax', 'tmin']:
            # Change the number of HRUs included to one
            # numhru = int(line[5:])
            fheader += line[0:5] + ' 1\n'
        else:
            fheader += line

    df1 = pd.read_csv(infile, sep=sep, na_values=missing_val, skipinitialspace=True, header=None,
                      date_parser=dparse, parse_dates={'thedate': [0, 1, 2, 3, 4, 5]}, index_col='thedate')
    infile.close()

    # Renumber/rename columns to reflect HRU number
    df1.rename(columns=lambda x: df1.columns.get_loc(x) + 1, inplace=True)
    return df1


def read_gdp(filename, missing_val=[255.]):
    """Read files that were created from Geodata Portal jobs"""

    # TODO: Extend this function to handle the metadata on lines 0 and 2

    if not isinstance(missing_val, list):
        missing_val = [missing_val]

    gdp_data = pd.read_csv(filename, na_values=missing_val, header=0, skiprows=[0, 2])

    gdp_data.rename(columns={gdp_data.columns[0]: 'thedate'}, inplace=True)
    gdp_data['thedate'] = pd.to_datetime(gdp_data['thedate'])
    gdp_data.set_index('thedate', inplace=True)
    return gdp_data

# def write_params_by_module(param_dict, filename):
#     """Write an input parameter db dictionary generated by build_input_param_db() to a .csv file"""
#     params_by_module = {}
#
#     for kk, vv in iter(param_dict.items()):
#         if isinstance(vv['Module'], list):
#             for mm in vv['Module']:
#                 if mm not in params_by_module:
#                     # Add new module entry
#                     params_by_module[mm] = []
#                 params_by_module[mm].append(kk)
#         else:
#             if vv['Module'] not in params_by_module:
#                 params_by_module[vv['Module']] = []
#             params_by_module[vv['Module']].append(kk)
#
#     outfile = open(filename, 'w')
#
#     # Write out parameters by module to file
#     for kk, vv in iter(params_by_module.items()):
#         vv.sort()
#         outfile.write('%s,' % kk)
#
#         oo = ','.join(vv)
#         outfile.write('%s\n' % oo)
#     outfile.close()


# # Order to write control file parameters for printing and writing a new control file
# ctl_order = ['start_time', 'end_time', 'executable_desc', 'executable_model', 'model_mode', 'param_file', 'data_file',
#              'model_output_file', 'parameter_check_flag', 'print_debug', 'et_module', 'precip_module',
#              'soilzone_module',
#              'solrad_module',
#              'srunoff_module', 'strmflow_module', 'temp_module', 'transp_module', 'prms_warmup', 'init_vars_from_file',
#              'save_vars_to_file', 'var_init_file', 'var_save_file', 'cbh_binary_flag', 'cbh_check_flag',
#              'gwflow_cbh_flag', 'orad_flag', 'snow_cbh_flag', 'humidity_day', 'potet_day', 'precip_day', 'precip_grid',
#              'swrad_day', 'tmax_day', 'tmax_grid', 'tmin_day', 'tmin_grid', 'transp_day', 'windspeed_day', 'csvON_OFF',
#              'csv_output_file', 'nhruOutON_OFF', 'nhruOutBaseFileName', 'nhruOutVars', 'nhruOutVar_names',
#              'nhruOut_freq', 'mapOutON_OFF', 'nmapOutVars', 'mapOutVar_names', 'statsON_OFF', 'stat_var_file',
#              'nstatVars', 'statVar_element', 'statVar_names', 'aniOutON_OFF', 'ani_output_file', 'naniOutVars',
#              'aniOutVar_names', 'dispGraphsBuffSize', 'ndispGraphs', 'dispVar_element', 'dispVar_names',
#              'dispVar_plot', 'initial_deltat', 'cascade_flag', 'cascadegw_flag', 'dprst_flag', 'dyn_covden_flag',
#              'dyn_covtype_flag', 'dyn_dprst_flag', 'dyn_fallfrost_flag', 'dyn_imperv_flag', 'dyn_intcp_flag',
#              'dyn_potet_flag',
#              'dyn_radtrncf_flag', 'dyn_snareathresh_flag', 'dyn_soil_flag', 'dyn_springfrost_flag',
#              'dyn_sro2dprst_imperv_flag', 'dyn_sro2dprst_perv_flag', 'dyn_transp_flag', 'frozen_flag',
#              'gwr_swale_flag', 'stream_temp_flag', 'subbasin_flag', 'covden_sum_dynamic', 'covden_win_dynamic',
#              'covtype_dynamic', 'dprst_depth_dynamic', 'dprst_frac_dynamic', 'fallfrost_dynamic',
#              'imperv_frac_dynamic', 'imperv_stor_dynamic', 'potetcoef_dynamic', 'radtrncf_dynamic',
#              'snareathresh_dynamic', 'snow_intcp_dynamic', 'soilmoist_dynamic', 'soilrechr_dynamic',
#              'springfrost_dynamic', 'srain_intcp_dynamic', 'sro2dprst_imperv_dynamic',
#              'sro2dprst_perv_dynamic', 'transp_flag_dynamic', 'transpbeg_dynamic', 'transpend_dynamic',
#              'wrain_intcp_dynamic', 'dprst_transferON_OFF', 'dprst_transfer_file', 'external_transferON_OFF',
#              'external_transfer_file', 'gwr_transferON_OFF', 'gwr_transfer_file', 'lake_transferON_OFF',
#              'lake_transfer_file', 'segment_transferON_OFF', 'segment_transfer_file', 'segmentOutON_OFF']
#
# ctl_module_params = ['et_module', 'precip_module', 'soilzone_module', 'solrad_module',
#                      'srunoff_module', 'strmflow_module', 'temp_module', 'transp_module']
#
# valtypes = ['', 'integer', 'float', 'double', 'string']


# class control(object):
#     """
#     Class which handles the processing of PRMS control files.
#     """
#     # Author: Parker Norton (pnorton@usgs.gov)
#     # Create date: 2015-02-05
#     # Description: Class object to handle reading and writing the PRMS
#     #              control files.
#
#     def __init__(self, filename):
#         # 1) open file
#         # 2) read file contents
#
#         self.__isloaded = False
#         self.__filename = filename
#         self.__controldict = {}
#         self.__modules = {}  # Initialize dictionary of selected module names
#         self.__header = []
#         self.__rowdelim = '####'  # Used to delimit variables
#         self.__valtypes = ['', 'integer', 'float', 'double', 'string']
#
#         self.filename = filename
#
#     # END __init__
#
#     def __getattr__(self, item):
#         return self.get_var(item)
#
#     def __str__(self):
#         outstr = ''
#         for xx in ctl_order:
#             try:
#                 pp = self.__controldict[xx]
#                 if len(pp['values']) == 1:
#                     outstr += '{0:s}: {1:s}, {2:s}\n'.format(xx, self.__valtypes[pp['valuetype']], str(pp['values'][0]))
#                 else:
#                     outstr += '{0:s}: {1:s}, {2:d} values\n'.format(xx, self.__valtypes[pp['valuetype']],
#                                                                     len(pp['values']))
#             except:
#                 continue
#         return outstr
#
#     @property
#     def filename(self):
#         if not self.__isloaded:
#             self.load_file(self.__filename)
#         return self.__filename
#
#     @filename.setter
#     def filename(self, fname):
#         self.__isloaded = False
#
#         self.__controldict = {}
#         self.__header = []
#
#         self.__filename = fname
#
#         self.load_file(self.__filename)
#
#     @property
#     def modules(self):
#         return self.__modules
#
#     @property
#     def vars(self):
#         # Return a list of variables
#         if not self.__isloaded:
#             self.load_file(self.__filename)
#
#         varlist = []
#
#         for cc in self.__controldict:
#             varlist.append(cc)
#         return varlist
#
#     @property
#     def rawvars(self):
#         return self.__controldict
#
#     def add(self, varname, vartype, val):
#         """Add a variable to the control file.
#
#         Args:
#             varname: The variable name to use.
#             vartype: The datatype of the variable (one of 'integer', 'string', 'double', 'float').
#             val: The value to assign to the variable
#         """
#         # Add a variable to the control file
#         if not self.__isloaded:
#             self.load_file(self.__filename)
#
#         cvars = self.vars
#
#         if varname in cvars:
#             print("ERROR: %s already exists, use replace_values() instead")
#             return
#
#         if not isinstance(val, list):
#             val = [val]
#
#         self.__controldict[varname] = {'valuetype': vartype, 'values': val}
#
#     def add_missing(self):
#         # Add missing control file variables
#         pass
#
#     def load_file(self, filename):
#         """Load a control file.
#
#         Reads the contents of a control file into the class.
#
#         Args:
#             filename: The name of the control file to read.
#         """
#         # Read the control file into memory and parse it
#         self.__isloaded = False
#         self.__modules = {}  # Initialize dictionary of selected module names
#         self.__controldict = {}  # Initialize the control dictionary
#
#         infile = open(filename, 'r')
#         rawdata = infile.read().splitlines()
#         infile.close()
#
#         it = iter(rawdata)
#
#         for fidx, line in enumerate(it):
#             if fidx == 0:
#                 self.__header.append(line)
#                 continue
#             elif line == self.__rowdelim:
#                 continue
#             else:
#                 # We're dealing with a control parameter/variable
#                 # We're in a parameter section
#                 vardict = {}  # temporary to build variable info
#                 varname = line.split(' ')[0]
#
#                 # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                 # Check for duplicate variable name
#                 if varname in self.__controldict:
#                     # Check for duplicate variables (that couldn't happen! :))
#                     # If it does skip to the next variable in the parameter file
#                     print('Duplicate variable name, %s, in Parameters section.. skipping' % varname)
#
#                     try:
#                         while next(it) != self.__rowdelim:
#                             pass
#                     except StopIteration:
#                         # We hit the end of the file
#                         continue
#                     continue
#                     # END check for duplicate varnames
#                 else:
#                     # Add variable to dictionary
#                     self.__controldict[varname] = {}
#                 # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#                 numval = int(next(it))  # number of values for this variable
#                 valuetype = int(next(it))  # Variable type (1 - integer, 2 - float, 4 - character)
#                 # print '\tnumval:', numval
#                 # print '\tvaluetype:', valuetype
#
#                 vardict['valuetype'] = int(valuetype)
#                 vals = []
#
#                 for vv in range(0, numval):
#                     try:
#                         if valuetype == 1:  # integer
#                             vals.append(int(next(it)))
#                         elif valuetype == 2:  # float
#                             vals.append(float(next(it)))
#                         else:  # character
#                             vals.append(next(it))
#                     except ValueError:
#                         print("varname: %s value type and defined type (%s) don't match" %
#                               (varname, self.__valtypes[valuetype]))
#                 vardict['values'] = vals
#
#                 if len(vals) != numval:
#                     print('ERROR: Not enough values provided for %s' % varname)
#                     print('       Expect %d, got %d' % (numval, len(vals)))
#
#                 # Check if there are too many values specified
#                 try:
#                     cnt = numval
#                     while next(it) != self.__rowdelim:
#                         cnt += 1
#
#                     if cnt > numval:
#                         print('WARNING: Too many values specified for %s' % varname)
#                         print('       %d expected, %d given' % (numval, cnt))
#                         print('       Keeping first %d values' % numval)
#                 except StopIteration:
#                     # Hit the end of the file
#                     pass
#                     # continue
#                 # self.__controldict[varname].append(vardict)
#                 self.__controldict[varname] = vardict
#
#                 # If this is a module-related parameter then add to __modules
#                 if varname in ctl_module_params:
#                     if len(vardict['values']) != 1:
#                         print("ERROR: %s should only have a single entry" % varname)
#                     else:
#                         if vardict['values'][0] not in self.__modules:
#                             self.__modules[vardict['values'][0]] = []
#                         self.__modules[vardict['values'][0]].append(varname)
#         # ***** END for line in it
#
#         # Add modules that should always included
#         def_mods = {'basin': ['basin_def'], 'soltab': ['potet_def'],
#                     'intcp': ['intcp_def'], 'snowcomp': ['snow_def'],
#                     'gwflow': ['gw_def'], 'soilzone': ['soil_def'],
#                     'basin_sum': ['summary_def']}
#         for (kk, vv) in iter(def_mods.items()):
#             self.__modules[kk] = vv
#
#         self.__isloaded = True
#
#     # END **** load_file()
#
#     def clear_parameter_group(self, group_name):
#         """Clear a parameter group.
#
#         Given a single parameter group name will clear out values for that parameter
#            and all related parameters.
#
#         Args:
#             group_name: The name of a group of related parameters.
#                 One of 'statVar', 'aniOut', 'mapOut', 'dispVar', 'nhruOut'.
#         """
#
#         groups = {'aniOut': {'naniOutVars': 0, 'aniOutON_OFF': 0, 'aniOutVar_names': []},
#                   'dispVar': {'ndispGraphs': 0, 'dispVar_element': [], 'dispVar_names': [], 'dispVar_plot': []},
#                   'mapOut': {'nmapOutVars': 0, 'mapOutON_OFF': 0, 'mapOutVar_names': []},
#                   'nhruOut': {'nhruOutVars': 0, 'nhruOutON_OFF': 0, 'nhruOutVar_names': []},
#                   'statVar': {'nstatVars': 0, 'statsON_OFF': 0, 'statVar_element': [], 'statVar_names': []}}
#
#         for (kk, vv) in iter(groups[group_name]).items():
#             if kk in self.__controldict:
#                 self.replace_values(kk, vv)
#
#     def get_var(self, varname):
#         """Get a control file variable.
#
#         Args:
#             varname: The name of the variable to retrieve.
#
#         Returns:
#             Returns a controldict entry.
#         """
#         # Return the given variable
#         if not self.__isloaded:
#             self.load_file(self.__filename)
#
#         if varname in self.__controldict:
#             return self.__controldict[varname]
#         return None
#
#     def get_values(self, varname):
#         """Get values for a control file variable.
#
#         Args:
#             varname: The name of the control file variable.
#
#         Returns:
#             Returns the value(s) associated with the control file variable
#         """
#         if not self.__isloaded:
#             self.load_file(self.__filename)
#
#         thevar = self.get_var(varname)['values']
#
#         if thevar is not None:
#             if len(thevar) == 1:
#                 return thevar[0]
#             else:
#                 return thevar
#         else:
#             return None
#
#     def replace_values(self, varname, newvals):
#         if not self.__isloaded:
#             self.load_file(self.__filename)
#
#         thevar = self.get_var(varname)
#
#         if isinstance(newvals, list):
#             pass
#         else:
#             # Convert newvals to a list
#             newvals = [newvals]
#
#         thevar['values'] = newvals
#
#         if varname in ['statVar_names', 'statVar_element'] and len(thevar['values']) != self.get_values('nstatVars'):
#             # update nstatvars
#             self.replace_values('nstatVars', len(newvals))
#
#             # Check if size of newvals array matches the oldvals array
#             # if len(newvals) == len(thevar['values']):
#             #     # Size of arrays match so replace the oldvals with the newvals
#             #     thevar['values'] = newvals
#             # else:
#             #     print "ERROR: Size of oldval array and size of newval array don't match"
#
#     def write_control_file(self, filename):
#         # Write the parameters out to a file
#         if not self.__isloaded:
#             self.load_file(self.__filename)
#
#         outfile = open(filename, 'w')
#
#         for hh in self.__header:
#             # Write out any header stuff
#             outfile.write('%s\n' % hh)
#
#         # Now write out the Parameter category
#         # order = ['name', 'dimnames', 'valuetype', 'values']
#         order = ['valuetype', 'values']
#
#         # Control file parameters may change. We'll use ctl_order to insure
#         # certain parameters are always ordered, but will be followed by any
#         # remaining non-ordered parameters.
#         curr_ctl = set(self.__controldict.keys())
#         curr_order = set(ctl_order)
#         unordered_set = curr_ctl.difference(curr_order)
#
#         # Add parameters that are missing in the ordered set at the end of the list
#         ctl_order.extend(list(unordered_set))
#
#         for kk in ctl_order:
#             if kk in self.__controldict:
#                 vv = self.__controldict[kk]
#             else:
#                 continue
#
#             valnum = len(vv['values'])
#             valtype = vv['valuetype']
#
#             # Set a format string based on the valtype
#             if valtype == 1:
#                 fmt = '%d\n'
#             elif valtype == 2:
#                 fmt = '%f\n'
#             else:
#                 fmt = '%s\n'
#
#             # Write the self.__rowdelim before the variable name
#             outfile.write('%s\n' % self.__rowdelim)
#             outfile.write('%s\n' % kk)
#
#             for item in order:
#                 # Write each variable out separated by self.__rowdelim
#                 val = vv[item]
#
#                 if item == 'valuetype':
#                     # valnum (which is computed) must be written before valuetype
#                     outfile.write('%d\n' % valnum)
#                     outfile.write('%d\n' % val)
#                 elif item == 'values':
#                     # Write one value per line
#                     for xx in val:
#                         outfile.write(fmt % xx)
#         outfile.close()
# # ***** END class control()


# class streamflow(object):
#     # Library to work with PRMS streamflow data files that were generated by
#     #   class gov.usgs.trinli.ft.point.writer.PrmsWriter
#
#     def __init__(self, filename, missing=-999.0, verbose=False):
#         # 1) open file
#         # 2) get the metaheaders
#         #    get the number of header lines
#         # 3) get the station list
#         # 4)
#
#         self.__missing = missing
#         self.filename = filename
#         self.__verbose = verbose
#         self.__timecols = 6  # number columns for time in the file
#         self.__headercount = None
#         self.__metaheader = None
#         self.__types = None
#         self.__units = []
#         self.__stations = None
#         self.__stationIndex = {}  # Lookup of station id to header info
#         self.__rawdata = None
#         self.__selectedStations = None
#         self.__isloaded = False
#
#         self.load_file(self.filename)
#
#     def load_file(self, filename):
#
#         self.__selectedStations = None  # Clear out any selected stations
#         self.__metaheader = []  # Hols the column names
#         self.__types = {}  # dictionary of 'Type' field in order of occurrence
#         self.__units = []  # list of units in file
#         self.__stations = []  # list of gage stations
#         self.__stationIndex = {}  # Lookup of station id to header info
#
#         # headerNext = False
#         # stationNext = False
#
#         infile = open(filename, 'r')
#         rawdata = infile.read().splitlines()
#         infile.close()
#
#         it = iter(rawdata)
#
#         self.__headercount = 0
#         # We assume if 'ID' and 'Type' header names exist then we have a valid
#         # meta-header.
#         for line in it:
#             self.__headercount += 1
#
#             # print line[0:10]
#             # Skip through lines until we hit the following
#             if line[0:10] == '// Station':
#                 # Read the next line in - this is the header info
#                 self.__headercount += 1
#                 self.__metaheader = re.findall(r"[\w]+", next(it))
#                 break
#
#         cnt = 0
#         order = 0  # defines the order of the data types in the dataset
#         # curr_fcnt = 0
#         st = 0
#
#         # print '-'*10,'metaheader','-'*10
#         # print self.__metaheader
#
#         for line in it:
#             self.__headercount += 1
#             if line[0:10] == '//////////':
#                 break
#
#             # Read in station information
#             # Include question mark in regex below as a valid character since the obs
#             # file uses it for missing data.
#             words = re.findall(r"[\w.-]+|[?]", line)  # Break the row up
#             curr_fcnt = len(words)
#
#             # Check that number of fields remains constant
#             if curr_fcnt != len(self.__metaheader):
#                 if self.__verbose:
#                     print("WARNING: number of header fields changed from %d to %d" %
#                           (len(self.__metaheader), curr_fcnt)),
#                     print("\t", words)
#                     # exit()
#
#             if words[self.__metaheader.index('Type')] not in self.__types:
#                 st = cnt  # last cnt becomes the starting column of the next type
#                 order += 1
#
#             # Information stored in __types array:
#             # 1) Order that type was added in
#             # 2) Starting index for data section
#             # 3) Ending index for data section
#             self.__types[words[self.__metaheader.index('Type')]] = [order, st, cnt]
#
#             self.__stations.append(words)
#             self.__stationIndex[words[0]] = cnt
#             cnt += 1
#
#         # print self.__types
#
#         # Now read in units and add to each type
#         # print '-'*10,'UNITS','-'*10
#         # print line
#         unittmp = next(it).split(':')[1].split(',')
#         for xx in unittmp:
#             unit_pair = xx.split('=')
#             # print 'unit_pair:', unit_pair[0].strip(), '/', unit_pair[1].strip()
#             # self.__units[unit_pair[0].strip()] = unit_pair[1].strip()
#             self.__units.append([unit_pair[0].strip(), unit_pair[1].strip()])
#
#         # print self.__units
#
#         # Skip to the data section
#         for line in it:
#             self.__headercount += 1
#             if line[0:10] == '##########':
#                 self.__headercount += 1  # plus one for good measure
#                 break
#
#         # print 'headercount:', self.__headercount
#         # Data section
#
#         # The first 6 columns are [year month day hour minute seconds]
#         thecols = ['year', 'month', 'day', 'hour', 'min', 'sec']
#
#         # Add the remaining columns to the list
#         for xx in self.__stations:
#             thecols.append(xx[0])
#
#         # print 'thecols:', thecols
#
#         # Use pandas to read the data in from the remainder of the file
#         # We use a custom date parser to convert the date information to a datetime
#         self.__rawdata = pd.read_csv(self.filename, skiprows=self.__headercount, sep=r"\s+",
#                                      header=None, names=thecols,
#                                      parse_dates={'thedate': ['year', 'month', 'day', 'hour', 'min', 'sec']},
#                                      date_parser=dparse, index_col='thedate')
#
#         # Convert the missing data (-999.0) to NaNs
#         self.__rawdata.replace(to_replace=self.__missing, value=np.nan, inplace=True)
#
#         # print self.__rawdata.head()
#         self.__isloaded = True
#
#     @property
#     def headercount(self):
#         # Description: Returns the line number where the data begins in the given
#         #              filename.
#         #        Date: 2013-07-01
#         if not self.__isloaded:
#             self.load_file(self.filename)
#         return self.__headercount
#
#     @property
#     def metaheader(self):
#         # Description: Reads the "meta" header from the prms
#         #        Date: 2013-06-25
#
#         if not self.__isloaded:
#             self.load_file(self.filename)
#         return self.__metaheader
#
#     @property
#     def stations(self):
#         # Description: Get the list of stations in the prms file.
#         #        Note: Modified to return a list of all fields for each station
#
#         # The order of the 'Type' field dictates the gross order of the following
#         # data section.  For a given 'Type' the order of the 'ID' (stations) dictates
#         # order of the data.
#
#         # Get the meta-headers for the file
#         if not self.__isloaded:
#             self.load_file(self.filename)
#         return self.__stations
#
#     @property
#     def timecolcnt(self):
#         return self.__timecols
#
#     @property
#     def types(self):
#         if not self.__isloaded:
#             self.load_file(self.filename)
#         return self.__types
#
#     @property
#     def data(self):
#         if not self.__isloaded:
#             self.load_file(self.filename)
#
#         if self.__selectedStations is None:
#             return self.__rawdata
#         else:
#             return self.__rawdata.ix[:, self.__selectedStations]
#
#     @property
#     def date_range(self):
#         if not self.__isloaded:
#             self.load_file(self.filename)
#
#         # Return the first and last available date for valid streamflow data
#         # 2015-05-19: This currently assumes it is returning a single streamgage
#         tmpdf = self.data.dropna(axis=0, how='any')
#         first_date = tmpdf[tmpdf.notnull()].index.min()
#         last_date = tmpdf[tmpdf.notnull()].index.max()
#
#         return first_date, last_date
#
#     @property
#     def numdays(self):
#         """The period of record in days"""
#         if not self.__isloaded:
#             self.load_file(self.filename)
#         return self.data.shape[0]
#
#     @property
#     def timedata(self):
#         """Returns an array of time information"""
#         # FIXME: This needs to be updated (2015-02-03)
#         return self.data[:, 0:self.timecolcnt].astype(int)
#
#     @property
#     def units(self):
#         return self.__units
#
#     def getDataByType(self, thetype):
#         """Returns data selected type (e.g. runoff)"""
#
#         if thetype in self.__types:
#             # print "Selected type '%s':" % (thetype), self.__types[thetype]
#             st = self.__types[thetype][1]
#             en = self.__types[thetype][2]
#             # print "From %d to %d" % (st, en)
#             b = self.data.iloc[:, st:en + 1]
#
#             return b
#         else:
#             print("not found")
#
#     def getStationsByType(self, thetype):
#         """Returns station IDs for a given type (e.g. runoff)"""
#
#         if thetype in self.__types:
#             # print "Selected type '%s':" % (thetype), self.__types[thetype]
#             st = self.__types[thetype][1]
#             en = self.__types[thetype][2]
#             # print "From %d to %d" % (st, en)
#             b = self.stations[st:en + 1]
#
#             return b
#         else:
#             print("not found")
#
#     def selectByStation(self, streamgages):
#         """Selects one or more streamgages from the dataset"""
#         # The routine writeSelected() will write selected streamgages and data
#         # to a new PRMS streamflow file.
#         # Use clearSelectedStations() to clear any current selection.
#         if isinstance(streamgages, list):
#             self.__selectedStations = streamgages
#         else:
#             self.__selectedStations = [streamgages]
#
#     def clearSelectedStations(self):
#         """Clears any selected streamgages"""
#         self.__selectedStations = None
#
#     def writeSelectedStations(self, filename):
#         """Writes station observations to a new file"""
#         # Either writes out all station observations or, if stations are selected,
#         # then a subset of station observations.
#
#         # Sample header format
#
#         # $Id:$
#         # ////////////////////////////////////////////////////////////
#         # // Station metadata (listed in the same order as the data):
#         # // ID    Type Latitude Longitude Elevation
#         # // <station info>
#         # ////////////////////////////////////////////////////////////
#         # // Unit: runoff = ft3 per sec, elevation = feet
#         # ////////////////////////////////////////////////////////////
#         # runoff <number of stations for each type>
#         # ################################################################################
#
#         top_line = '$Id:$\n'
#         section_sep = '////////////////////////////////////////////////////////////\n'
#         meta_header_1 = '// Station metadata (listed in the same order as the data):\n'
#         # metaHeader2 = '// ID    Type Latitude Longitude Elevation'
#         meta_header_2 = '// %s\n' % ' '.join(self.metaheader)
#         data_section = '################################################################################\n'
#
#         # ----------------------------------
#         # Get the station information for each selected station
#         type_count = {}  # Counts the number of stations for each type of data (e.g. 'runoff')
#         stninfo = ''
#         if self.__selectedStations is None:
#             for xx in self.__stations:
#                 if xx[1] not in type_count:
#                     # index 1 should be the type field
#                     type_count[xx[1]] = 0
#                 type_count[xx[1]] += 1
#
#                 stninfo += '// %s\n' % ' '.join(xx)
#         else:
#             for xx in self.__selectedStations:
#                 cstn = self.__stations[self.__stationIndex[xx]]
#
#                 if cstn[1] not in type_count:
#                     # index 1 should be the type field
#                     type_count[cstn[1]] = 0
#
#                 type_count[cstn[1]] += 1
#
#                 stninfo += '// %s\n' % ' '.join(cstn)
#         # stninfo = stninfo.rstrip('\n')
#
#         # ----------------------------------
#         # Get the units information
#         unit_line = '// Unit:'
#         for uu in self.__units:
#             unit_line += ' %s,' % ' = '.join(uu)
#         unit_line = '%s\n' % unit_line.rstrip(',')
#
#         # ----------------------------------
#         # Create the list of types of data that are being included
#         tmpl = []
#
#         # Create list of types in the correct order
#         for (kk, vv) in iter(self.__types.items()):
#             if kk in type_count:
#                 tmpl.insert(vv[0], [kk, type_count[kk]])
#
#         type_line = ''
#         for tt in tmpl:
#             type_line += '%s %d\n' % (tt[0], tt[1])
#         # typeLine = typeLine.rstrip('\n')
#
#         # Write out the header to the new file
#         outfile = open(filename, 'w')
#         outfile.write(top_line)
#         outfile.write(section_sep)
#         outfile.write(meta_header_1)
#         outfile.write(meta_header_2)
#         outfile.write(stninfo)
#         outfile.write(section_sep)
#         outfile.write(unit_line)
#         outfile.write(section_sep)
#         outfile.write(type_line)
#         outfile.write(data_section)
#
#         # Write out the data to the new file
#         # Using quoting=csv.QUOTE_NONE results in an error when using a customized  date_format
#         # A kludgy work around is to write with quoting and then re-open the file
#         # and write it back out, stripping the quote characters.
#         self.data.to_csv(outfile, index=True, header=False, date_format='%Y %m %d %H %M %S', sep=' ')
#         outfile.close()
#
#         old = open(filename, 'r').read()
#         new = re.sub('["]', '', old)
#         open(filename, 'w').write(new)
#
#         # def getRecurrenceInterval(self, thetype):
#         #     """Returns the recurrence intervals for each station"""
#         #
#         #     # Copy the subset of data
#         #     xx = self.seldata(thetype)
#         #
#         #     ri = np.zeros(xx.shape)
#         #     ri[:,:] = -1.
#         #
#         #     # for each station we need to compute the RI for non-zero values
#         #     for ss in range(0,xx.shape[1]):
#         #         tmp = xx[:,ss]              # copy values for current station
#         #
#         #         # Get array of indices that would result in a sorted array
#         #         sorted_ind = np.argsort(tmp)
#         #         #print "sorted_ind.shape:", sorted_ind.shape
#         #
#         #         numobs = tmp[(tmp > 0.0),].shape[0]  # Number of observations > 0.
#         #         nyr = float(numobs / 365)     # Number of years of non-zero observations
#         #
#         #         nz_cnt = 0  # non-zero value counter
#         #         for si in sorted_ind:
#         #             if tmp[si] > 0.:
#         #                 nz_cnt += 1
#         #                 rank = numobs - nz_cnt + 1
#         #                 ri[si,ss] = (nyr + 1.) / float(rank)
#         #                 #print "%s: [%d]: %d %d %0.3f %0.3f" % (ss, si,  numobs, rank, tmp[si], ri[si,ss])
#         #
#         #     return ri
# # ***** END of class streamflow()


# class param_db(object):
#     # Author: Parker Norton (pnorton@usgs.gov)
#     # Create date: 2016-01-06
#     # Description: Object for the database of valid input parameters
#
#     def __init__(self, filename):
#         # Mapping of certain parameters to their correct module
#         self.__mod_map = {'hru_pansta': ['potet_pan'],
#                           'tmin_adj': ['temp_1sta', 'temp_laps', 'ide_dist', 'xyz_dist'],
#                           'tmax_adj': ['temp_1sta', 'temp_laps', 'ide_dist', 'xyz_dist'],
#                           'hru_tsta': ['temp_1sta', 'temp_laps'],
#                           'basin_tsta': ['temp_1sta', 'temp_laps', 'temp_dist2'],
#                           'psta_elev': ['precip_laps', 'ide_dist', 'xyz_dist'],
#                           'tsta_elev': ['temp_1sta', 'temp_laps', 'temp_dist2', 'ide_dist', 'xyz_dist'],
#                           'elevlake_init': ['muskingum_lake'],
#                           'gw_seep_coef': ['muskingum_lake'],
#                           'lake_evap_adj': ['muskingum_lake'],
#                           'lake_hru': ['muskingum_lake'],
#                           'lake_hru_id': ['muskingum_lake'],
#                           'lake_seep_elev': ['muskingum_lake'],
#                           'lake_type': ['muskingum_lake']}
#
#         self.__filename = filename
#         self.__paramdb = None
#
#         # TODO: need more robust logic here; currently no way to handle failures
#         self.__isloaded = False
#         self.__build_paramdb()
#         self.__isloaded = True
#
#     @property
#     def filename(self):
#         return self.__filename
#
#     @filename.setter
#     def filename(self, fname):
#         self.__filename = fname
#
#         self.__isloaded = False
#         self.__build_paramdb()
#         self.__isloaded = True
#
#     @property
#     def paramdb(self):
#         return self.__paramdb
#
#     def __build_paramdb(self):
#         """Build the input parameter db from a collection of par_name files in a directory"""
#         filelist = []
#
#         if os.path.isfile(self.__filename):
#             # A single input par_name file was specified
#             filelist = [self.__filename]
#         elif os.path.isdir(self.__filename):
#             # A path containing multiple par_name files was specified
#             filelist = [el for el in glob.glob('%s/*par_name*' % self.__filename)]
#
#         thefirst = True
#
#         for ff in filelist:
#             if thefirst:
#                 self.__paramdb = self.__read_parname_file(ff)
#                 thefirst = False
#             else:
#                 curr_dict = self.__read_parname_file(ff)
#
#                 # Add new control parameters or update module field for existing parameters
#                 for (kk, vv) in iter(curr_dict.items()):
#                     if kk in self.__paramdb:
#                         # Control parameter already exists, check if this is a new module
#                         if isinstance(self.__paramdb[kk]['Module'], list):
#                             if vv['Module'][0] not in self.__paramdb[kk]['Module']:
#                                 self.__paramdb[kk]['Module'] += vv['Module']
#                                 # self.__paramdb[kk]['Module'].append(vv['Module'])
#                         else:
#                             if vv['Module'] != self.__paramdb[kk]['Module']:
#                                 # Convert Module entry to a list and add the new module name
#                                 tmp = self.__paramdb[kk]['Module']
#                                 self.__paramdb[kk]['Module'] = [tmp, vv['Module']]
#                     else:
#                         # We have a new control parameter
#                         self.__paramdb[kk] = vv
#
#     def __read_parname_file(self, fname):
#         """Given a .par_name file (generated by prms -print) returns a dictionary
#            of valid parameters. Returns None if file cannot be opened"""
#
#         validparams = {}
#
#         # Create parameter default ranges file from from PRMS -print results
#         try:
#             infile = open(fname, 'r')
#         except IOError as err:
#             print("Unable to open file\n", err)
#             return None
#         else:
#             rawdata = infile.read().splitlines()
#             infile.close()
#
#             it = iter(rawdata)
#
#             for line in it:
#                 if line == '--------------- PARAMETERS ---------------':
#                     break
#
#             toss_param = False  # Trigger for removing unwanted parameters
#
#             for line in it:
#                 flds = line.split(':')
#
#                 if len(flds) < 2:
#                     continue
#
#                 key = flds[0].strip()
#                 val = flds[1].strip()
#
#                 # Only need 'Name' and 'Module' information
#                 if key == 'Name':
#                     if toss_param:
#                         # Remove prior parameter if it was not wanted
#                         del validparams[cparam]
#                         toss_param = False
#
#                     cparam = val  # Save parameter name for the remaining information
#                     validparams[cparam] = {}
#                 elif key == 'Module':
#                     if val == 'setup':
#                         # Don't want to include parameters from the setup module
#                         toss_param = True
#
#                     # Override module(s) for select parameters
#                     if cparam in self.__mod_map:
#                         validparams[cparam][key] = self.__mod_map[cparam]
#                     else:
#                         validparams[cparam][key] = [val]
#                 elif key == 'Ndimen':
#                     # Number of dimensions is superfluous; don't store
#                     pass
#                 elif key == 'Dimensions':
#                     # Get the dimension names; discard the sizes
#                     dnames = [xx.split('-')[0].strip() for xx in val.split(',')]
#                     validparams[cparam][key] = dnames
#                 elif key == 'Size':
#                     # Don't need the total parameter size
#                     pass
#                 elif key == 'Type':
#                     cparam_type = val  # needed to convert max, min, and default values
#                     validparams[cparam][key] = val
#                 elif key == 'Units':
#                     if cparam_type == 'string':
#                         # Units for strings are 'none'; no reason to store
#                         pass
#                 elif key == 'Width':
#                     # Width currently isn't populated
#                     pass
#                 elif key in ['Max', 'Min', 'Default']:
#                     if cparam_type == 'float':
#                         validparams[cparam][key] = float(val)
#                     elif cparam_type == 'long':
#                         validparams[cparam][key] = int(val)
#                     else:
#                         validparams[cparam][key] = val
#                 else:
#                     validparams[cparam][key] = val
#         return validparams
#
#     def get_param_subset(self, mods):
#         """Return subset of paramdb based on selected modules"""
#         subset = {}
#
#         param_by_module = self.module_params(mods)
#
#         for (cmod, params) in iter(param_by_module.items()):
#             for param in params:
#                 subset[param] = self.__paramdb[param]
#
#         return subset
#
#     def module_params(self, mod):
#         # mod is a dictionary containing a single entry with format:
#         #         key = a valid module name for any of vals
#         #         val = one of [et_module, precip_module, solrad_module, srunoff_module,
#         #               strmflow_module, temp_module, transp_module]
#
#         params_by_module = {}
#
#         # Build params by modules
#         for (cmodname, val_mod) in iter(mod.items()):
#             # Can have one or more set
#             for c_mod in val_mod:
#                 for (kk, vv) in iter(self.__paramdb.items()):
#                     if cmodname in vv['Module']:
#                         if kk in ['potet_cbh_adj'] and cmodname == 'climate_hru' and c_mod != 'et_module':
#                             # Only include potet_cbh_adj if et_module == climate_hru
#                             continue
#
#                         if cmodname not in params_by_module:
#                             # Add new module entry
#                             params_by_module[cmodname] = []
#
#                         if kk not in params_by_module[cmodname]:
#                             # Add new parameter name
#                             params_by_module[cmodname].append(kk)
#         return params_by_module


# class parameters(object):
#     # Author: Parker Norton (pnorton@usgs.gov)
#     # Create date: 2015-01-29
#     # Description: Class object to handle reading and writing the PRMS
#     #              parameter files which have been generated by Java.
#
#     # TODO: Add basic statistical functions
#
#     def __init__(self, filename):
#         # 1) open file
#         # 2) read file contents
#
#         self.__isloaded = False
#         self.__validparamsloaded = False  # Valid params are loaded by load_valid_parameters()
#         self.__filename = filename
#         self.__paramdict = {}
#         self.__paramdb = None  # Dictionary of required parameters from *.par_name file(s)
#         self.__header = []
#         self.__vardict = {}
#         self.__vardirty = True  # Flag to trigger rebuild of self.__vardict
#         self.__catdelim = '**'  # Delimiter for categories of variables
#         self.__rowdelim = '####'  # Used to delimit variables
#         self.__valtypes = ['', 'integer', 'float', 'double', 'string']
#
#         self.load_file()
#
#     # END __init__
#
#     def __getattr__(self, item):
#         # Undefined attributes will look up the given parameter
#         return self.get_var(item)
#
#     @property
#     def dimensions(self):
#         """Return a list of dimensions"""
#         if not self.__isloaded:
#             self.load_file()
#
#         # dimlist = []
#         # parent = self.__paramdict['Dimensions']
#         #
#         # for kk,vv in iter(parent.items()):
#         #     dimlist.append((kk, vv))
#         #
#         # return dimlist
#         return self.__paramdict['Dimensions']
#
#     @property
#     def filename(self):
#         # if not self.__isloaded:
#         #     self.load_file(self.__filename)
#         return self.__filename
#
#     @filename.setter
#     def filename(self, fname):
#         self.__isloaded = False
#
#         self.__paramdict = {}
#         self.__header = []
#
#         self.__filename = fname
#
#         self.load_file()
#
#     @property
#     def headers(self):
#         """Returns the headers read from the parameter file"""
#         return self.__header
#
#     @property
#     def vars(self):
#         """Return a structure of loaded variables"""
#         if not self.__isloaded:
#             self.load_file()
#
#         varlist = []
#         parent = self.__paramdict['Parameters']
#
#         for ee in parent:
#             varlist.append(ee['name'])
#
#         return varlist
#
#     def add_dimension(self, dimname, value):
#         """Add a new dimension"""
#         if not self.__isloaded:
#             self.load_file()
#
#         parent = self.__paramdict['Dimensions']
#
#         if dimname in parent:
#             print('ERROR: Dimension already exists. %s = %d' % (dimname, parent[dimname]))
#         else:
#             parent[dimname] = int(value)
#
#     def add_param(self, name, dimnames, valuetype, values):
#         # Add a new parameter
#         if not self.__isloaded:
#             self.load_file()
#
#         # Check that valuetype is valid
#         if valuetype not in [1, 2, 3, 4]:
#             print("ERROR: Invalid valuetype was specified")
#             return
#
#         # Check that total dimension size matches number of values supplied
#         if isinstance(dimnames, list):
#             # multiple dimensions supplied
#             tsize = 1
#
#             for dd in dimnames:
#                 tsize *= self.get_dim(dd)
#
#             if tsize != len(values):
#                 print("ERROR: Number of values (%d) does not match size of dimensions (%d)" % (len(values), tsize))
#                 return
#         else:
#             # single dimension
#             tsize = self.get_dim(dimnames)
#
#             if isinstance(values, list):
#                 print("ERROR: Scalar dimensions specified but of list of values given")
#                 return
#
#         parent = self.__paramdict['Parameters']
#
#         # Make sure the parameter doesn't already exist
#         if self.var_exists(name):
#             print('ERROR: Parameter name already exists, use replace_values() instead.')
#             return
#
#         # for ee in parent:
#         #     if ee['name'] == name:
#         #         print 'ERROR: Parameter name already exists, use replace_values() instead.'
#         #         return
#
#         if isinstance(dimnames, list):
#             parent.append({'name': name, 'dimnames': dimnames, 'valuetype': valuetype, 'values': values})
#         else:
#             parent.append({'name': name, 'dimnames': [dimnames], 'valuetype': valuetype, 'values': values})
#
#         self.rebuild_vardict()
#
#     def add_param_from_file(self, fname):
#         """Add one or more parameter(s) from a file."""
#
#         tmp_params = []
#
#         infile = open(fname, 'r')
#         rawdata = infile.read().splitlines()
#         infile.close()
#
#         it = iter(rawdata)
#
#         for line in it:
#             dupskip = False
#
#             if line == self.__rowdelim:
#                 # Skip to next iteration when a row delimiter is found
#                 continue
#             else:
#                 vardict = {}  # temporary to build variable info
#                 varname = line.split(' ')[0]
#
#                 # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                 # Check for duplicate variable name
#                 for kk in tmp_params:
#                     # Check for duplicate variables (that couldn't happen! :))
#                     # If it does skip to the next variable in the parameter file
#                     if varname == kk['name']:
#                         print('%s: Duplicate parameter name.. skipping' % varname)
#                         dupskip = True
#                         break
#
#                 if dupskip:
#                     try:
#                         while next(it) != self.__rowdelim:
#                             pass
#                     except StopIteration:
#                         # We hit the end of the file
#                         pass
#                     continue
#                 # END check for duplicate varnames
#                 # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#                 vardict['name'] = varname
#
#                 # Read in the dimension names
#                 numdim = int(next(it))  # number of dimensions for this variable
#                 vardict['dimnames'] = [next(it) for dd in range(numdim)]
#
#                 # Lookup dimension size for each dimension name
#                 arr_shp = [self.__paramdict['Dimensions'][dd] for dd in vardict['dimnames']]
#
#                 numval = int(next(it))  # Denotes the number of data values we have. Should match dimensions.
#                 valuetype = int(next(it))  # Datatype of the values
#                 vardict['valuetype'] = int(valuetype)
#
#                 try:
#                     # Read in the data values
#                     vals = []
#
#                     while True:
#                         cval = next(it)
#
#                         if cval == self.__rowdelim or cval.strip() == '':
#                             break
#                         vals.append(cval)
#                 except StopIteration:
#                     # Hit the end of the file
#                     pass
#
#                 if len(vals) != numval:
#                     print('%s: number of values does not match dimension size (%d != %d).. skipping' %
#                           (varname, len(vals), numval))
#                 else:
#                     # Convert the values to the correct datatype
#                     # 20151118 PAN: found a value of 1e+05 in nhm_id for r17 caused this to fail
#                     #               even though manaully converting the value to int works.
#                     try:
#                         if valuetype == 1:  # integer
#                             vals = [int(vals) for vals in vals]
#                         elif valuetype == 2:  # float
#                             vals = [float(vals) for vals in vals]
#                     except ValueError:
#                         print("%s: value type and defined type (%s) don't match" %
#                               (varname, self.__valtypes[valuetype]))
#
#                     # Add to dictionary as a numpy array
#                     vardict['values'] = np.array(vals).reshape(arr_shp)
#                     tmp_params.append(vardict)
#
#         # Add or replace parameters depending on whether they already exist
#         for pp in tmp_params:
#             if self.var_exists(pp['name']):
#                 print("Replacing existing parameter: %s" % pp['name'])
#                 self.replace_values(pp['name'], pp['values'], pp['dimnames'])
#             else:
#                 print("Adding new parameter: %s" % pp['name'])
#                 self.add_param(pp['name'], pp['dimnames'], pp['valuetype'], pp['values'])
#
#     def check_var(self, varname):
#         # Check a variable to see if the number of values it has is
#         # consistent with the given dimensions
#
#         if not self.__isloaded:
#             self.load_file()
#
#         thevar = self.get_var(varname)
#
#         # Get the defined size for each dimension used by the variable
#         total_size = 1
#         for dd in thevar['dimnames']:
#             total_size *= self.get_dim(dd)
#
#         if thevar['values'].size == total_size:
#             # The number of values for the defined dimensions match
#             print('%s: OK' % varname)
#         else:
#             print('%s: BAD' % varname)
#
#     def check_all_vars(self):
#         """Check all parameter variables for proper array size"""
#         if not self.__isloaded:
#             self.load_file()
#
#         parent = self.__paramdict['Parameters']
#
#         for ee in parent:
#             self.check_var(ee['name'])
#
#     def check_all_module_vars(self, mods):
#         """Given a .par_name file verify whether all needed parameters are in the parameter file"""
#         # mods      Dictionary created by param_db.module_params()
#
#         for (cmodule, params) in iter(mods.items()):
#             print('Module:', cmodule)
#
#             for cparam in params:
#                 if cparam in ['gw_seep_coef', 'elevlake_init', 'lake_hru_id',
#                               'lake_seep_elev', 'lake_hru', 'lake_type'] and not self.get_dim('nlake'):
#                     continue
#                 elif cparam in ['basin_solsta', 'hru_solsta', 'rad_conv'] and not self.get_dim('nlake'):
#                     continue
#                 elif cparam in ['irr_type'] and not self.get_dim('nwateruser'):
#                     continue
#
#                 if not self.var_exists(cparam):
#                     print('\t%s: MISSING' % cparam)
#
#     def copy_param(self, varname, filename):
#         """Copies selected varname from given src input parameter file (filename).
#         The incoming parameter is verified to have the same dimensions and sizes as
#         the destination. This method is intended to work with full parameter files.
#         To copy parameters from partial parameter files use add_param_from_file()."""
#
#         # TODO: Expand this handle one or more varnames
#         srcparamfile = parameters(filename)
#         srcparam = srcparamfile.get_var(varname)
#
#         if self.var_exists(srcparam['name']):
#             print('Replacing existing parameter')
#             self.replace_values(srcparam['name'], srcparam['values'], srcparam['dimnames'])
#         else:
#             print('Adding new parameter')
#             self.add_param(srcparam['name'], srcparam['dimnames'], srcparam['valuetype'], srcparam['values'])
#         del srcparamfile
#
#     def distribute_mean_value(self, varname, new_mean):
#         # def redistribute_mean(old_vals, new_mean):
#         # Redistribute mean value to set of multiple initial values
#         # see Hay and Umemoto, 2006 (p. 11)
#
#         old_vals = self.get_var(varname)['values']
#
#         if old_vals.size > 1:
#             # This parameter is a list of values
#             zc = 10.  # Constant to avoid zero values
#             new_vals = []
#
#             old_mean = old_vals.sum() / float(old_vals.size)
#
#             for vv in old_vals.flatten():
#                 new_vals.append((((new_mean + zc) * (vv + zc)) / (old_mean + zc)) - zc)
#
#             self.replace_values(varname, np.array(new_vals).reshape(old_vals.shape))
#         else:
#             # Even scalar values are stored as numpy arrays
#             self.replace_values(varname, np.array(new_mean).reshape(old_vals.shape))
#
#     def expand_params(self, valid_params):
#         """Given a dictionary of valid parameters from paramdb will expand the
#            input parameters to their maximum dimensionality"""
#         # 1) Check that all parameters required by modules are present and expand them (add as necessary)
#         #    1a) Handle parameters that need conversion and/or renaming (e.g. soil_rechr_max->soil_rechr_max_frac)
#         #    1b) Missing parameters should be added with default values
#         #    1c) Existing parameters should be expanded in place
#         # 2) Remove any remaining deprecated or non-needed parameters
#         # 3) Check parameter integrity
#
#         param_type = {'long': 1, 'float': 2, 'double': 3, 'string': 4}
#
#         # Deprecated parameter relationships
#         # depr_params = {'smidx_coef': 'carea_min',
#         depr_params = {'dprst_area': 'dprst_frac',
#                        # 'hru_percent_imperv': 'imperv_frac',
#                        'soil_moist_init': 'soil_moist_init_frac',
#                        'soil_rechr_init': 'soil_rechr_init_frac',
#                        'soil_rechr_max': 'soil_rechr_max_frac',
#                        'sro_to_dprst': 'sro_to_dprst_perv',
#                        'ssstor_init': 'ssstor_init_frac',
#                        'tmax_allrain': 'tmax_allrain_offset'}
#
#         if not self.__isloaded:
#             self.load_file()
#
#         # Iterator through parameters
#         cparams = set(self.vars)
#         vparams = set(valid_params.keys())
#
#         # Parameters common to the deprecated params (depr_params) and the current input parameters (cparams)
#         conv_params = set(depr_params.keys()).intersection(cparams)
#
#         # =====================================================================
#         # Deprecated parameters conversion
#         # Convert (as necessary) and rename deprecated parameters to new names
#         # This only converts existing data, expansion is done later
#         remove_list = []
#         for cc in conv_params:
#             if cc == 'soil_rechr_max':
#                 # Convert with soil_rechr_max_frac = soil_rechr_max / soil_moist_max
#                 newparam = valid_params[depr_params[cc]]
#                 newarr = self.get_var(cc)['values'] / self.get_var('soil_moist_max')['values']
#                 self.add_param(depr_params[cc], self.get_var(cc)['dimnames'], param_type[newparam['Type']], newarr)
#                 remove_list.append(cc)
#             elif cc == 'dprst_area':
#                 # Convert with dprst_frac = dprst_area / hru_area
#                 newparam = valid_params[depr_params[cc]]
#                 newarr = self.get_var(cc)['values'] / self.get_var('hru_area')['values']
#                 self.add_param(depr_params[cc], self.get_var(cc)['dimnames'], param_type[newparam['Type']], newarr)
#                 remove_list.append(cc)
#             elif cc == 'tmax_allrain':
#                 # Convert with tmax_allrain_offset = tmax_allrain - tmax_allsnow
#                 newparam = valid_params[depr_params[cc]]
#                 newarr = self.get_var(cc)['values'] - self.get_var('tmax_allsnow')['values']
#                 self.add_param(depr_params[cc], self.get_var(cc)['dimnames'], param_type[newparam['Type']], newarr)
#                 remove_list.append(cc)
#             elif cc == 'soil_moist_init':
#                 # Convert with soil_moist_init_frac = soil_moist_init / soil_moist_max
#                 newparam = valid_params[depr_params[cc]]
#                 newarr = self.get_var(cc)['values'] / self.get_var('soil_moist_max')['values']
#                 newarr[newarr > 1.0] = 1.0
#                 self.add_param(depr_params[cc], self.get_var(cc)['dimnames'], param_type[newparam['Type']], newarr)
#                 remove_list.append(cc)
#             elif cc == 'soil_rechr_init':
#                 # Convert with soil_rechr_init_frac = soil_rechr_init / soil_rechr_max
#                 if self.var_exists('soil_rechr_init'):
#                     if self.var_exists('soil_rechr_max'):
#                         newparam = valid_params[depr_params[cc]]
#                         newarr = self.get_var(cc)['values'] / self.get_var('soil_rechr_max')['values']
#                         newarr[newarr > 1.0] = 1.0
#                         self.add_param(depr_params[cc], self.get_var(cc)['dimnames'], param_type[newparam['Type']], newarr)
#                     elif self.var_exists('soil_rechr_max_frac'):
#                         # Compute with alternative equation of
#                         # soil_rechr_init_frac = soil_rechr_init / (soil_rechr_max_frac * soil_moist_max)
#                         newparam = valid_params[depr_params[cc]]
#                         newarr = self.get_var(cc)['values'] / (self.get_var('soil_rechr_max_frac')['values'] * self.get_var('soil_moist_max')['values'])
#                         newarr[newarr > 1.0] = 1.0
#                         self.add_param(depr_params[cc], self.get_var(cc)['dimnames'], param_type[newparam['Type']], newarr)
#                 else:
#                     print('ERROR: Missing parameters required for converting to %s' % valid_params[depr_params[cc]])
#                 remove_list.append(cc)
#             elif cc == 'ssstor_init':
#                 # Convert with ssstor_init_frac = sstor_init / sat_threshold
#                 newparam = valid_params[depr_params[cc]]
#                 newarr = self.get_var(cc)['values'] / self.get_var('sat_threshold')['values']
#                 newarr[newarr > 1.0] = 1.0
#                 self.add_param(depr_params[cc], self.get_var(cc)['dimnames'], param_type[newparam['Type']], newarr)
#                 remove_list.append(cc)
#             else:
#                 # Rename any other deprecated params
#                 # TODO: Many of the new _frac parameters need to be handled individually
#                 self.rename_param(cc, depr_params[cc])
#
#         # Remove parameters that are deprecated
#         for pp in remove_list:
#             print("Removing deprecated parameter %s" % pp)
#             self.remove_param(pp)
#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#         # =====================================================================
#         # Add missing parameters using default values
#         # Check for any valid params (vparams) that are missing from cparams.
#         # These will be created with default values
#         cparams = set(self.vars)
#         def_params = vparams.difference(cparams)
#         # print 'New parameters to create with default value:', def_params
#
#         for pp in def_params:
#             if pp in ['basin_solsta', 'hru_solsta', 'rad_conv'] and not self.get_dim('nsol'):
#                 # Shouldn't be added if nsol == 0
#                 continue
#             elif pp in ['hru_pansta'] and not self.get_dim('nevapl'):
#                 # Shouldn't be added if nevapl == 0
#                 continue
#             elif pp in ['lake_hru_id'] and not self.get_dim('nlake'):
#                 # Shouldn't be added if nlake == 0
#                 continue
#             elif pp in ['irr_type'] and not self.get_dim('nwateruse'):
#                 # Shouldn't be added if nwateruser == 0
#                 continue
#             elif pp in ['gvr_hru_id'] and not self.get_dim('nhrucell'):
#                 continue
#
#             newparam = valid_params[pp]
#             newarr = np.asarray(newparam['Default'])
#
#             # Compute new dimension size
#             newsize = 1
#             for dd in newparam['Dimensions']:
#                 if self.get_dim(dd) is None:
#                     print("Not adding %s because %s doesn't exist" % (pp, dd))
#                     newsize = 0
#                     break
#                 else:
#                     newsize *= self.get_dim(dd)
#
#             if newsize > 0:
#                 # Create new array, repeating default value to fill it
#                 newarr = np.resize(newarr, newsize)
#                 self.add_param(pp, newparam['Dimensions'], param_type[newparam['Type']], newarr)
#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#         # =====================================================================
#         # Create set of cparams that are not needed by modules
#         # Not used for now but it could be used to strip out unneeded additional parameters
#         addl_params = cparams.difference(vparams)
#         print('cparams not in validparams:', addl_params)
#         print('-' * 40)
#
#         # =====================================================================
#         # Expand parameters whose dimensionality has changed
#         for ee in vparams:
#             if ee in ['basin_solsta', 'hru_solsta', 'rad_conv'] and not self.get_dim('nsol'):
#                 # Shouldn't be added if nsol == 0
#                 continue
#             elif ee in ['hru_pansta'] and not self.get_dim('nevapl'):
#                 # Shouldn't be added if nevapl == 0
#                 continue
#             elif ee in ['lake_hru_id'] and not self.get_dim('nlake'):
#                 # Shouldn't be added if nlake == 0
#                 continue
#             elif ee in ['irr_type'] and not self.get_dim('nwateruse'):
#                 # Shouldn't be added if nwateruser == 0
#                 continue
#             elif ee in ['gvr_hru_id'] and not self.get_dim('nhrucell'):
#                 continue
#
#             cvar = self.get_var(ee)
#             if cvar is None:
#                 print("Not expanding %s because parameter doesn't exist" % ee)
#             else:
#                 cname = cvar['name']
#
#                 # Check for changed dimensionality
#                 cdimnames = cvar['dimnames']
#                 vdimnames = valid_params[cname]['Dimensions']
#
#                 if set(vdimnames).issubset(set(cdimnames)):
#                     # NOTE: This doesn't properly handle the case when number of
#                     #       dimensions has shrunk.
#                     # print "%s: No dimensionality change" % cname
#                     pass
#                 else:
#                     # Parameter has a change in dimensionality
#                     print("%s: Dimensionality changed from" % cname, cdimnames, 'to', vdimnames)
#
#                     # Compute new dimension size
#                     newsize = 1
#                     for dd in vdimnames:
#                         newsize *= self.get_dim(dd)
#
#                     # Create new array, repeating original values to fill it
#                     newarr = np.resize(cvar['values'], newsize)
#
#                     self.replace_values(cname, newarr, vdimnames)
#         # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#         self.rebuild_vardict()
#         return None
#
#     def get_dim(self, dimname):
#         # Return the size of the specified dimension
#
#         if not self.__isloaded:
#             self.load_file()
#
#         parent = self.__paramdict['Dimensions']
#
#         if dimname in parent:
#             return parent[dimname]
#         return None
#
#     def get_var(self, varname):
#         # Return the given variable
#
#         if not self.__isloaded:
#             self.load_file()
#
#         parent = self.__paramdict['Parameters']
#
#         for ee in parent:
#             if ee['name'] == varname:
#                 return ee
#         raise ValueError('Parameter does not exist.')
#
#         return None
#
#     def load_file(self):
#         # Read the parameter file into memory and parse it
#
#         self.__paramdict = {}  # Initialize the parameter dictionary
#         self.__vardict = {}  # dictionary of parameter names to paramdict array index
#
#         self.__header = []  # Initialize the list of file headers
#
#         infile = open(self.__filename, 'r')
#         rawdata = infile.read().splitlines()
#         infile.close()
#
#         it = iter(rawdata)
#         curr_cat = None  # Current category (None, Dimensions, or Parameters)
#
#         for line in it:
#             dupskip = False
#
#             if line[0:2] == self.__catdelim:
#                 # Found the category delimiter
#                 curr_cat = line.strip('* ')
#
#                 if curr_cat == 'Dimensions':
#                     self.__paramdict[curr_cat] = {}
#                 elif curr_cat == 'Parameters':
#                     self.__paramdict[curr_cat] = []
#             elif line == self.__rowdelim:
#                 # Skip to next iteration when a row delimiter is found
#                 continue
#             else:
#                 if curr_cat is None:
#                     # Any lines up to the Dimensions category go into the header
#                     # The parameter file header is defined to be exactly 2 lines
#                     # but this will handle any number of header lines.
#                     self.__header.append(line)
#                 elif curr_cat == 'Dimensions':
#                     # Dimension variables are scalar integers
#                     self.__paramdict[curr_cat][line] = int(next(it))
#                 elif curr_cat == 'Parameters':
#                     vardict = {}  # temporary to build variable info
#                     varname = line.split(' ')[0]
#
#                     # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#                     # Check for duplicate variable name
#                     for kk in self.__paramdict['Parameters']:
#                         # Check for duplicate variables (that couldn't happen! :))
#                         # If it does skip to the next variable in the parameter file
#                         if varname == kk['name']:
#                             print('%s: Duplicate parameter name.. skipping' % varname)
#                             dupskip = True
#                             break
#
#                     if dupskip:
#                         try:
#                             while next(it) != self.__rowdelim:
#                                 pass
#                         except StopIteration:
#                             # We hit the end of the file
#                             pass
#                         continue
#                     # END check for duplicate varnames
#                     # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#                     vardict['name'] = varname
#
#                     # Read in the dimension names
#                     numdim = int(next(it))  # number of dimensions for this variable
#                     vardict['dimnames'] = [next(it) for dd in range(numdim)]
#
#                     # Lookup dimension size for each dimension name
#                     arr_shp = [self.__paramdict['Dimensions'][dd] for dd in vardict['dimnames']]
#                     dim_size = reduce(lambda x, y: x*y, arr_shp)
#
#                     numval = int(next(it))  # Denotes the number of data values we have. Should match dimensions.
#                     valuetype = int(next(it))  # Datatype of the values
#                     vardict['valuetype'] = int(valuetype)
#
#                     if numval != dim_size:
#                         # The declared total size doesn't match the total size of the declared dimensions
#                         print('%s: Declared total size for parameter does not match the total size of the declared dimension(s) (%d != %d).. skipping'
#                               % (varname, numval, dim_size))
#
#                         # Still have to read all the values to skip this properly
#                         try:
#                             while True:
#                                 cval = next(it)
#
#                                 if cval == self.__rowdelim or cval.strip() == '':
#                                     break
#                         except StopIteration:
#                             # Hit the end of the file
#                             pass
#                     else:
#                         # Check if number of values written match the number of values declared
#                         try:
#                             # Read in the data values
#                             vals = []
#
#                             while True:
#                                 cval = next(it)
#
#                                 if cval == self.__rowdelim or cval.strip() == '':
#                                     break
#                                 vals.append(cval)
#                         except StopIteration:
#                             # Hit the end of the file
#                             pass
#
#                         if len(vals) != numval:
#                             print('%s: number of values does not match dimension size (%d != %d).. skipping' %
#                                   (varname, len(vals), numval))
#                         else:
#                             # Convert the values to the correct datatype
#                             # 20151118 PAN: found a value of 1e+05 in nhm_id for r17 caused this to fail
#                             #               even though manaully converting the value to int works.
#                             try:
#                                 if valuetype == 1:  # integer
#                                     vals = [int(vals) for vals in vals]
#                                 elif valuetype == 2:  # float
#                                     vals = [float(vals) for vals in vals]
#                             except ValueError:
#                                 print("%s: value type and defined type (%s) don't match" %
#                                       (varname, self.__valtypes[valuetype]))
#
#                             # Add to dictionary as a numpy array
#                             # Use column-major ordering for Fortran
#                             vardict['values'] = np.array(vals).reshape(arr_shp, order='F')
#                             self.__paramdict['Parameters'].append(vardict)
#
#         # Build the vardict dictionary (links varname to array index in self.__paramdict)
#         self.rebuild_vardict()
#
#         self.__isloaded = True
#
#     def pull_hru2(self, hru_index, filename):
#         # Pulls a single HRU out by index and writes a new parameter file for that HRU
#         # This version greatly improves on the original pull_hru by just reading from the parameter
#         # data structure and writing the modified file directly instead of modifying a copy of the
#         # original parameter structure and then writing it out.
#
#         split_dims = ['nhru', 'nssr', 'ngw']
#         ndepl = self.get_dim('ndepl')
#         nhru = self.get_dim('nhru')
#         order = ['name', 'dimnames', 'valuetype', 'values']
#
#         # Parameters that need parent information saved
#         # parent_info = {'hru_segment': 'parent_hru',
#         #                'tosegment': 'parent_segment' }
#
#         # List of vars that have dimension of nsegment
#         # TODO: This should be auto-created from the parameter file based on the dimension type
#         segvars = ['K_coef', 'obsin_segment', 'x_coef', 'segment_type', 'segment_flow_init', 'parent_segment',
#                    'nhm_seg', 'tosegment_nhm']
#
#         # Adjustment values for select dimensions
#         dim_adj = {'nobs': 1, 'nsegment': 1, 'npoigages': 0}
#
#         # ===================================================================
#         outfile = open(filename, 'w')
#
#         # -------------------------------------------------------------------
#         for hh in self.__header:
#             # Write out any header stuff
#             outfile.write('%s\n' % hh)
#
#         # Dimension section must be written first
#         dimparent = self.__paramdict['Dimensions']
#
#         outfile.write('%s Dimensions %s\n' % (self.__catdelim, self.__catdelim))
#
#         # -------------------------------------------------------------------
#         for (kk, vv) in iter(dimparent.items()):
#             # Write the dimension names and values separated by self.__rowdelim
#             outfile.write('%s\n' % self.__rowdelim)
#             outfile.write('%s\n' % kk)
#
#             # Adjust the split_dims e.g. nhru, ngw, nssr and asssorted other dimensions
#             if kk in split_dims:
#                 outfile.write('%d\n' % 1)
#             elif kk in dim_adj:
#                 outfile.write('%d\n' % dim_adj[kk])
#             elif kk == 'ndepl':
#                 outfile.write('%d\n' % 1)
#             elif kk == 'ndeplval':
#                 outfile.write('%d\n' % 11)
#             else:
#                 outfile.write('%d\n' % vv)
#
#         # Now write out the Parameter category
#         paramparent = self.__paramdict['Parameters']
#
#         outfile.write('%s Parameters %s\n' % (self.__catdelim, self.__catdelim))
#
#         # Get the segment index for the HRU we are grabbing
#         seg_idx = self.get_var('hru_segment')['values'][hru_index]
#         sys.stdout.write('\rHRU %06d to segment: %06d' % (hru_index, seg_idx))
#         sys.stdout.flush()
#
#         # -------------------------------------------------------------------
#         for vv in paramparent:
#             valtype = vv['valuetype']
#
#             # Set a format string based on the valtype
#             if valtype == 1:
#                 fmt = '%s\n'
#             elif valtype == 2:
#                 # fmt = '%0.8f\n'
#                 fmt = '%s\n'
#             else:
#                 fmt = '%s\n'
#
#             if bool(set(vv['dimnames']).intersection(split_dims)):
#                 # dealing with nhru, nssr, or ngw
#
#                 if len(vv['dimnames']) == 2:
#                     the_values = vv['values'][hru_index, :]
#                     dimsize = vv['values'][hru_index, :].size
#                 elif len(vv['dimnames']) == 1:
#                     the_values = vv['values'][hru_index]
#                     dimsize = vv['values'][hru_index].size
#             elif bool(set(vv['dimnames']).intersection(set(['ndeplval']))):
#                 # The ndeplval dimension is actually nhru x 11
#                 # The index for ndeplval for each HRU is stored in hru_deplcrv
#                 crv_idx = self.get_var('hru_deplcrv')['values'][hru_index] - 1
#                 the_values = vv['values'].reshape((-1, 11), order='A')[crv_idx]
#                 dimsize = 11
#             else:
#                 dimsize = vv['values'].size
#                 the_values = vv['values']
#
#             # Special overrides for some parameters
#             if vv['name'] in segvars:
#                 the_values = np.array([vv['values'][seg_idx - 1]])
#                 dimsize = 1
#             elif vv['name'] == 'hru_deplcrv':
#                 # The hru_deplcrv parameter is the snarea_curve index for each HRU.
#                 # For a single HRU this should be reset to 1.
#                 the_values = np.array([1])
#                 dimsize = 1
#             elif vv['name'] == 'hru_segment':
#                 the_values = np.array([1])
#                 dimsize = 1
#             elif vv['name'] in ['tosegment']:
#                 the_values = np.array([0])
#                 dimsize = 1
#             elif vv['name'] in ['poi_gage_segment', 'poi_type', 'poi_gage_id']:
#                 # 2016-03-24: Having these parameters causes PRMS to error out
#                 continue
#
#             for item in order:
#                 # Write each variable write out separated by self.__rowdelim
#                 val = vv[item]
#
#                 if item == 'dimnames':
#                     # Write number of dimensions first
#                     outfile.write('%d\n' % len(val))
#                     for dd in val:
#                         # Write dimension names
#                         outfile.write('%s\n' % dd)
#                 elif item == 'valuetype':
#                     # dimsize (which is computed) must be written before valuetype
#                     outfile.write('%d\n' % dimsize)
#                     outfile.write('%d\n' % val)
#                 elif item == 'values':
#                     # Write one value per line
#                     for xx in the_values.flatten():
#                         outfile.write(fmt % xx)
#                 elif item == 'name':
#                     # Write the self.__rowdelim before the variable name
#                     outfile.write('%s\n' % self.__rowdelim)
#                     outfile.write('%s\n' % val)
#
#         # Not quite done... add parent information so we can stitch the HRUs back together later
#         # order = ['name', 'dimnames', 'valuetype', 'values']
#
#         # Write the parent_segment information
#         # The parent_segment is the value that was used in the parent parameter file for hru_segment at
#         # the given parent_hru index. It shouldn't be needed for checking a single HRU back into the
#         # parent parameter file.
#         outfile.write('%s\n' % self.__rowdelim)
#         outfile.write('%s\n' % 'parent_segment')
#         outfile.write('%d\n' % 1)
#         outfile.write('%s\n' % 'nsegment')
#         outfile.write('%d\n' % 1)
#         outfile.write('%d\n' % 1)
#         outfile.write('%d\n' % seg_idx)
#
#         # Write the parent_hru information
#         # The parent_hru is the index to use when checking a single HRU file back into the parent parameter file
#         outfile.write('%s\n' % self.__rowdelim)
#         outfile.write('%s\n' % 'parent_hru')
#         outfile.write('%d\n' % 1)
#         outfile.write('%s\n' % 'nhru')
#         outfile.write('%d\n' % 1)
#         outfile.write('%d\n' % 1)
#         outfile.write('%d\n' % (hru_index + 1))
#
#         outfile.close()
#
#     def rebuild_vardict(self):
#         # Build the vardict dictionary (links varname to array index in self.__paramdict)
#         self.__vardict = {}
#         for idx, vname in enumerate(self.__paramdict['Parameters']):
#             self.__vardict[vname['name']] = idx
#         self.__vardirty = False
#
#     def remove_param(self, varname):
#         """Removes a parameter"""
#         if not self.__isloaded:
#             self.load_file()
#
#         if self.get_var(varname) is not None:
#             for ii, vv in enumerate(self.__paramdict['Parameters']):
#                 if vv['name'] == varname:
#                     rmidx = ii
#
#             del self.__paramdict['Parameters'][rmidx]
#
#     def rename_param(self, varname, newname):
#         """Renames a parameter"""
#         if not self.__isloaded:
#             self.load_file()
#
#         thevar = self.get_var(varname)
#         thevar['name'] = newname
#
#     def replace_values(self, varname, newvals, newdims=None):
#         """Replaces all values for a given variable/parameter. Size of old and new arrays/values must match."""
#         if not self.__isloaded:
#             self.load_file()
#
#         # parent = self.__paramdict['Parameters']
#         thevar = self.get_var(varname)
#
#         # NOTE: Need to figure out whether this function should expect row-major ordering
#         #       or column-major ordering when called. Right it expects column-major ordering
#         #       for newvals, which means no re-ordering of the array is necessary when
#         #       replacing values.
#         if newdims is None:
#             # We are not changing dimensions of the variable/parameter, just the values
#             # Check if size of newvals array matches the oldvals array
#             if isinstance(newvals, list) and len(newvals) == thevar['values'].size:
#                 # Size of arrays match so replace the oldvals with the newvals
#                 # Lookup dimension size for each dimension name
#                 arr_shp = [self.__paramdict['Dimensions'][dd] for dd in thevar['dimnames']]
#
#                 thevar['values'][:] = np.array(newvals).reshape(arr_shp)
#             elif isinstance(newvals, np.ndarray) and newvals.size == thevar['values'].size:
#                 # newvals is a numpy ndarray
#                 # Size of arrays match so replace the oldvals with the newvals
#                 # Lookup dimension size for each dimension name
#                 arr_shp = [self.__paramdict['Dimensions'][dd] for dd in thevar['dimnames']]
#
#                 thevar['values'][:] = newvals.reshape(arr_shp)
#             # NOTE: removed the following because even scalars should be stored as numpy array
#             # elif thevar['values'].size == 1:
#             #     # This is a scalar value
#             #     if isinstance(newvals, float):
#             #         thevar['values'] = [newvals]
#             #     elif isinstance(newvals, int):
#             #         thevar['values'] = [newvals]
#             else:
#                 print("ERROR: Size of oldval array and size of newval array don't match")
#         else:
#             # The dimensions are being changed and new values provided
#
#             # Use the dimension sizes from the parameter file to check the size
#             # of the newvals array. If the size of the newvals array doesn't match the
#             # parameter file's dimensions sizes we have a problem.
#             size_check = 1
#             for dd in newdims:
#                 size_check *= self.get_dim(dd)
#
#             if isinstance(newvals, list) and len(newvals) == size_check:
#                 # Size of arrays match so replace the oldvals with the newvals
#                 thevar['values'] = newvals
#                 thevar['dimnames'] = newdims
#             elif isinstance(newvals, np.ndarray) and newvals.size == size_check:
#                 # newvals is a numpy ndarray
#                 # Size of arrays match so replace the oldvals with the newvals
#                 thevar['values'] = newvals
#                 thevar['dimnames'] = newdims
#             elif thevar['values'].size == 1:
#                 # This is a scalar value
#                 thevar['dimnames'] = newdims
#                 if isinstance(newvals, float):
#                     thevar['values'] = [newvals]
#                 elif isinstance(newvals, int):
#                     thevar['values'] = [newvals]
#             else:
#                 print("ERROR: Size of newval array doesn't match dimensions in parameter file")
#
#     def resize_dim(self, dimname, newsize):
#         """Changes the size of the given dimension.
#            This does *not* check validity of parameters that use the dimension.
#            Check variable integrity before writing parameter file."""
#
#         # Some dimensions are related to each other.
#         related_dims = {'ndepl': 'ndeplval', 'nhru': ['nssr', 'ngw'],
#                         'nssr': ['nhru', 'ngw'], 'ngw': ['nhru', 'nssr']}
#
#         if not self.__isloaded:
#             self.load_file()
#
#         parent = self.__paramdict['Dimensions']
#
#         if dimname in parent:
#             parent[dimname] = newsize
#
#             # Also update related dimensions
#             if dimname in related_dims:
#                 if dimname == 'ndepl':
#                     parent[related_dims[dimname]] = parent[dimname] * 11
#                 elif dimname in ['nhru', 'nssr', 'ngw']:
#                     for dd in related_dims[dimname]:
#                         parent[dd] = parent[dimname]
#             return True
#         else:
#             return False
#
#     def update_values_by_hru(self, varname, newvals, hru_index):
#         """Updates parameter/variable with new values for a a given HRU.
#            This is used when merging data from an individual HRU into a region"""
#         if not self.__isloaded:
#             self.load_file()
#
#         # parent = self.__paramdict['Parameters']
#         thevar = self.get_var(varname)
#
#         if len(newvals) == 1:
#             thevar['values'][(hru_index - 1)] = newvals
#         elif len(newvals) == 2:
#             thevar['values'][(hru_index - 1), :] = newvals
#         elif len(newvals) == 3:
#             thevar['values'][(hru_index - 1), :, :] = newvals
#
#     def var_exists(self, varname):
#         """Checks to see if a variable exists in the currently loaded parameter file.
#            Returns true if the variable exists, otherwise false."""
#         if not self.__isloaded:
#             self.load_file()
#
#         if varname in self.__vardict:
#             return True
#         return False
#
#     def write_select_param_file(self, filename, selection):
#         # Write selected subset of parameters to a new parameter file
#         if not self.__isloaded:
#             self.load_file()
#
#         outfile = open(filename, 'w')
#
#         # Write out the Parameter category
#         order = ['name', 'dimnames', 'valuetype', 'values']
#
#         for ss in selection:
#             vv = self.get_var(ss)
#             dimsize = vv['values'].size
#             valtype = vv['valuetype']
#
#             # Set a format string based on the valtype
#             if valtype == 1:
#                 fmt = '%s\n'
#             elif valtype == 2:
#                 # fmt = '%f\n'
#                 fmt = '%s\n'
#             else:
#                 fmt = '%s\n'
#
#             for item in order:
#                 # Write each variable out separated by self.__rowdelim
#                 val = vv[item]
#
#                 if item == 'dimnames':
#                     # Write number of dimensions first
#                     outfile.write('%d\n' % len(val))
#                     for dd in val:
#                         # Write dimension names
#                         outfile.write('%s\n' % dd)
#                 elif item == 'valuetype':
#                     # dimsize (which is computed) must be written before valuetype
#                     outfile.write('%d\n' % dimsize)
#                     outfile.write('%d\n' % val)
#                 elif item == 'values':
#                     # Write one value per line
#                     for xx in val.flatten():
#                         outfile.write(fmt % xx)
#                 elif item == 'name':
#                     # Write the self.__rowdelim before the variable name
#                     outfile.write('%s\n' % self.__rowdelim)
#                     outfile.write('%s 10\n' % val)
#
#         outfile.close()
#
#     def write_param_file(self, filename):
#         # Write the parameters out to a file
#
#         if not self.__isloaded:
#             self.load_file()
#
#         outfile = open(filename, 'w')
#
#         for hh in self.__header:
#             # Write out any header stuff
#             outfile.write('%s\n' % hh)
#
#         # Dimension section must be written first
#         dimparent = self.__paramdict['Dimensions']
#
#         outfile.write('%s Dimensions %s\n' % (self.__catdelim, self.__catdelim))
#
#         for (kk, vv) in iter(dimparent.items()):
#             # Write the dimension names and values separated by self.__rowdelim
#             outfile.write('%s\n' % self.__rowdelim)
#             outfile.write('%s\n' % kk)
#             outfile.write('%d\n' % vv)
#
#         # Now write out the Parameter category
#         paramparent = self.__paramdict['Parameters']
#         order = ['name', 'dimnames', 'valuetype', 'values']
#
#         outfile.write('%s Parameters %s\n' % (self.__catdelim, self.__catdelim))
#
#         for vv in paramparent:
#             dimsize = vv['values'].size
#             valtype = vv['valuetype']
#
#             # Set a format string based on the valtype
#             if valtype == 1:
#                 fmt = '%s\n'
#             elif valtype == 2:
#                 # fmt = '%f\n'
#                 fmt = '%s\n'
#             else:
#                 fmt = '%s\n'
#
#             for item in order:
#                 # Write each variable out separated by self.__rowdelim
#                 val = vv[item]
#
#                 if item == 'dimnames':
#                     # Write number of dimensions first
#                     outfile.write('%d\n' % len(val))
#                     for dd in val:
#                         # Write dimension names
#                         outfile.write('%s\n' % dd)
#                 elif item == 'valuetype':
#                     # dimsize (which is computed) must be written before valuetype
#                     outfile.write('%d\n' % dimsize)
#                     outfile.write('%d\n' % val)
#                 elif item == 'values':
#                     # Write one value per line
#                     for xx in val.flatten(order='A'):
#                         outfile.write(fmt % xx)
#                 elif item == 'name':
#                     # Write the self.__rowdelim before the variable name
#                     outfile.write('%s\n' % self.__rowdelim)
#                     outfile.write('%s\n' % val)
#
#         outfile.close()
#
#
# # ***** END of class parameters()


# class statvar(object):
#     def __init__(self, filename=None, missing=-999.0):
#         self.__timecols = 6  # number columns for time in the file
#         self.__missing = missing  # what is considered a missing value?
#
#         self.__isloaded = False
#         self.__vars = None
#         self.__rawdata = None
#         self.__metaheader = None
#         self.__header = None
#         self.__headercount = None
#         self.__types = None
#         self.__units = {}
#         self.__stations = None
#         self.__filename = ''
#         self.filename = filename  # trigger the filename setter
#
#     @property
#     def filename(self):
#         if not self.__isloaded:
#             self.load_file(self.__filename)
#         return self.__filename
#
#     @filename.setter
#     def filename(self, fname):
#         self.__isloaded = False
#         self.__vars = None
#         self.__rawdata = None
#         self.__metaheader = None
#         self.__header = None
#         self.__headercount = None
#         self.__types = None
#         self.__units = {}
#         self.__stations = None
#         self.__filename = fname
#
#         self.load_file(self.__filename)
#
#     def load_file(self, filename):
#         """Load a statvar file"""
#
#         infile = open(filename, 'r')
#
#         # The first line gives the number of variables that follow
#         numvars = int(infile.readline())
#         # print "Number of variables: %d" % (numvars)
#
#         # The next numvar rows contain a variable name followed by a number which
#         # indicates the number of columns used by that variable.
#         # The relative order of the variable in the list indicates the column
#         # the variable data is found in.
#         self.__isloaded = False
#         self.__vars = {}
#         self.__header = []
#
#         # The first 7 columns are [record year month day hour minute seconds]
#         self.__header = ['rec', 'year', 'month', 'day', 'hour', 'min', 'sec']
#
#         for rr in range(0, numvars):
#             row = infile.readline()
#             fields = row.rstrip().split(' ')
#             varname = fields[0]
#             varsize = int(fields[1])
#
#             # Store the variable name along with the order it was read
#             # and the dimension size of the variable.
#             self.__vars[varname] = [rr, varsize]
#
#             # Add to the header
#             # TODO: Lookup each variable to find the dimension name.
#             #       This could be used to create informative headers
#             for dd in range(0, varsize):
#                 if varsize > 1:
#                     # If a variable has dimension more than one (e.g. hru)
#                     # then append a sequential number to each instance
#                     self.__header.append('%s_%d' % (varname, dd + 1))
#                 else:
#                     self.__header.append('%s' % varname)
#
#         # Now load the data
#
#         # Use pandas to read the data in from the remainder of the file
#         # We use a custom date parser to convert the date information to a datetime
#         self.__rawdata = pd.read_csv(infile, sep=r"\s+", header=None, names=self.__header,
#                                      parse_dates={'thedate': ['year', 'month', 'day', 'hour', 'min', 'sec']},
#                                      date_parser=dparse, index_col='thedate')
#
#         # Drop the 'rec' field and convert the missing data to NaNs
#         self.__rawdata.drop(['rec'], axis=1, inplace=True)
#         self.__rawdata.replace(to_replace=self.__missing, value=np.nan, inplace=True)
#
#         self.__isloaded = True
#
#     # **** END def load_file()
#
#     @property
#     def headercount(self):
#         """Returns the size of the header list"""
#         if not self.__isloaded:
#             self.load_file(self.filename)
#         return len(self.__header)
#
#     @property
#     def vars(self):
#         """Returns a dictionary of the variables in the statvar file"""
#         if not self.__isloaded:
#             self.load_file(self.filename)
#         return self.__vars
#
#     @property
#     def data(self):
#         """Returns the pandas dataframe of data from the statvar file"""
#         if not self.__isloaded:
#             self.load_file(self.filename)
#         return self.__rawdata
#
# # ***** END of class statvar()

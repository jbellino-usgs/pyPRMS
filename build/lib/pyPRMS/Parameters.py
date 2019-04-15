
from __future__ import (absolute_import, division, print_function)
# from future.utils import iteritems

import numpy as np
import pandas as pd
from collections import OrderedDict
import xml.etree.ElementTree as xmlET

from pyPRMS.Exceptions_custom import ParameterError
from pyPRMS.constants import DATA_TYPES
from pyPRMS.Dimensions import ParamDimensions


class Parameter(object):
    """
    Container for a single Parameter object

    A parameter has a name, datatype, optional units, one or more dimensions, and
    associated data.
    """

    # Container for a single parameter
    def __init__(self, name=None, datatype=None, units=None, model=None, description=None,
                 help=None, modules=None, minimum=None, maximum=None, default=None):
        """Initialize the Parameter object

        :param name: A valid PRMS parameter name
        :param datatype: The datatype for the parameter (1-Integer, 2-Float, 3-Double, 4-String)
        :param units: Option units string for the parameter"""

        self.__modules = []

        self.__name = name  # string
        self.__datatype = datatype  # ??
        self.__units = units    # string (optional)
        self.__model = model    # string (optional)
        self.__description = description    # string (optional)
        self.__help = help      # string (optional)
        self.modules = modules      # PRMS modules that use the parameter (optional)
        self.__minimum = minimum    # Minimum value allowed (optional)
        self.__maximum = maximum    # Maximum value allowed (optional)
        self.__default = default    # Default value for parameter (optional)

        self.__dimensions = ParamDimensions()
        self.__data = None  # array

    def __str__(self):
        """Return a pretty print string representation of the parameter information"""

        outstr = 'name: {}\ndatatype: {}\nunits: {}\nndims: {}\ndescription: {}\nhelp: {}\n'.format(self.name, self.datatype,
                                                                         self.units, self.ndims, self.description, self.help)

        if self.__minimum is not None:
            outstr += 'Minimum value: {}\n'.format(self.__minimum)

        if self.__maximum is not None:
            outstr += 'Maximum value: {}\n'.format(self.__maximum)

        if self.__default is not None:
            outstr += 'Default value: {}\n'.format(self.__default)

        outstr += 'Size of data: '
        if self.__data is not None:
            outstr += '{}\n'.format(self.data.size)
        else:
            outstr += '<empty>\n'

        if self.__modules is not None:
            outstr += 'Modules: '

            for xx in self.__modules:
                outstr += '{} '.format(xx)
            outstr += '\n'

        if self.ndims:
            outstr += 'Dimensions:\n' + self.__dimensions.__str__()
        return outstr

    @property
    def as_dataframe(self):
        """Returns the data for the parameter as a pandas dataframe"""

        if len(self.data.shape) == 2:
            df = pd.DataFrame(self.data)
            df.rename(columns=lambda xx: '{}_{}'.format(self.name, df.columns.get_loc(xx) + 1), inplace=True)
        else:
            # Assuming 1D array
            df = pd.DataFrame(self.data, columns=[self.name])
            # df.rename(columns={0: name}, inplace=True)

        return df

    @property
    def name(self):
        """Returns the name of the parameter"""
        return self.__name

    @property
    def datatype(self):
        """Returns the datatype of the parameter"""
        return self.__datatype

    @datatype.setter
    def datatype(self, dtype):
        """Sets the datatype for the parameter

        :param dtype: The datatype for the parameter (1-Integer, 2-Float, 3-Double, 4-String)
        """
        # TODO: Should this be able to handle both string (e.g. 'I') and integer datatypes?
        # TODO: If datatype is changed should verify existing data can be cast to it
        if dtype in DATA_TYPES:
            self.__datatype = dtype
        else:
            print('WARNING: Datatype, {}, is not valid.'.format(dtype))

    @property
    def units(self):
        """Returns the units used for the parameter data"""
        return self.__units

    @units.setter
    def units(self, unitstr):
        """Set the units used for the parameter data

        :param unitstr: String denoting the units for the parameter (e.g. mm)
        """
        self.__units = unitstr

    @property
    def model(self):
        """Returns the model the parameter is used in"""
        return self.__model

    @model.setter
    def model(self, modelstr):
        """Set the model description for the parameter

        :param modelstr: String denoting the model (e.g. PRMS)
        """
        self.__model = modelstr

    @property
    def description(self):
        """Returns the parameter description"""
        return self.__description

    @description.setter
    def description(self, descstr):
        """Set the model description for the parameter

        :param descstr: Description string
        """
        self.__description = descstr

    @property
    def help(self):
        """Returns the help information for the parameter"""
        return self.__help

    @help.setter
    def help(self, helpstr):
        """Set the help string for the parameter

        :param helpstr: Help string
        """
        self.__help = helpstr

    @property
    def minimum(self):
        """Returns the minimum valid value for the parameter"""
        return self.__minimum

    @minimum.setter
    def minimum(self, value):
        """Set the minimum valid value for the parameter

        :param value: The value to use
        """
        if self.__datatype is None:
            self.__minimum = value
        elif DATA_TYPES[self.__datatype] == 'float':
            self.__minimum = float(value)
        elif DATA_TYPES[self.__datatype] == 'integer':
            try:
                self.__minimum = int(value)
            except ValueError:
                # This happens with 'bounded' parameters
                self.__minimum = value
        else:
            self.__minimum = value

    @property
    def maximum(self):
        """Returns the maximum valid value for the parameter"""
        return self.__maximum

    @maximum.setter
    def maximum(self, value):
        """Set the maximum valid value for the parameter

        :param value: The value to use
        """
        if self.__datatype is None:
            self.__maximum = value
        elif DATA_TYPES[self.__datatype] == 'float':
            self.__maximum = float(value)
        elif DATA_TYPES[self.__datatype] == 'integer':
            try:
                self.__maximum = int(value)
            except ValueError:
                # This happens with bounded parameters
                self.__maximum = value
        else:
            self.__maximum = value

    @property
    def default(self):
        """Returns the minimum valid value for the parameter"""
        return self.__default

    @default.setter
    def default(self, value):
        """Set the default value for the parameter

        :param value: The value to use
        """
        if self.__datatype is None:
            self.__default = value
        elif DATA_TYPES[self.__datatype] == 'float':
            self.__default = float(value)
        elif DATA_TYPES[self.__datatype] == 'integer':
            self.__default = int(value)
        else:
            self.__default = value

    @property
    def modules(self):
        """Returns the names of the modules that use the parameter"""
        return self.__modules

    @modules.setter
    def modules(self, modulestr):
        """Set the names of the modules that use the parameter

        :param modulestr: Single module name or list of module names to add
        """
        if modulestr is not None:
            if isinstance(modulestr, list):
                self.__modules.extend(modulestr)
            else:
                self.__modules.append(modulestr)
        else:
            # Don't add a None type to the set of modules
            pass

    @property
    def dimensions(self):
        """Returns the Dimensions object associated with the parameter"""
        return self.__dimensions

    @property
    def ndims(self):
        """Returns the number of dimensions that are defined for the parameter"""
        # Return the number of dimensions defined for the parameter
        return self.__dimensions.ndims

    @property
    def data(self):
        """Returns the data associated with the parameter"""
        if self.__data is not None:
            return self.__data
        raise ValueError('Parameter, {}, has no data'.format(self.__name))

    @data.setter
    def data(self, data_in):
        """Sets the data associated with the parameter

        :param data_in: A list containing the data for the parameter
        """
        # Raise an error if no dimensions are defined for parameter
        if not self.ndims:
            raise ValueError('No dimensions have been defined for {}. Unable to append data'.format(self.name))

        # Convert datatype first
        datatype_conv = {1: self.__str_to_int, 2: self.__str_to_float,
                         3: self.__str_to_float, 4: self.__str_to_str}

        if self.__datatype in DATA_TYPES.keys():
            data_in = datatype_conv[self.__datatype](data_in)
        else:
            raise TypeError('Defined datatype {} for parameter {} is not valid'.format(self.__datatype,
                                                                                       self.__name))

        # Convert list to np.array
        if self.ndims == 2:
            data_np = np.array(data_in).reshape((-1, self.get_dimsize_by_index(1),), order='F')
            # data_np = np.array(data_in).reshape((-1, self.__dimensions.get_dimsize_by_index(1),), order='F')
        elif self.ndims == 1:
            data_np = np.array(data_in)
        else:
            raise ValueError('Number of dimensions, {}, is not supported'.format(self.ndims))

        # Replace data
        # self.__data = data_np

        if 'one' in self.__dimensions.dimensions.keys():
            # A parameter with the dimension 'one' should never have more
            # than 1 value. Output warning if the incoming value is different
            # from a pre-existing value
            if data_np.size > 1:
                print('WARNING: {} with dimension "one" has {} values. Using first ' +
                      'value only.'.format(self.__name, data_np.size))
            # self.__data = np.array(data_np[0])
            self.__data = data_np
        else:
            self.__data = data_np

    @property
    def xml(self):
        """Return the xml metadata for the parameter as xml Element"""
        param_root = xmlET.Element('parameter')
        param_root.set('name', self.name)
        param_root.set('version', 'ver')
        param_root.append(self.dimensions.xml)
        return param_root

    def concat(self, data_in):
        """Takes a list and concatenates to the end of the parameter data.
        This is most useful when reading 2D parameter data by region where
        the ordering of the data must be correctly maintained in the final
        dataset"""
        if not self.ndims:
            raise ValueError('No dimensions have been defined for {}. Unable to concatenate data'.format(self.name))

        if self.__data is None:
            # Don't bother with the concatenation if there is no pre-existing data
            self.data = data_in
            return

        # Convert datatype first
        datatype_conv = {1: self.__str_to_int, 2: self.__str_to_float,
                         3: self.__str_to_float, 4: self.__str_to_str}

        if self.__datatype in DATA_TYPES.keys():
            data_in = datatype_conv[self.__datatype](data_in)
        else:
            raise TypeError('Defined datatype {} for parameter {} is not valid'.format(self.__datatype,
                                                                                       self.__name))

        # Convert list to np.array
        if self.ndims == 2:
            data_np = np.array(data_in).reshape((-1, self.get_dimsize_by_index(1),), order='F')
        elif self.ndims == 1:
            data_np = np.array(data_in)
        else:
            raise ValueError('Number of dimensions, {}, is not supported'.format(self.ndims))

        if 'one' in self.__dimensions.dimensions.keys():
            # A parameter with the dimension 'one' should never have more
            # than 1 value. Output warning if the incoming value is different
            # from a pre-existing value
            if data_np[0] != self.__data[0]:
                print('WARNING: {} with dimension "one" has different '.format(self.__name) +
                      'value ({}) from current ({}). Keeping current value.'.format(data_np[0], self.__data[0]))
        else:
            self.__data = np.concatenate((self.__data, data_np))
            # self.__data = data_np

    def check(self):
        """Verifies the total size of the data for the parameter matches the total declared dimension sizes
        and returns a message """

        # Check a variable to see if the number of values it has is
        # consistent with the given dimensions

        if self.has_correct_size():
            # The number of values for the defined dimensions match
            print('%s: OK' % self.name)
        else:
            print('%s: BAD' % self.name)

    def get_dimsize_by_index(self, index):
        """Return size of dimension at the given index

        :param index: The 0-based position of the dimension.
        :returns: Integer size of the dimension.
        """

        if index < len(self.__dimensions.dimensions.items()):
            return self.__dimensions.dimensions.items()[index][1].size
        raise ValueError('Parameter has no dimension at index {}'.format(index))

    def has_correct_size(self):
        """Verifies the total size of the data for the parameter matches the total declared dimension sizes"""

        # Check a variable to see if the number of values it has is
        # consistent with the given dimensions

        # Get the defined size for each dimension used by the variable
        total_size = 1
        for dd in self.dimensions.keys():
            total_size *= self.dimensions.get(dd).size

        # This assumes a numpy array
        if self.data.size == total_size:
            # The number of values for the defined dimensions match
            return True
        return False

    def tolist(self):
        """Returns the parameter data as a list

        :returns: Parameter data as a list"""
        # Return a list of the data
        return self.__data.ravel(order='F').tolist()

    def toparamdb(self):
        """Outputs parameter data in the paramDb csv format"""
        outstr = '$id,{}\n'.format(self.name)
        for ii, dd in enumerate(self.tolist()):
            outstr += '{},{}\n'.format(ii+1, dd)
        return outstr

    def tostructure(self):
        """Returns a dictionary structure of the parameter. This is typically used for serializing parameters.

        :returns: dictionary structure of the parameter.
        """

        # Return all information about this parameter in the following form
        param = {'name': self.name,
                 'datatype': self.datatype,
                 'dimensions': self.dimensions.tostructure(),
                 'data': self.tolist()}
        return param

    def __str_to_float(self, data):
        """Convert strings to a floats

        :returns: array of floats
        """

        # Convert provide list of data to float
        try:
            return [float(vv) for vv in data]
        except ValueError as ve:
            print(ve)

    def __str_to_int(self, data):
        """Converts strings to integers

        :returns: array of integers
        """

        # Convert list of data to integer
        try:
            return [int(vv) for vv in data]
        except ValueError as ve:
            print(ve)

    def __str_to_str(self, data):
        """Null op for string to string conversion

        :returns: data unchanged"""
        # nop for list of strings
        return data


class Parameters(object):
    """Container of multiple Parameter objects"""
    # Author: Parker Norton (pnorton@usgs.gov)
    # Create date: 2017-05-01
    # Description: Class object to handle reading and writing the PRMS
    #              parameter files which have been generated by Java.

    # TODO: Add basic statistical functions

    def __init__(self):
        """Create an ordered dictionary to contain individual parameter objects"""
        self.__parameters = OrderedDict()
    # END __init__

    def __getattr__(self, name):
        # Undefined attributes will look up the given parameter
        # return self.get(item)
        return getattr(self.__parameters, name)

    def __getitem__(self, item):
        return self.get(item)

    @property
    def parameters(self):
        """Returns an ordered dictionary of parameter names"""
        return self.__parameters

    def add(self, name):
        """Add a new parameter by name

        :param name: A valid PRMS parameter name
        """

        # Add a new parameter
        if self.exists(name):
            raise ParameterError("Parameter already exists")
        self.__parameters[name] = Parameter(name=name)

    def check(self):
        """Check all parameter variables for proper array size"""
        for pp in self.__parameters.values():
            pp.check()

    def remove(self, name):
        """Delete a parameter if it exists

        :param name: The name of the parameter to remove
        """

        if self.exists(name):
            del self.__parameters[name]

    def exists(self, name):
        """Checks if a given parameter name exists

        :param name: The name of the parameter
        :returns: Boolean (True if parameter exists otherwise False
        """

        return name in self.parameters.keys()

    def get(self, name):
        """Returns the given parameter object

        :param name: The name of the parameter
        :returns: Parameter object
        """

        # Return the given parameter
        if self.exists(name):
            return self.__parameters[name]
        raise ValueError('Parameter, {}, does not exist.'.format(name))

    def get_dataframe(self, name):
        """Returns a pandas DataFrame for a parameter. If the parameter dimensions includes
           either nhrus or nsegment then the respective national ids are included as the
           index in the return dataframe.

           :param name: The name of the parameter
           :returns: Pandas DataFrame of the parameter data
           """

        if self.exists(name):
            cparam = self.__parameters[name]
            param_data = cparam.as_dataframe

            if set(cparam.dimensions.keys()).intersection({'nhru', 'ngw', 'nssr'}):
                if name != 'nhm_id':
                    param_id = self.__parameters['nhm_id'].as_dataframe

                    # Create a DataFrame of the parameter
                    param_data = param_data.merge(param_id, left_index=True, right_index=True)
                    param_data.set_index('nhm_id', inplace=True)
                else:
                    param_data = self.__parameters['nhm_id'].as_dataframe
            elif set(cparam.dimensions.keys()).intersection({'nsegment'}):
                param_id = self.__parameters['nhm_seg'].as_dataframe

                # Create a DataFrame of the parameter
                param_data = param_data.merge(param_id, left_index=True, right_index=True)
                param_data.set_index(['nhm_seg'], inplace=True)

            return param_data
        raise ValueError('Parameter, {}, has no associated data'.format(name))

    # def replace_values(self, varname, newvals, newdims=None):
    #     """Replaces all values for a given variable/parameter. Size of old and new arrays/values must match."""
    #     if not self.__isloaded:
    #         self.load_file()
    #
    #     # parent = self.__paramdict['Parameters']
    #     thevar = self.get_var(varname)
    #
    #     # NOTE: Need to figure out whether this function should expect row-major ordering
    #     #       or column-major ordering when called. Right it expects column-major ordering
    #     #       for newvals, which means no re-ordering of the array is necessary when
    #     #       replacing values.
    #     if newdims is None:
    #         # We are not changing dimensions of the variable/parameter, just the values
    #         # Check if size of newvals array matches the oldvals array
    #         if isinstance(newvals, list) and len(newvals) == thevar['values'].size:
    #             # Size of arrays match so replace the oldvals with the newvals
    #             # Lookup dimension size for each dimension name
    #             arr_shp = [self.__paramdict['Dimensions'][dd] for dd in thevar['dimnames']]
    #
    #             thevar['values'][:] = np.array(newvals).reshape(arr_shp)
    #         elif isinstance(newvals, np.ndarray) and newvals.size == thevar['values'].size:
    #             # newvals is a numpy ndarray
    #             # Size of arrays match so replace the oldvals with the newvals
    #             # Lookup dimension size for each dimension name
    #             arr_shp = [self.__paramdict['Dimensions'][dd] for dd in thevar['dimnames']]
    #
    #             thevar['values'][:] = newvals.reshape(arr_shp)
    #         # NOTE: removed the following because even scalars should be stored as numpy array
    #         # elif thevar['values'].size == 1:
    #         #     # This is a scalar value
    #         #     if isinstance(newvals, float):
    #         #         thevar['values'] = [newvals]
    #         #     elif isinstance(newvals, int):
    #         #         thevar['values'] = [newvals]
    #         else:
    #             print("ERROR: Size of oldval array and size of newval array don't match")
    #     else:
    #         # The dimensions are being changed and new values provided
    #
    #         # Use the dimension sizes from the parameter file to check the size
    #         # of the newvals array. If the size of the newvals array doesn't match the
    #         # parameter file's dimensions sizes we have a problem.
    #         size_check = 1
    #         for dd in newdims:
    #             size_check *= self.get_dim(dd)
    #
    #         if isinstance(newvals, list) and len(newvals) == size_check:
    #             # Size of arrays match so replace the oldvals with the newvals
    #             thevar['values'] = newvals
    #             thevar['dimnames'] = newdims
    #         elif isinstance(newvals, np.ndarray) and newvals.size == size_check:
    #             # newvals is a numpy ndarray
    #             # Size of arrays match so replace the oldvals with the newvals
    #             thevar['values'] = newvals
    #             thevar['dimnames'] = newdims
    #         elif thevar['values'].size == 1:
    #             # This is a scalar value
    #             thevar['dimnames'] = newdims
    #             if isinstance(newvals, float):
    #                 thevar['values'] = [newvals]
    #             elif isinstance(newvals, int):
    #                 thevar['values'] = [newvals]
    #         else:
    #             print("ERROR: Size of newval array doesn't match dimensions in parameter file")
    #
    # def resize_dim(self, dimname, newsize):
    #     """Changes the size of the given dimension.
    #        This does *not* check validity of parameters that use the dimension.
    #        Check variable integrity before writing parameter file."""
    #
    #     # Some dimensions are related to each other.
    #     related_dims = {'ndepl': 'ndeplval', 'nhru': ['nssr', 'ngw'],
    #                     'nssr': ['nhru', 'ngw'], 'ngw': ['nhru', 'nssr']}
    #
    #     if not self.__isloaded:
    #         self.load_file()
    #
    #     parent = self.__paramdict['Dimensions']
    #
    #     if dimname in parent:
    #         parent[dimname] = newsize
    #
    #         # Also update related dimensions
    #         if dimname in related_dims:
    #             if dimname == 'ndepl':
    #                 parent[related_dims[dimname]] = parent[dimname] * 11
    #             elif dimname in ['nhru', 'nssr', 'ngw']:
    #                 for dd in related_dims[dimname]:
    #                     parent[dd] = parent[dimname]
    #         return True
    #     else:
    #         return False
    #
    # def update_values_by_hru(self, varname, newvals, hru_index):
    #     """Updates parameter/variable with new values for a a given HRU.
    #        This is used when merging data from an individual HRU into a region"""
    #     if not self.__isloaded:
    #         self.load_file()
    #
    #     # parent = self.__paramdict['Parameters']
    #     thevar = self.get_var(varname)
    #
    #     if len(newvals) == 1:
    #         thevar['values'][(hru_index - 1)] = newvals
    #     elif len(newvals) == 2:
    #         thevar['values'][(hru_index - 1), :] = newvals
    #     elif len(newvals) == 3:
    #         thevar['values'][(hru_index - 1), :, :] = newvals

# ***** END of class parameters()

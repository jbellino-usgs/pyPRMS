import io
import pkgutil
import numpy as np
import pandas as pd
from collections import OrderedDict
import xml.etree.ElementTree as xmlET

from .Exceptions_custom import ParameterError, ConcatError
from .constants import DATA_TYPES, NHM_DATATYPES
from .dimbase import ParamDimensions

from .util_dict import PrmsDict


class Parameter(object):

    """Container for a single Parameter object.

    A parameter has a name, datatype, optional units, one or more dimensions, and
    associated data.
    """

    # Container for a single parameter
    def __init__(self, name=None, datatype=None, units=None, model=None, description=None,
                 help=None, modules=None, minimum=None, maximum=None, default=None):
        """Initialize the Parameter object.

        :param str name: A valid PRMS parameter name
        :param int datatype: The datatype for the parameter (1-Integer, 2-Float, 3-Double, 4-String)
        :param str units: Option units string for the parameter
        :param str model: <<FILL IN LATER>>
        :param str description: Description of the parameter
        :param str help: Help text for the parameter
        :param modules: List of modules that require the parameter
        :type modules: list[str] or None
        :param minimum: Minimum value allowed in the parameter data
        :type minimum: int or float or None
        :param maximum: Maximum value allowed in the parameter data
        :type maximum: int or float or None
        :param default: Default value used for parameter data
        :type default: int or float or None
        """

        # Set the parameter name
        self.__name = name

        # Initialize internal variables
        self.__datatype = None
        self.__units = None
        self.__model = None
        self.__description = None
        self.__help = None
        self.__modules = None
        self.__minimum = None
        self.__maximum = None
        self.__default = None

        self.__dimensions = ParamDimensions()
        self.__data = None  # array

        # Use setters for most internal variables
        self.datatype = datatype
        self.units = units
        self.model = model
        self.description = description
        self.help = help
        self.modules = modules
        self.minimum = minimum
        self.maximum = maximum
        self.default = default

    def __str__(self):
        """Pretty-print string representation of the parameter information.

        :return: Parameter information
        :rtype: str
        """
        out_text = 'name: {}\ndatatype: {}\nunits: {}\nndims: {}\ndescription: {}\nhelp: {}\n'
        outstr = out_text.format(self.name, self.datatype, self.units, self.ndims, self.description,
                                 self.help)

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
        """Returns the parameter data as a pandas DataFrame."""

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
        """Returns the parameter name."""
        return self.__name

    @property
    def datatype(self):
        """Returns the datatype of the parameter.

        :rtype: int"""
        return self.__datatype

    @datatype.setter
    def datatype(self, dtype):
        """Sets the datatype for the parameter.

        :param int dtype: The datatype for the parameter (1-Integer, 2-Float, 3-Double, 4-String)
        """

        # TODO: Should this be able to handle both string (e.g. 'I') and integer datatypes?
        # TODO: If datatype is changed should verify existing data can be cast to it
        if dtype in DATA_TYPES:
            self.__datatype = dtype
        elif dtype is None:
            self.__datatype = None
        else:
            # TODO: This should raise and error (what kind?)
            print('WARNING: Datatype, {}, is not valid.'.format(dtype))

    @property
    def units(self):
        """Returns the parameter units.

        :rtype: str
        """
        return self.__units

    @units.setter
    def units(self, unitstr):
        """Set the parameter units.

        :param str unitstr: String denoting the units for the parameter (e.g. mm)
        """
        self.__units = unitstr

    @property
    def model(self):
        """Returns the model the parameter is used in.

        :rtype: str
        """
        return self.__model

    @model.setter
    def model(self, modelstr):
        """Set the model description for the parameter.

        :param str modelstr: String denoting the model (e.g. PRMS)
        """
        self.__model = modelstr

    @property
    def description(self):
        """Returns the parameter description.

        :rtype: str
        """
        return self.__description

    @description.setter
    def description(self, descstr):
        """Set the model description for the parameter.

        :param str descstr: Description string
        """
        self.__description = descstr

    @property
    def help(self):
        """Returns the help information for the parameter.

        :rtype: str
        """
        return self.__help

    @help.setter
    def help(self, helpstr):
        """Set the help string for the parameter.

        :param str helpstr: Help string
        """
        self.__help = helpstr

    @property
    def minimum(self):
        """Returns the minimum valid value for the parameter.

        :rtype: int or float or None
        """
        return self.__minimum

    @minimum.setter
    def minimum(self, value):
        """Set the minimum valid value for the parameter.

        :param value: The minimum value
        :type value: int or float or None
        """
        if self.__datatype is None or value is None:
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
        """Returns the maximum valid value for the parameter.

        :rtype: int or float or None
        """
        return self.__maximum

    @maximum.setter
    def maximum(self, value):
        """Set the maximum valid value for the parameter.

        :param value: The maximum value
        :type value: int or float or None
        """
        if self.__datatype is None or value is None:
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
        """Returns the default value for the parameter.

        :rtype: int or float or None
        """
        return self.__default

    @default.setter
    def default(self, value):
        """Set the default value for the parameter.

        :param value: The default value
        :type value: int or float or None
        """
        if self.__datatype is None or value is None:
            self.__default = value
        elif DATA_TYPES[self.__datatype] == 'float':
            self.__default = float(value)
        elif DATA_TYPES[self.__datatype] == 'integer':
            self.__default = int(value)
        else:
            self.__default = value

    @property
    def modules(self):
        """Returns the names of the modules require the parameter.

        :rtype: list[str] or None
        """
        return self.__modules

    @modules.setter
    def modules(self, modulestr):
        """Set the names of the modules that require the parameter.

        :param modulestr: Single module name or list of module names to add
        :type modulestr: list[str] or str or None
        """
        if modulestr is not None:
            if isinstance(modulestr, list):
                self.__modules = modulestr
            else:
                self.__modules = [modulestr]
        else:
            self.__modules = None

    @property
    def dimensions(self):
        """Returns the Dimensions object associated with the parameter."""
        return self.__dimensions

    @property
    def ndims(self):
        """Returns the number of dimensions that are defined for the parameter.

        :rtype: int"""
        return self.__dimensions.ndims

    @property
    def data(self):
        """Returns the data associated with the parameter.

        :rtype: np.ndarray
        """
        if self.__data is not None:
            return self.__data
        raise ValueError('Parameter, {}, has no data'.format(self.__name))

    @data.setter
    def data(self, data_in):
        """Sets the data for the parameter.

        :param list data_in: A list containing the parameter data
        :raises TypeError: if the datatype for the parameter is invalid
        :raises ValueError: if the number of dimensions for the parameter is greater than 2
        """
        # Raise an error if no dimensions are defined for parameter
        if not self.ndims:
            raise ValueError('No dimensions have been defined for {}. Unable to append data'.format(self.name))

        if isinstance(data_in, list):
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
                data_np = np.array(data_in).reshape((-1, self.__dimensions.get_dimsize_by_index(1),), order='F')
                # data_np = np.array(data_in).reshape((-1, self.__dimensions.get_dimsize_by_index(1),), order='F')
            elif self.ndims == 1:
                data_np = np.array(data_in)
            else:
                raise ValueError('Number of dimensions, {}, is not supported'.format(self.ndims))

            # Replace data
            # self.__data = data_np

            if 'one' in self.__dimensions.keys():
                # A parameter with the dimension 'one' should never have more
                # than 1 value. Output warning if the incoming value is different
                # from a pre-existing value
                if data_np.size > 1:
                    print('WARNING: {} with dimension "one" has {} values. Using first value only.'.format(self.__name, data_np.size))
                self.__data = np.array(data_np[0], ndmin=1)
                # self.__data = data_np[0]
            else:
                self.__data = data_np

        elif isinstance(data_in, np.ndarray):
            if data_in.ndim == self.ndims:
                self.__data = data_in
            else:
                err_txt = 'Number of dimensions for new data ({}) doesn\'t match old ({})'
                raise IndexError(err_txt.format(data_in.ndim, self.ndims))

    @property
    def index_map(self):
        """Returns an ordered dictionary which maps data values to index position"""
        return OrderedDict((val, idx) for idx, val in enumerate(self.__data.tolist()))

    @property
    def xml(self):
        """Return the xml metadata for the parameter as an xml Element.

        :rtype: xmlET.Element
        """
        param_root = xmlET.Element('parameter')
        param_root.set('name', self.name)
        param_root.set('version', 'ver')
        param_root.append(self.dimensions.xml)
        return param_root

    def concat(self, data_in):
        """Takes a list of parameter data and concatenates it to the end of the existing parameter data.

        This is useful when reading 2D parameter data by region where
        the ordering of the data must be correctly maintained in the final
        dataset

        :param list data_in: Data to concatenate (or append) to existing parameter data
        :raises TypeError: if the datatype for the parameter is invalid
        :raises ValueError: if the number of dimensions for the parameter is greater than 2
        :raises ConcatError: if concatenation is attempted with a parameter of dimension 'one' (e.g. scalar)
        """

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
            data_np = np.array(data_in).reshape((-1, self.dimensions.get_dimsize_by_index(1),), order='F')
        elif self.ndims == 1:
            data_np = np.array(data_in)
        else:
            raise ValueError('Number of dimensions, {}, is not supported'.format(self.ndims))

        if 'one' in self.__dimensions.dimensions.keys():
            # A parameter with the dimension 'one' should never have more
            # than 1 value. Output warning if the incoming value is different
            # from a pre-existing value
            if data_np[0] != self.__data[0]:
                raise ConcatError('Parameter, {}, with dimension "one" already '.format(self.__name) +
                                  'has assigned value = {}; '.format(self.__data[0]) +
                                  'Cannot concatenate additional value(s), {}'.format(data_np[0]))
                # print('WARNING: {} with dimension "one" has different '.format(self.__name) +
                #       'value ({}) from current ({}). Keeping current value.'.format(data_np[0], self.__data[0]))
        else:
            self.__data = np.concatenate((self.__data, data_np))
            # self.__data = data_np

    def check(self):
        """Verifies the total size of the data for the parameter matches the total declared dimension(s) size
        and returns a message.

        :rtype: str
        """

        # TODO: check that values are between min and max values
        # Check a variable to see if the number of values it has is
        # consistent with the given dimensions
        if self.has_correct_size():
            # The number of values for the defined dimensions match
            return '{}: OK'.format(self.name)
        else:
            return '{}: BAD'.format(self.name)

    def check_values(self):
        """Returns true if all data values are within the min/max values for the parameter."""
        if self.__minimum is not None and self.__maximum is not None:
            # Check both ends of the range
            if not(isinstance(self.__minimum, str) or isinstance(self.__maximum, str)):
                return (self.__data >= self.__minimum).all() and (self.__data <= self.__maximum).all()
        return True

    def has_correct_size(self):
        """Verifies the total size of the data for the parameter matches the total declared dimension(s) sizes.

        :rtype: bool"""

        # Check a variable to see if the number of values it has is
        # consistent with the given dimensions

        # Get the defined size for each dimension used by the variable
        total_size = 1
        for dd in self.dimensions.keys():
            total_size *= self.dimensions.get(dd).size

        # This assumes a numpy array
        return self.data.size == total_size

    def remove_by_index(self, dim_name, indices):
        """Remove columns (nhru or nsegment) from data array given a list of indices"""

        if isinstance(indices, type(OrderedDict().values())):
            indices = list(indices)

        if self.__data.size == 1:
            print('{}: Cannot reduce array of size one'.format(self.name))
            return

        self.__data = np.delete(self.__data, indices, axis=self.dimensions.get_position(dim_name))
        self.dimensions[dim_name].size = self.__data.shape[self.dimensions.get_position(dim_name)]

    def reshape(self, new_dims):
        """Reshape a parameter, broadcasting existing values as necessary.

        :param collections.OrderedDict new_dims: Dimension names and sizes that will be used to reshape the parameter data
        """

        if self.dimensions.ndims == 1:
            if 'one' in self.dimensions.keys():
                # Reshaping from a scalar to a 1D or 2D array
                # print('Scalar to 1D or 2D')
                new_sizes = [vv.size for vv in new_dims.values()]
                tmp_data = np.broadcast_to(self.__data, new_sizes)

                # Remove the original dimension
                self.dimensions.remove('one')

                # Add the new ones
                for kk, vv in iter(new_dims.items()):
                    self.dimensions.add(kk, vv.size)

                self.__data = tmp_data
            elif set(self.dimensions.keys()).issubset(set(new_dims.keys())):
                # Reschaping a 1D to a 2D
                if len(new_dims) == 1:
                    print('ERROR: Cannot reshape from 1D array to 1D array')
                else:
                    # print('1D array to 2D array')
                    new_sizes = [vv.size for vv in new_dims.values()]
                    try:
                        tmp_data = np.broadcast_to(self.__data, new_sizes)
                    except ValueError:
                        # operands could not be broadcast together with remapped shapes
                        tmp_data = np.broadcast_to(self.__data, new_sizes[::-1]).T

                    old_dim = list(self.dimensions.keys())[0]
                    self.dimensions.remove(old_dim)

                    for kk, vv in iter(new_dims.items()):
                        self.dimensions.add(kk, vv.size)

                    self.__data = tmp_data

    def subset_by_index(self, dim_name, indices):
        """Reduce columns (nhru or nsegment) from data array given a list of indices"""

        if isinstance(indices, type(OrderedDict().values())):
            indices = list(indices)

        if self.__data.size == 1:
            print('{}: Cannot reduce array of size one'.format(self.name))
            return

        self.__data = self.__data[indices]
        self.dimensions[dim_name].size = self.__data.shape[self.dimensions.get_position(dim_name)]
        # self.__data = np.take(self.__data, indices, axis=0)
        # self.__data = np.delete(self.__data, indices, axis=self.dimensions.get_position(dim_name))

    def tolist(self):
        """Returns the parameter data as a list.

        :returns: Parameter data
        :rtype: list
        """

        # TODO: is this correct for snarea_curve?
        # Return a list of the data
        return self.__data.ravel(order='F').tolist()

    def toparamdb(self):
        """Outputs parameter data in the paramDb csv format.

        :rtype: str
        """

        outstr = '$id,{}\n'.format(self.name)
        for ii, dd in enumerate(self.tolist()):
            outstr += '{},{}\n'.format(ii+1, dd)
        return outstr

    def tostructure(self):
        """Returns a dictionary structure of the parameter.

        This is typically used for serializing parameters.

        :returns: dictionary structure of the parameter
        :rtype: dict
        """

        # Return all information about this parameter in the following form
        param = {'name': self.name,
                 'datatype': self.datatype,
                 'dimensions': self.dimensions.tostructure(),
                 'data': self.tolist()}
        return param

    def unique(self):
        """Create array of unique values from the parameter data.

        :returns: Array of unique values
        :rtype: np.ndarray
        """
        return np.unique(self.__data)

    @staticmethod
    def __str_to_float(data):
        """Convert strings to a floats.

        :param list[str] data: list of data

        :returns: array of floats
        :rtype: list[float]
        """

        # Convert provide list of data to float
        try:
            return [float(vv) for vv in data]
        except ValueError as ve:
            print(ve)

    @staticmethod
    def __str_to_int(data):
        """Converts strings to integers.

        :param list[str] data: list of data

        :returns: array of integers
        :rtype: list[int]
        """

        # Convert list of data to integer
        try:
            return [int(vv) for vv in data]
        except ValueError as ve:
            # Perhaps it's a float, try converting to float and then integer
            try:
                tmp = [float(vv) for vv in data]
                return [int(vv) for vv in tmp]
            except ValueError as ve:
                print(ve)

    @staticmethod
    def __str_to_str(data):
        """Null op for string-to-string conversion.

        :param list[str] data: list of data

        :returns: unmodified array of data
        :rtype: list[str]
        """

        # nop for list of strings
        # 2019-05-22 PAN: For python 3 force string type to byte
        #                 otherwise they are treated as unicode
        #                 which breaks the write_netcdf() routine.
        # 2019-06-26 PAN: Removed the encode because it broken writing the ASCII
        #                 parameter files. Instead the conversion to ascii is
        #                 handled in the write_netcdf routine of ParameterSet
        # data = [dd.encode() for dd in data]
        return data


class ParameterDict(PrmsDict):
    """
    An Odict-like object that holds pyPRMS.Parameter objects with the
    ability to add and remove parameter objects.

    *** This class would replace the ParameterSet class. It would allow for
    more straightforward access to the underlying parameters. A call to the
    "parameters" attribute of a ParameterFile would return the ParameterDict
    object which can be queried directly instead of having to call the
    "parameters" attribute of the ParameterSet object to return the
    underlying Odict of parameters. Additional functionality would allow for
    calling of parameters as attributes using the ."parameter name"
    notation.***

    Example
    -------
    >>> from pyPRMS.parfile import ParameterFile
    >>> pf = ParameterFile('param.param')
    >>> pf.parameters['hru_slope']
    >>> pf.parameters.hru_slope.data[:20]

    """

    def __init__(self, verify=True):

        super().__init__(data=[])

        self.__master_params = None
        if verify:
            self.__master_params = ValidParams()

    @property
    def master_parameters(self):
        return self.__master_params

    def add(self, name, datatype=None, units=None, model=None, description=None,
            help=None, modules=None, minimum=None, maximum=None, default=None,
            info=None):
        """Add a new parameter by name.

        :param str name: A valid PRMS parameter name
        :param int datatype: The datatype for the parameter (1-Integer, 2-Float, 3-Double, 4-String)
        :param str units: Option units string for the parameter
        :param str model: <<FILL IN LATER>>
        :param str description: Description of the parameter
        :param str help: Help text for the parameter
        :param modules: List of modules that require the parameter
        :type modules: list[str] or None
        :param minimum: Minimum value allowed in the parameter data
        :type minimum: int or float or None
        :param maximum: Maximum value allowed in the parameter data
        :type maximum: int or float or None
        :param default: Default value used for parameter data
        :type default: int or float or None
        :param info: Parameter object containing the metadata information for the parameter
        :type info: Parameter

        :raises ParameterError: if parameter already exists or name is None
        """

        # Add a new parameter
        if self.exists(name):
            raise ParameterError("Parameter already exists")
        elif name is None:
            raise ParameterError("None is not a valid parameter name")

        if isinstance(info, Parameter):
            param = Parameter(name=name,
                              datatype=info.datatype,
                              units=info.units,
                              model=info.model,
                              description=info.description,
                              help=info.help,
                              modules=info.modules,
                              minimum=info.minimum,
                              maximum=info.maximum,
                              default=info.default)
        else:
            param = Parameter(name=name,
                              datatype=datatype,
                              units=units,
                              model=model,
                              description=description,
                              help=help,
                              modules=modules,
                              minimum=minimum,
                              maximum=maximum,
                              default=default)

        self.__setitem__(name, param)
        self.__dict__[name] = param

    def check(self):
        """Check all parameter variables for proper array size.
        """

        # for pp in self.__parameters.values():
        for pk in sorted(list(self.keys())):
            pp = self.__getitem__(pk)

            print(pp.check())

            if not pp.check_values():
                print('    WARNING: Value(s) (range: {}, {}) outside the valid range of ({}, {})'.format(pp.data.min(), pp.data.max(), pp.minimum, pp.maximum))

            if pp.name == 'snarea_curve':
                if pp.as_dataframe.values.reshape((-1, 11)).shape[0] != \
                        self.__getitem__('hru_deplcrv').unique().size:
                    print('  WARNING: snarea_curve has more entries than needed by hru_deplcrv')

    def remove(self, name):
        """Delete one or more parameters if they exist.

        :param name: parameter or list of parameters to remove
        :type name: str or list[str]
        """

        if isinstance(name, list):
            # Remove multiple parameters
            for cparam in name:
                if self.exists(cparam):
                    self.__delitem__(cparam)
            pass
        else:
            if self.exists(name):
                self.__delitem__(name)

    def exists(self, name):
        """Checks if a given parameter name exists.

        :param str name: Name of the parameter
        :returns: True if parameter exists, otherwise False
        :rtype: bool
        """

        return name in self.keys()

    def get(self, name):
        """Returns the given parameter object.

        :param str name: The name of the parameter
        :returns: Parameter object
        :rtype: Parameter
        """

        # Return the given parameter
        if self.exists(name):
            return self.__getitem__(name)
        raise ValueError('Parameter, {}, does not exist.'.format(name))

    def get_dataframe(self, name):
        """Returns a pandas DataFrame for a parameter.

        If the parameter dimensions includes either nhrus or nsegment then the
        respective national ids are included, if they exist, as the index in the
        returned dataframe.

        :param str name: The name of the parameter
        :returns: Pandas DataFrame of the parameter data
        :rtype: pd.DataFrame
        """

        if self.exists(name):
            cparam = self.__getitem__(name)
            param_data = cparam.as_dataframe

            if set(cparam.dimensions.keys()).intersection({'nhru', 'ngw', 'nssr'}):
                if name != 'nhm_id':
                    try:
                        param_id = self.__getitem__('nhm_id').as_dataframe

                        # Create a DataFrame of the parameter
                        param_data = param_data.merge(param_id, left_index=True, right_index=True)
                        param_data.set_index('nhm_id', inplace=True)
                    except KeyError:
                        # If there is no nhm_id parameter then just return the
                        # requested parameter by itself
                        param_data.rename(index={k: k + 1 for k in param_data.index},
                                          inplace=True)
                        param_data.index.name = 'hru'
                else:
                    param_data = self.__getitem__('nhm_id').as_dataframe
            elif set(cparam.dimensions.keys()).intersection({'nsegment'}):
                param_id = self.__getitem__('nhm_seg').as_dataframe

                # Create a DataFrame of the parameter
                param_data = param_data.merge(param_id, left_index=True, right_index=True)
                param_data.set_index(['nhm_seg'], inplace=True)
            elif name == 'snarea_curve':
                # Special handling for snarea_curve parameter
                param_data = pd.DataFrame(cparam.as_dataframe.values.reshape((-1, 11)))
                param_data.rename(columns={k: k+1 for k in param_data.columns},
                                  index={k: k+1 for k in param_data.index},
                                  inplace=True)
                param_data.index.name = 'curve_index'
            return param_data
        raise ValueError('Parameter, {}, has no associated data'.format(name))

    def get_subset(self, name, global_ids):
        """Returns a subset for a parameter based on the global_ids (e.g. nhm)"""
        param = self.__getitem__(name)
        dim_set = set(param.dimensions.keys()).intersection({'nhru', 'nssr', 'ngw', 'nsegment'})
        id_index_map = {}
        cdim = dim_set.pop()

        if cdim in ['nhru', 'nssr', 'ngw']:
            # Global IDs should be in the range of nhm_id
            id_index_map = self.__getitem__('nhm_id').index_map
        elif cdim in ['nsegment']:
            # Global IDs should be in the range of nhm_seg
            id_index_map = self.__getitem__('nhm_seg').index_map

        # Zero-based indices in order of global_ids
        nhm_idx0 = []
        for kk in global_ids:
            nhm_idx0.append(id_index_map[kk])

        if param.dimensions.ndims == 2:
            return param.data[tuple(nhm_idx0), :]
        else:
            return param.data[tuple(nhm_idx0), ]

    def remove_by_global_id(self, hrus=None, segs=None):
        """Removes data-by-id (nhm_seg, nhm_id) from all parameters"""

        if segs is not None:
            pass

        if hrus is not None:
            # Map original nhm_id to their index
            nhm_idx = OrderedDict((hid, ii) for ii, hid in enumerate(self.get('nhm_id').data.tolist()))
            nhm_seg = self.get('nhm_seg').tolist()

            print(list(nhm_idx.keys())[0:10])

            for xx in list(nhm_idx.keys()):
                if xx in hrus:
                    del nhm_idx[xx]

            print('-'*40)
            print(list(nhm_idx.keys())[0:10])
            print(list(nhm_idx.values())[0:10])

            # [hru_segment_nhm[yy] for yy in nhm_idx.values()]
            self.get('nhm_id').subset_by_index('nhru', nhm_idx.values())

            # Update hru_segment_nhm then go back and make sure the referenced nhm_segs are valid
            self.get('hru_segment_nhm').subset_by_index('nhru', nhm_idx.values())
            self.get('hru_segment_nhm').data = [kk if kk in nhm_seg else 0 if kk == 0 else -1
                                                for kk in self.get('hru_segment_nhm').data.tolist()]

            # Now do the local hru_segment
            self.get('hru_segment').subset_by_index('nhru', nhm_idx.values())
            self.get('hru_segment').data = [nhm_seg.index(kk)+1 if kk in nhm_seg else 0 if kk == 0 else -1
                                            for kk in self.get('hru_segment_nhm').data.tolist()]

            # # First remove the HRUs from nhm_id and hru_segment_nhm
            # id_to_seg = np.column_stack((self.get('nhm_id').data, self.get('hru_segment_nhm').data))
            #
            # # Create ordered dictionary to reindex hru_segment
            # nhm_id_to_hru_segment_nhm = OrderedDict((nhm, hseg) for nhm, hseg in id_to_seg)
            #
            # nhm_seg = self.get('nhm_seg').data.tolist()
            #
            # self.get('nhm_id').data = [xx for xx in nhm_id_to_hru_segment_nhm.keys()]
            # # self.get('nhm_id').remove_by_index('nhru', hrus)
            #
            # self.get('hru_segment_nhm').data = [kk if kk in nhm_seg else 0 if kk == 0 else -1
            #                                     for kk in nhm_id_to_hru_segment_nhm.values()]
            #
            # self.get('hru_segment').data = [nhm_seg.index(kk)+1 if kk in nhm_seg else 0 if kk == 0 else -1
            #                                 for kk in nhm_id_to_hru_segment_nhm.values()]

            for pp in self.values():
                if pp.name not in ['nhm_id', 'hru_segment_nhm', 'hru_segment']:
                    dim_set = set(pp.dimensions.keys()).intersection({'nhru', 'nssr', 'ngw'})

                    if bool(dim_set):
                        if len(dim_set) > 1:
                            raise ValueError('dim_set > 1 for {}'.format(pp.name))
                        else:
                            cdim = dim_set.pop()
                            pp.subset_by_index(cdim, nhm_idx.values())

                            if pp.name == 'hru_deplcrv':
                                # Save the list of snow indices for reducing the snarea_curve later
                                uniq_deplcrv_idx = list(set(pp.data.tolist()))
                                uniq_dict = {}
                                for ii, xx in enumerate(uniq_deplcrv_idx):
                                    uniq_dict[xx] = ii + 1

                                uniq_deplcrv_idx0 = [xx - 1 for xx in uniq_deplcrv_idx]

                                # Renumber the hru_deplcrv indices
                                data_copy = pp.data.copy()
                                with np.nditer(data_copy, op_flags=['readwrite']) as it:
                                    for xx in it:
                                        xx[...] = uniq_dict[int(xx)]

                                pp.data = data_copy

                                tmp = self.__getitem__(
                                    'snarea_curve').data.reshape((-1, 11))[tuple(uniq_deplcrv_idx0), :]

                                self.__getitem__('snarea_curve').data = \
                                    tmp.ravel()

                                self.__getitem__('snarea_curve').dimensions[
                                    'ndeplval'].size = tmp.size

            # Need to reduce the snarea_curve array to match the number of indices in hru_deplcrv
            # new_deplcrv = pp['hru_deplcrv'].data.tolist()


class ValidParams(PrmsDict):

    """Object containing master list of parameters."""

    # Author: Parker Norton (pnorton@usgs.gov)
    # Create date: 2019-04

    def __init__(self, filename=None):
        """Create ValidParams object.

        Read an XML file of parameters to use as a master of valid PRMS
        parameters. If no filename is specified an internal library XML file
        is read.

        :param filename: name of XML parameter file
        :type filename: str or None
        """
        super(ValidParams, self).__init__()
        print('Initializing valid parameters')

        self.__filename = filename

        if filename:
            self.__xml_tree = xmlET.parse(self.__filename)
        else:
            # Use the package file, parameters.xml, by default
            xml_fh = io.StringIO(
                pkgutil.get_data('pyPRMS',
                                 'xml/parameters.xml').decode('utf-8'))
            self.__xml_tree = xmlET.parse(xml_fh)

        # TODO: need more robust logic here; currently no way to handle
        #  failures
        self.__isloaded = False
        print('Reading xml')
        self._read()
        self.__isloaded = True
        print('Initialization complete')

    @property
    def filename(self):
        """Get XML filename.

        Returned filename is None if reading from the library-internal XML
        file.

        :returns: name of XML file
        :rtype: str or None
        """

        return self.__filename

    @filename.setter
    def filename(self, filename=None):
        """Set the XML file name.

        If no filename is specified an library-internal XML file is read.

        :param filename: name of XML parameter file
        :type filename: str or None
        """

        self.__filename = filename

        if filename is not None:
            self.__xml_tree = xmlET.parse(self.__filename)
        else:
            # Use the package parameters.xml by default
            xml_fh = io.StringIO(
                pkgutil.get_data('pyPRMS',
                                 'xml/parameters.xml').decode('utf-8'))
            self.__xml_tree = xmlET.parse(xml_fh)

        self.__isloaded = False
        self._read()
        self.__isloaded = True

    def add(self, name, datatype=None, units=None, model=None, description=None,
            help=None, modules=None, minimum=None, maximum=None, default=None,
            info=None):
        """Add a new parameter by name.

        :param str name: A valid PRMS parameter name
        :param int datatype: The datatype for the parameter (1-Integer, 2-Float, 3-Double, 4-String)
        :param str units: Option units string for the parameter
        :param str model: <<FILL IN LATER>>
        :param str description: Description of the parameter
        :param str help: Help text for the parameter
        :param modules: List of modules that require the parameter
        :type modules: list[str] or None
        :param minimum: Minimum value allowed in the parameter data
        :type minimum: int or float or None
        :param maximum: Maximum value allowed in the parameter data
        :type maximum: int or float or None
        :param default: Default value used for parameter data
        :type default: int or float or None
        :param info: Parameter object containing the metadata information for the parameter
        :type info: Parameter

        :raises ParameterError: if parameter already exists or name is None
        """

        # Add a new parameter
        if self.exists(name):
            raise ParameterError("Parameter already exists")
        elif name is None:
            raise ParameterError("None is not a valid parameter name")

        if isinstance(info, Parameter):
            param = Parameter(name=name,
                              datatype=info.datatype,
                              units=info.units,
                              model=info.model,
                              description=info.description,
                              help=info.help,
                              modules=info.modules,
                              minimum=info.minimum,
                              maximum=info.maximum,
                              default=info.default)
        else:
            param = Parameter(name=name,
                              datatype=datatype,
                              units=units,
                              model=model,
                              description=description,
                              help=help,
                              modules=modules,
                              minimum=minimum,
                              maximum=maximum,
                              default=default)

        self.__setitem__(name, param)
        self.__dict__[name] = param

    def exists(self, name):
        """Checks if a given parameter name exists.

        :param str name: Name of the parameter
        :returns: True if parameter exists, otherwise False
        :rtype: bool
        """

        return name in self.keys()

    def get_params_for_modules(self, modules):
        """Get list of unique parameters required for a given list of modules.

        :param list[str] modules: list of PRMS modules

        :returns: set of parameter names
        :rtype: set[str]
        """

        params_by_module = []

        for xx in self.values():
            for mm in xx.modules:
                if mm in modules:
                    params_by_module.append(xx.name)
        return set(params_by_module)

    def _read(self):
        """Read an XML parameter file.

        The resulting Parameters object will have parameters that have no data.
        """

        xml_root = self.__xml_tree.getroot()

        # Iterate over child nodes of root
        for elem in xml_root.findall('parameter'):
            # print(elem.attrib.get('name'))
            name = elem.attrib.get('name')
            dtype = elem.find('type').text
            # print(name)
            try:
                self.add(name)

                self.__getitem__(name).datatype = NHM_DATATYPES[dtype]
                self.__getitem__(name).description = elem.find('desc').text
                self.__getitem__(name).units = elem.find('units').text

                try:
                    self.__getitem__(name).minimum = elem.find('minimum').text
                except AttributeError:
                    pass

                try:
                    self.__getitem__(name).maximum = elem.find('maximum').text
                except AttributeError:
                    pass

                try:
                    self.__getitem__(name).default = elem.find('default').text
                except AttributeError:
                    # Parameter has no default value
                    pass

                # Add dimensions for current parameter
                for cdim in elem.findall('./dimensions/dimension'):
                    try:
                        self.__getitem__(name).dimensions.add(
                            cdim.attrib.get('name'),
                            size=int(cdim.find('default').text))
                    except AttributeError:
                        # Dimension has no default value
                        self.__getitem__(name).\
                            dimensions.add(cdim.attrib.get('name'))

                mods = []
                for cmod in elem.findall('./modules/module'):
                    mods.append(cmod.text)

                self.__getitem__(name).modules = mods
            except ParameterError:
                # Parameter exists add any new attribute information
                pass
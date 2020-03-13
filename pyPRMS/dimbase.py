import xml.etree.ElementTree as xmlET

from .constants import DIMENSION_NAMES
from .prms_helpers import read_xml
from .util_dict import PrmsDict


def _valid_dimension_name(name):
    """Check if given dimension name is valid for PRMS.

    :param str name: dimension name
    :returns: True if dimension name is valid otherwise False
    :rtype: bool
    """

    return name in DIMENSION_NAMES


class Dimension(object):

    """Defines a single dimension."""

    def __init__(self, name=None, size=0, description=None):
        """Create a new dimension object.

        A dimension has a name and a size associated with it.

        :param str name: The name of the dimension
        :param int size: The size of the dimension
        :param description: Description of the dimension
        :type description: str or None
        """

        self.__name = None
        self.__size = None
        self.__description = None
        self.name = name
        self.size = size
        self.description = description

    @property
    def name(self):
        """Name of the dimension.

        :returns: Name of the dimension
        :rtype: str
        """

        return self.__name

    @name.setter
    def name(self, name):
        """Sets the name of the dimension.

        :param str name: Name of the dimension
        :raises ValueError: if dimension name is not a valid PRMS dimension
        """

        if _valid_dimension_name(name):
            self.__name = name
        else:
            # TODO: Should this raise an error?
            raise ValueError('Dimension name, {}, is not a valid PRMS dimension name'.format(name))

    @property
    def size(self):
        """Size of the dimension.

        :returns: size of the dimension
        :rtype: int
        """

        return self.__size

    @size.setter
    def size(self, value):
        """Set the size of the dimension.

        :param int value: size of the dimension
        :raises ValueError: if dimension size in not a positive integer
        """
        if not isinstance(value, int) or value < 0:
            raise ValueError('Dimension size must be a positive integer')

        if self.__name == 'one':
            self.__size = 1
        elif self.__name == 'nmonths':
            self.__size = 12
        elif self.__name == 'ndays':
            self.__size = 366
        else:
            self.__size = value

        if self.__name not in ['one', 'nmonths', 'ndays'] and self.__size != value:
            print('ERROR: Dimension, {}, size={}, but size {} was requested'.format(self.__name, self.__size, value))

    @property
    def description(self):
        """Description for the dimension.

        :returns: description for the dimension
        :rtype: str
        """

        return self.__description

    @description.setter
    def description(self, descstr):
        """Set the description of the dimension.

        :param str descstr: description string
        """

        self.__description = descstr

    def __repr__(self):
        return 'Dimension(name={}, size={!r})'.format(self.name, self.size)

    def __iadd__(self, other):
        """Add a number to dimension size.

        :param int other: integer value

        :returns: dimension size
        :rtype: int

        :raises ValueError: if type of parameter is not an integer
        """

        # augment in-place addition so the instance plus a number results
        # in a change to self.__size
        if not isinstance(other, int):
            raise ValueError('Dimension size type must be an integer')
        self.__size += other
        return self

    def __isub__(self, other):
        """Subtracts integer from dimension size.

        :param int other: integer value

        :returns: dimension size
        :rtype: int

        :raises ValueError: if type of parameter is not an integer
        :raises ValeuError: if parameter is not a positive integer
        """

        # augment in-place addition so the instance minus a number results
        # in a change to self.__size
        if not isinstance(other, int):
            raise ValueError('Dimension size type must be an integer')
        if self.__size - other < 0:
            raise ValueError('Dimension size must be positive')
        self.__size -= other
        return self


class DimensionDict(PrmsDict):
    """
    An Odict-like object that holds pyPRMS.Dimension objects with the
    ability to add and remove parameter objects.

    Example
    -------

    """

    def __init__(self, verbose=False):

        super().__init__(data=[])
        self.__verbose = verbose


    @property
    def ndims(self):
        """Get number of dimensions.

        :returns: number of dimensions
        :rtype: int
        """

        return len(self.keys())

    @property
    def xml(self):
        """Get xml element for the dimensions.

        :returns: XML element for the dimensions
        :rtype: xmlET.Element
        """

        # <dimensions>
        #     <dimension name = "nsegment" position = "1" size = "1434" />
        # </ dimensions>
        dims_xml = xmlET.Element('dimensions')

        for kk, vv in iter(self.items()):
            dim_sub = xmlET.SubElement(dims_xml, 'dimension')
            dim_sub.set('name', kk)
            xmlET.SubElement(dim_sub, 'size').text = str(vv.size)
            # dim_sub.set('size', str(vv.size))
        return dims_xml

    def add(self, name, size=0):
        """Add a new dimension.

        :param str name: name of the dimension
        :param int size: size of the dimension
        """

        # This method adds a dimension if it doesn't exist
        # Duplicate dimension names are silently ignored
        # TODO: check for valid dimension size for ndays, nmonths, and one
        if name not in self.keys():
            try:
                self.__setitem__(name, Dimension(name=name, size=size))
                self.__dict__[name] = Dimension(name=name, size=size)
            except ValueError as err:
                if self.__verbose:
                    print(err)
                else:
                    pass
        # else:
        #     # TODO: Should this raise an error?
        #     print('Dimension {} already exists...skipping add\
        #     name'.format(name))

    def add_from_xml(self, filename):
        """Add one or more dimensions from an xml file.

        :param str filename: name of xml file to read
        """

        # Add dimensions and grow dimension sizes from xml information for a
        # parameter
        # This information is found in xml files for each region for each
        # parameter
        # No attempt is made to verify whether each region for a given
        # parameter has the same or same number of dimensions.
        xml_root = read_xml(filename)

        # TODO: We can't guarantee the order of the dimensions in the xml file
        #       so we should make sure dimensions are added in the correct
        #       order dictated by the position attribute.
        #       1) read all dimensions in the correct 'position'-dictated order
        #       into a list
        #       2) add dimensions in list to the dimensions ordereddict
        for cdim in xml_root.findall('./dimensions/dimension'):
            name = cdim.get('name')
            size = int(cdim.get('size'))

            if name not in self.keys():
                try:
                    self.__setitem__(name, Dimension(name=name, size=size))
                    self.__dict__[name] = Dimension(name=name, size=size)
                except ValueError as err:
                    print(err)
            else:
                if name not in ['nmonths', 'ndays', 'one']:
                    # NOTE: This will always try to grow a dimension if it
                    # already exists!
                    self.__dict__[name].size += size

    def exists(self, name):
        """Check if dimension exists.

        :param str name: name of the dimension
        :returns: True if dimension exists, otherwise False
        :rtype: bool
        """

        return name in self.keys()

    def get(self, name):
        """Get dimension.

        :param str name: name of the dimension

        :returns: dimension
        :rtype: Dimension

        :raises ValueError: if dimension does not exist
        """

        if self.exists(name):
            return self.__getitem__(name)
        raise ValueError('Dimension, {}, does not exist.'.format(name))

    def remove(self, name):
        """Remove dimension.

        :param str name: dimension name
        """

        if self.exists(name):
            self.__delitem__(name)

    def tostructure(self):
        """Get data structure of Dimensions data for serialization.

        :returns: dictionary of dimension names and sizes
        :rtype: dict
        """

        dims = {}
        for kk, vv in iter(self.items()):
            dims[kk] = {'size': vv.size}
        return dims

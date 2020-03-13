import abc
from collections import OrderedDict


class PrmsDict(OrderedDict):
    """
    A generic object for handling collections of parameters,
    variables, or dimensions.
    """

    def __init__(self, data=None):
        """
        Parameters
        ----------
        data : list or dict of objects
            A list of pyPRMS.Parameter, pyPRMS.Variable, or pyPRMS.Dimension
            objects.

        """
        super(PrmsDict, self).__init__(self)
        if data is not None:
            self.__cast_data(data)

    # Private method to cast the data argument
    # Should only be called by the constructor
    def __cast_data(self, data):
        """
        Casts a list or dict of objects into the ODict structure storing
        object names as the keys and objects as the values.
        """
        if isinstance(data, list):

            # Assume this is a dictionary of pyPRMS.Parameter objects
            for item in data:
                self.__setitem__(item.name, item)
                self.__dict__[item.name] = item

        elif isinstance(data, dict) or isinstance(data, OrderedDict):

            # Assume this is a dictionary of pyPRMS.Parameter objects
            for name, item in iter(data.items()):
                self.__setitem__(name, item)
                self.__dict__[name] = item

        else:
            raise Exception('Input data format is not recognized. Please \
                            pass a list or dict-like object.')

        return

    @abc.abstractmethod
    def add(self, name):
        raise NotImplementedError(
            'must define check in child '
            'class to use this base class')

    @abc.abstractmethod
    def exists(self, name):
        raise NotImplementedError(
            'must define check in child '
            'class to use this base class')


from __future__ import annotations
from typing import Union, Type, Tuple
from .device import Device


class ConnectionMetadata:
    """
    Describes the metadata of a connection.
    """

    def __init__(
            self,
            from_device: Union[Type[Device], None] = None,
            to_device: Union[Type[Device], None] = None,
            from_device_node_name: Union[str, None] = None,
            to_device_node_name: Union[str, None] = None,
            bidirectional: bool = True,
    ):

        self._from_device = None
        self._from_device_node_name = None
        self.set_from(from_device, from_device_node_name)

        self._to_device = None
        self._to_device_node_name = None
        self.set_to(to_device, to_device_node_name)

        if not ((from_device is None and to_device is None and from_device_node_name is None
                 and to_device_node_name is None) or (
                from_device is not None and to_device is not None and from_device_node_name is not None and
                to_device_node_name is not None)):
            raise ValueError(
                "you have to provide all or none of the following items: `from_device`, `from_device_node_name`, "
                "`to_device` or `to_device_node_name`")

        # describes if the connection is uni or bidirectional
        self._bidirectional = bidirectional

    def __eq__(self, other: ConnectionMetadata):
        return self.equal_with(other)

    def __compare_with(self, other: ConnectionMetadata, allow_single_unidirectional_for_both_directions: bool) -> bool:
        """
        This method checks, if the metadata of this object is the metadata of the other object.

        The method returns true in the following situations:
        * both connections are bidirectional / the FROM and TO elements (device and node name) are the same
        * both connections are bidirectional / the FROM is the TO and the TO is the FROM
        * both connections are unidirectional and have the same from and to elements

        If the parameter `allow_single_unidirectional_for_both_directions` is True, it additionally checks the following
        situations:
        * one is unidirectional / the other is bidirectional / the FROM and TO elements are the same
        * one is unidirectional / the other is bidirectional / the FROM is the TO and the TO is the FROM
        """
        def check_same() -> bool:
            return (self.from_device == other.from_device and self.from_node_name == other.from_node_name and
                    self.to_device == other.to_device and self.to_node_name == other.to_node_name)

        def check_twisted() -> bool:
            return (self.from_device == other.to_device and self.from_node_name == other.to_node_name and
                    self.to_device == other.from_device and self.to_node_name == other.from_node_name)

        # CHECK: both connections are bidirectional / the FROM and TO elements (device and node name) are the same
        # CHECK: both connections are bidirectional / the FROM is the TO and the TO is the FROM
        if self.bidirectional and other.bidirectional:
            return check_same() or check_twisted()
        # CHECK: both connections are unidirectional and have the same from and to elements
        if not self.bidirectional and not other.bidirectional:
            return check_same()

        if allow_single_unidirectional_for_both_directions:
            # CHECK: one is unidirectional / the other is bidirectional / the FROM and TO elements are the same
            # CHECK: one is unidirectional / the other is bidirectional / the FROM is the TO and the TO is the FROM
            if self.bidirectional and not other.bidirectional or not self.bidirectional and other.bidirectional:
                return check_same() or check_twisted()
        return False

    def set_from(self, from_device: Union[Type[Device], None], from_device_node_name: Union[str, None] = None):
        """
        This method sets the FROM device and node for this connection.

        :param from_device: The FROM device of this connection.
        :param from_device_node_name: The FROM node of this connection (if it should be set, otherwise None).
        """
        if from_device is not None and isinstance(from_device, type) and not issubclass(from_device, Device):
            raise TypeError(f"detect illegal argument element {str(from_device)} for given attribute "
                            f"`from_device` - should be a subclasses of `balder.Device`")
        self._from_device = from_device

        if from_device_node_name is not None and not isinstance(from_device_node_name, str):
            raise TypeError(f"detect illegal argument type {type(from_device_node_name)} for given attribute "
                            f"`from_device_node_name` - should be a string value")
        self._from_device_node_name = from_device_node_name

    def set_to(self, to_device: Union[Type[Device], None], to_device_node_name: Union[str, None] = None):
        """
        This method sets the TO device and node of this connection.

        :param to_device: The TO device of this connection.
        :param to_device_node_name: The TO node of this connection (if it should be set, otherwise None).
        """
        if to_device is not None and isinstance(to_device, type) and not issubclass(to_device, Device):
            raise TypeError(f"detect illegal argument element {str(to_device)} for given attribute "
                            f"`to_device` - should be a subclasses of `balder.Device`")
        self._to_device = to_device

        if to_device_node_name is not None and not isinstance(to_device_node_name, str):
            raise TypeError(f"detect illegal argument type {type(to_device_node_name)} for given attribute "
                            f"`to_device_node_name` - should be a string value")
        self._to_device_node_name = to_device_node_name

    def get_conn_partner_of(self, device: Type[Device], node: Union[str, None] = None) -> Tuple[Type[Device], str]:
        """
        This method returns the connection partner of this connection - it always returns the other not given side

        :param device: the device itself - the other will be returned

        :param node: the node name of the device itself (only required if the connection starts and ends with the same
                     device)
        """
        if device not in (self.from_device, self.to_device):
            raise ValueError(f"the given device `{device.__qualname__}` is no component of this connection")
        if node is None:
            # check that the from_device and to_device are not the same
            if self.from_device == self.to_device:
                raise ValueError("the connection is a inner-device connection (start and end is the same device) - you "
                                 "have to provide the `node` string too")
            if device == self.from_device:
                return self.to_device, self.to_node_name

            return self.from_device, self.from_node_name

        if node not in (self.from_node_name, self.to_node_name):
            raise ValueError(f"the given node `{node}` is no component of this connection")

        if device == self.from_device and node == self.from_node_name:
            return self.to_device, self.to_node_name

        if device == self.to_device and node == self.to_node_name:
            return self.from_device, self.from_node_name

        raise ValueError(f"the given node `{node}` is no component of the given device `{device.__qualname__}`")

    def has_connection_from_to(self, start_device, end_device=None) -> bool:
        """
        This method checks if there is a connection from ``start_device`` to ``end_device``. This will return
        true if the ``start_device`` and ``end_device`` given in this method are also the ``start_device`` and
        ``end_device`` mentioned in this connection object. If this is a bidirectional connection, ``start_device`` and
        ``end_device`` can switch places.


        :param start_device: the device for which the method should check whether it is a communication partner (for
                             non-bidirectional connection, this has to be the start device)

        :param end_device: the other device for which the method should check whether it is a communication partner (for
                           non-bidirectional connection, this has to be the end device - this is optional if only the
                           start device should be checked)

        :return: returns true if the given direction is possible
        """
        if end_device is None:

            if self.bidirectional:
                return start_device in (self.from_device, self.to_device)

            return start_device == self.from_device

        if self.bidirectional:
            return start_device == self.from_device and end_device == self.to_device or \
                   start_device == self.to_device and end_device == self.from_device

        return start_device == self.from_device and end_device == self.to_device

    def equal_with(self, other: ConnectionMetadata) -> bool:
        """
        This method returns true if the metadata of the current connection is equal with the metadata of the given
        connection.

        The method returns true in the following situations:
        * both connections are bidirectional and the from and to elements (device and node name) are the same
        * both connections are unidirectional and have the same from and to elements
        * both connections are bidirectional and the from is the to and the to is the from

        :return: true if the metadata of the current connection is contained in the metadata of the given one
        """
        return self.__compare_with(other, allow_single_unidirectional_for_both_directions=False)

    def contained_in(self, other: ConnectionMetadata) -> bool:
        """
        This method returns true if the metadata of the current connection is contained in the given one.

        The method returns true in the following situations:
        * both connections are bidirectional and the from and to elements (device and node name) are the same
        * both connections are unidirectional and have the same from and to elements
        * both connections are bidirectional and the from is the to and the to is the from
        * one connection is unidirectional and the other is bidirectional and the from and to elements are the same
        * one connection is unidirectional and the other is bidirectional and the from is the to and the to is the from

        :return: true if the metadata of the current connection is contained in the metadata of the given one
        """
        return self.__compare_with(other, allow_single_unidirectional_for_both_directions=True)

    @property
    def from_device(self):
        """device from which the connection starts"""
        return self._from_device

    @property
    def to_device(self):
        """device at which the connection ends"""
        return self._to_device

    @property
    def from_node_name(self):
        """the name of the node in the `Device` from which the connection starts"""
        return self._from_device_node_name

    @property
    def to_node_name(self):
        """the name of the node in the `Device` at which the connection ends"""
        return self._to_device_node_name

    @property
    def bidirectional(self) -> bool:
        """
        returns true if the connection is bidirectional (can go in both directions) otherwise false
        """
        return self._bidirectional

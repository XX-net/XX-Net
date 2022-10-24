# Copyright (c) 2015, Hubert Kario
#
# See the LICENSE file for legal information regarding use of this file.

"""Helper package for handling fragmentation of messages."""

from __future__ import generators

from .utils.codec import Parser
from .utils.deprecations import deprecated_attrs, deprecated_params


@deprecated_attrs({"add_static_size": "addStaticSize",
                   "add_dynamic_size": "addDynamicSize",
                   "add_data": "addData",
                   "get_message": "getMessage",
                   "clear_buffers": "clearBuffers"})
class Defragmenter(object):
    """
    Class for demultiplexing TLS messages.

    Since the messages can be interleaved and fragmented between each other
    we need to cache not complete ones and return in order of urgency.

    Supports messages with given size (like Alerts) or with a length header
    in specific place (like Handshake messages).

    :ivar priorities: order in which messages from given types should be
        returned.
    :ivar buffers: data buffers for message types
    :ivar decoders: functions which check buffers if a message of given type
        is complete
    """

    def __init__(self):
        """Set up empty defregmenter"""
        self.priorities = []
        self.buffers = {}
        self.decoders = {}

    @deprecated_params({"msg_type": "msgType"})
    def add_static_size(self, msg_type, size):
        """Add a message type which all messages are of same length"""
        if msg_type in self.priorities:
            raise ValueError("Message type already defined")
        if size < 1:
            raise ValueError("Message size must be positive integer")

        self.priorities += [msg_type]

        self.buffers[msg_type] = bytearray(0)
        def size_handler(data):
            """
            Size of message in parameter

            If complete message is present in parameter returns its size,
            None otherwise.
            """
            if len(data) < size:
                return None
            else:
                return size
        self.decoders[msg_type] = size_handler

    @deprecated_params({"msg_type": "msgType",
                        "size_offset": "sizeOffset",
                        "size_of_size": "sizeOfSize"})
    def add_dynamic_size(self, msg_type, size_offset, size_of_size):
        """Add a message type which has a dynamic size set in a header"""
        if msg_type in self.priorities:
            raise ValueError("Message type already defined")
        if size_of_size < 1:
            raise ValueError("Size of size must be positive integer")
        if size_offset < 0:
            raise ValueError("Offset can't be negative")

        self.priorities += [msg_type]
        self.buffers[msg_type] = bytearray(0)

        def size_handler(data):
            """
            Size of message in parameter

            If complete message is present in parameter returns its size,
            None otherwise.
            """
            if len(data) < size_offset+size_of_size:
                return None
            else:
                parser = Parser(data)
                # skip the header
                parser.skip_bytes(size_offset)

                payload_length = parser.get(size_of_size)
                if parser.getRemainingLength() < payload_length:
                    # not enough bytes in buffer
                    return None
                return size_offset + size_of_size + payload_length

        self.decoders[msg_type] = size_handler

    @deprecated_params({"msg_type": "msgType"})
    def add_data(self, msg_type, data):
        """Adds data to buffers"""
        if msg_type not in self.priorities:
            raise ValueError("Message type not defined")

        self.buffers[msg_type] += data

    def get_message(self):
        """Extract the highest priority complete message from buffer"""
        for msg_type in self.priorities:
            buf = self.buffers[msg_type]
            length = self.decoders[msg_type](buf)
            if length is None:
                continue

            # extract message
            data = buf[:length]
            # remove it from buffer
            del buf[:length]
            return (msg_type, data)
        return None

    def clear_buffers(self):
        """Remove all data from buffers"""
        for key in self.buffers.keys():
            self.buffers[key] = bytearray(0)

# -*- coding: utf-8 -*-
"""
port from hyper/http20/stream for async
remove push support
increase init window size to improve performance
~~~~~~~~~~~~~~~~~~~

Objects that make up the stream-level abstraction of hyper's HTTP/2 support.


Conceptually, a single HTTP/2 connection is made up of many streams: each
stream is an independent, bi-directional sequence of HTTP headers and data.
Each stream is identified by a monotonically increasing integer, assigned to
the stream by the endpoint that initiated the stream.
"""




from hyper.common.headers import HTTPHeaderMap
from hyper.packages.hyperframe.frame import (
    FRAME_MAX_LEN, FRAMES, HeadersFrame, DataFrame, PushPromiseFrame,
    WindowUpdateFrame, ContinuationFrame, BlockedFrame, RstStreamFrame
)
from hyper.http20.exceptions import ProtocolError, StreamResetError
from hyper.http20.util import h2_safe_headers
from hyper.http20.response import strip_headers
from hyper.common.util import to_host_port_tuple, to_native_string, to_bytestring

from http_common import *
from xlog import getLogger
xlog = getLogger("gae_proxy")


# Define a set of states for a HTTP/2 stream.
STATE_IDLE               = 0
STATE_OPEN               = 1
STATE_HALF_CLOSED_LOCAL  = 2
STATE_HALF_CLOSED_REMOTE = 3
STATE_CLOSED             = 4


class Stream(object):
    """
    A single HTTP/2 stream.

    A stream is an independent, bi-directional sequence of HTTP headers and
    data. Each stream is identified by a single integer. From a HTTP
    perspective, a stream _approximately_ matches a single request-response
    pair.
    """
    def __init__(self,
                 connection,
                 ip,
                 stream_id,
                 host,
                 task,
                 send_cb,
                 close_cb,
                 header_encoder,
                 header_decoder,
                 receive_window_manager,
                 remote_window_size,
                 max_frame_size):

        self.connection = connection
        self.ip = ip
        self.stream_id = stream_id
        self.host = host
        self.task = task
        self.state = STATE_IDLE
        self.get_head_time = None

        # There are two flow control windows: one for data we're sending,
        # one for data being sent to us.
        self.receive_window_manager = receive_window_manager
        self.remote_window_size = remote_window_size
        self.max_frame_size = max_frame_size

        # This is the callback handed to the stream by its parent connection.
        # It is called when the stream wants to send data. It expects to
        # receive a list of frames that will be automatically serialized.
        self._send_cb = send_cb

        # This is the callback to be called when the stream is closed.
        self._close_cb = close_cb

        # A reference to the header encoder and decoder objects belonging to
        # the parent connection.
        self._encoder = header_encoder
        self._decoder = header_decoder

        self.request_headers = HTTPHeaderMap()

        # Convert the body to bytes if needed.
        self.request_body = to_bytestring(self.task.body)

        # request body not send blocked by send window
        # the left body will send when send window opened.
        self.request_body_left = len(self.request_body)

        # data list before decode
        self.response_header_datas = []

        # Set to a key-value set of the response headers once their
        # HEADERS..CONTINUATION frame sequence finishes.
        self.response_headers = None

        # Unconsumed response data chunks
        self.response_body = []
        self.response_body_len = 0

        self.start_request()

    def start_request(self):
        """
        Open the stream. Does this by encoding and sending the headers: no more
        calls to ``add_header`` are allowed after this method is called.
        The `end` flag controls whether this will be the end of the stream, or
        whether data will follow.
        """
        # Strip any headers invalid in H2.
        #headers = h2_safe_headers(self.request_headers)

        self.add_header(":method", "POST")
        self.add_header(":scheme", "https")
        self.add_header(":authority", self.host)
        self.add_header(":path", "/_gh/")

        default_headers = (':method', ':scheme', ':authority', ':path')
        for name, value in self.task.headers.items():
            is_default = to_native_string(name) in default_headers
            self.add_header(name, value, replace=is_default)

        # Encode the headers.
        encoded_headers = self._encoder.encode(self.request_headers)

        # It's possible that there is a substantial amount of data here. The
        # data needs to go into one HEADERS frame, followed by a number of
        # CONTINUATION frames. For now, for ease of implementation, let's just
        # assume that's never going to happen (16kB of headers is lots!).
        # Additionally, since this is so unlikely, there's no point writing a
        # test for this: it's just so simple.
        if len(encoded_headers) > FRAME_MAX_LEN:  # pragma: no cover
            raise ValueError("Header block too large.")

        header_frame = HeadersFrame(self.stream_id)
        header_frame.data = encoded_headers

        # If no data has been provided, this is the end of the stream. Either
        # way, due to the restriction above it's definitely the end of the
        # headers.
        header_frame.flags.add('END_HEADERS')

        # Send the header frame.
        self._send_cb(header_frame)

        # Transition the stream state appropriately.
        self.state = STATE_OPEN

        self.send_left_body()

    def add_header(self, name, value, replace=False):
        """
        Adds a single HTTP header to the headers to be sent on the request.
        """
        if not replace:
            self.request_headers[name] = value
        else:
            self.request_headers.replace(name, value)

    def send_left_body(self):
        while self.remote_window_size and self.request_body_left:
            send_size = min(self.remote_window_size, self.request_body_left, self.max_frame_size)

            f = DataFrame(self.stream_id)
            data_start = len(self.request_body) - self.request_body_left
            f.data = self.request_body[data_start:data_start+send_size]

            self.remote_window_size -= send_size
            self.request_body_left -= send_size

            # If the length of the data is less than MAX_CHUNK, we're probably
            # at the end of the file. If this is the end of the data, mark it
            # as END_STREAM.
            if self.request_body_left == 0:
                f.flags.add('END_STREAM')

            # Send the frame and decrement the flow control window.
            self._send_cb(f)

            # If no more data is to be sent on this stream, transition our state.
            if self.request_body_left == 0:
                self._close_local()

    def receive_frame(self, frame):
        """
        Handle a frame received on this stream.
        called by connection.
        """

        if frame.type == WindowUpdateFrame.type:
            self.remote_window_size += frame.window_increment
            self.send_left_body()
        elif frame.type == HeadersFrame.type:
            # Begin the header block for the response headers.
            self.response_header_datas = [frame.data]
        elif frame.type == PushPromiseFrame.type:
            xlog.error("%s receive PushPromiseFrame:%d", self.ip, frame.stream_id)
        elif frame.type == ContinuationFrame.type:
            # Continue a header block begun with either HEADERS or PUSH_PROMISE.
            self.response_header_datas.append(frame.data)
        elif frame.type == DataFrame.type:
            # Append the data to the buffer.
            self.task.put_data(frame.data)

            if 'END_STREAM' not in frame.flags:
                # Increase the window size. Only do this if the data frame contains
                # actual data.
                # don't do it if stream is closed.
                size = frame.flow_controlled_length
                increment = self.receive_window_manager._handle_frame(size)
                #if increment:
                #    xlog.debug("stream:%d frame size:%d increase win:%d", self.stream_id, size, increment)

                #content_len = int(self.request_headers.get("Content-Length")[0])
                #xlog.debug("%s get:%d s:%d", self.ip, self.response_body_len, size)

                if increment and not self._remote_closed:
                    w = WindowUpdateFrame(self.stream_id)
                    w.window_increment = increment
                    self._send_cb(w)
        elif frame.type == BlockedFrame.type:
            # If we've been blocked we may want to fixup the window.
            increment = self.receive_window_manager._blocked()
            if increment:
                w = WindowUpdateFrame(self.stream_id)
                w.window_increment = increment
                self._send_cb(w)
        elif frame.type == RstStreamFrame.type:
            xlog.warn("%s Stream %d forcefully closed.", self.ip, self.stream_id)
            self.close("RESET")
        elif frame.type in FRAMES:
            # This frame isn't valid at this point.
            #raise ValueError("Unexpected frame %s." % frame)
            xlog.error("%s Unexpected frame %s.", self.ip, frame)
        else:  # pragma: no cover
            # Unknown frames belong to extensions. Just drop it on the
            # floor, but log so that users know that something happened.
            xlog.error("%s Received unknown frame, type %d", self.ip, frame.type)
            pass

        if 'END_HEADERS' in frame.flags:
            # Begin by decoding the header block. If this fails, we need to
            # tear down the entire connection. TODO: actually do that.
            headers = self._decoder.decode(b''.join(self.response_header_datas))

            self._handle_header_block(headers)
            # We've handled the headers, zero them out.
            self.response_header_datas = None

            self.task.content_length = int(self.response_headers["Content-Length"][0])
            time_now = self.task.set_state("h2_get_head")
            self.get_head_time = time_now
            self.send_response()

        if 'END_STREAM' in frame.flags:
            #xlog.debug("%s Closing remote side of stream:%d", self.ip, self.stream_id)
            time_now = time.time()
            time_cose = time_now - self.get_head_time
            if time_cose:
                speed = self.task.content_length / time_cose
                self.task.set_state("h2_finish[SP:%d]" % speed)
                self.connection.report_speed(speed, self.task.content_length)

            self._close_remote()

            self.close("end stream")

    def send_response(self):
        status = int(self.response_headers[b':status'][0])
        strip_headers(self.response_headers)
        response = BaseResponse(status=status, headers=self.response_headers)
        response.ssl_sock = self.connection.ssl_sock
        response.worker = self.connection
        response.task = self.task
        self.task.queue.put(response)

    def close(self, reason=""):
        self.task.put_data("")
        # empty block means fail or closed.

        self._close_cb(self.stream_id, reason)

    def _handle_header_block(self, headers):
        """
        Handles the logic for receiving a completed headers block.

        A headers block is an uninterrupted sequence of one HEADERS frame
        followed by zero or more CONTINUATION frames, and is terminated by a
        frame bearing the END_HEADERS flag.

        HTTP/2 allows receipt of up to three such blocks on a stream. The first
        is optional, and contains a 1XX response. The second is mandatory, and
        must contain a final response (200 or higher). The third is optional,
        and may contain 'trailers', headers that are sent after a chunk-encoded
        body is sent.

        Here we only process the simple state: no push, one header frame.
        """

        if self.response_headers is None:
            self.response_headers = HTTPHeaderMap(headers)
        else:
            # Received too many headers blocks.
            raise ProtocolError("Too many header blocks.")

        return

    @property
    def _local_closed(self):
        return self.state in (STATE_CLOSED, STATE_HALF_CLOSED_LOCAL)

    @property
    def _remote_closed(self):
        return self.state in (STATE_CLOSED, STATE_HALF_CLOSED_REMOTE)

    @property
    def _local_open(self):
        return self.state in (STATE_OPEN, STATE_HALF_CLOSED_REMOTE)

    def _close_local(self):
        self.state = (
            STATE_HALF_CLOSED_LOCAL if self.state == STATE_OPEN
            else STATE_CLOSED
        )

    def _close_remote(self):
        self.state = (
            STATE_HALF_CLOSED_REMOTE if self.state == STATE_OPEN
            else STATE_CLOSED
        )

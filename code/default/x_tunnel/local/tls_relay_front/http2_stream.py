

from front_base.http2_stream import Stream as StreamBase
from front_base.http2_stream import STATE_OPEN

from hyper.packages.hyperframe.frame import (
    FRAME_MAX_LEN, HeadersFrame
)
from hyper.common.util import to_native_string


class Stream(StreamBase):

    def start_request(self):
        """
        Open the stream. Does this by encoding and sending the headers: no more
        calls to ``add_header`` are allowed after this method is called.
        The `end` flag controls whether this will be the end of the stream, or
        whether data will follow.
        """
        # Strip any headers invalid in H2.

        # Use the sni as host
        host = self.connection.ssl_sock.host

        # build the path
        path = self.connection.ssl_sock.url_path + self.task.path

        self.add_header(":method", self.task.method)
        self.add_header(":scheme", "https")
        self.add_header(":authority", host)
        self.add_header(":path", path)

        default_headers = (':method', ':scheme', ':authority', ':path')

        for name, value in list(self.task.headers.items()):
            is_default = to_native_string(name) in default_headers
            self.add_header(name, value, replace=is_default)

        # set the target host in header
        self.add_header(b"X-Host", self.task.host, replace=False)

        # Encode the headers.
        encoded_headers = self._encoder(self.request_headers)

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
        if self.request_body_left == 0:
            header_frame.flags.add('END_STREAM')

        # Send the header frame.
        self.task.set_state("start send header")
        self._send_cb(header_frame)

        # Transition the stream state appropriately.
        self.state = STATE_OPEN

        self.task.set_state("start send left body")
        if self.request_body_left > 0:
            self.send_left_body()

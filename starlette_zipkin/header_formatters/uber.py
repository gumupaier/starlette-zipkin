"""
https://www.jaegertracing.io/docs/1.7/client-libraries/
https://github.com/aio-libs/aiozipkin/blob/v0.5.0/aiozipkin/helpers.py
"""
from aiozipkin.helpers import (
    TRACE_ID_HEADER as B3_TRACE_ID_HEADER,
    SPAN_ID_HEADER,
    PARENT_ID_HEADER,
    SAMPLED_ID_HEADER,
    FLAGS_HEADER,
    make_context,
    TraceContext,
)
from .template import Headers


class UberHeaders(Headers):
    TRACE_ID_HEADER = "uber-trace-id"
    KEYS = ["uber-trace-id"]

    def make_headers(self, context, response_headers):
        # if headers already injected within whe application
        # using the build in b3 format, set the context to
        # the child context
        if B3_TRACE_ID_HEADER in response_headers:
            context = self.make_context(response_headers)
            self._clean_b3_headers(response_headers)

        parent_span_id = (
            context.parent_id if context.parent_id is not None else "0"
        )

        # TODO: validate this is correct
        if context.debug:
            flags = "2"
        elif context.sampled:
            flags = "1"
        else:
            flags = "0"

        headers = {
            self.TRACE_ID_HEADER: f"{context.trace_id}:{context.span_id}:{parent_span_id}:{flags}"
        }
        response_headers.update(headers)

        return response_headers

    def make_context(self, headers):
        has_uber = self.TRACE_ID_HEADER in headers

        if has_uber:
            trace_id, span_id, parent_id, debug, sampled = self._parse_uber_headers(
                headers
            )
            tc = TraceContext(
                trace_id=trace_id,
                parent_id=parent_id,
                span_id=span_id,
                sampled=sampled,
                debug=debug,
                shared=False,
            )
            return tc
        else:
            # create context from B3 headers - used as a shortcut
            # for make_headers. It is NOT recommended to mix b3
            # and uber-trace-id formats together, as it is untested
            return make_context(headers)

    def _parse_uber_headers(self, headers):
        trace_id, span_id, parent_id, flags = headers[
            self.TRACE_ID_HEADER
        ].split(":")
        debug = flags == "2"
        sampled = debug if debug else flags == "1"
        return trace_id, span_id, parent_id, debug, sampled

    def get_trace_id(self, headers):
        has_uber = self.TRACE_ID_HEADER in headers
        if has_uber:
            trace_id, span_id, parent_id, debug, sampled = self._parse_uber_headers(
                headers
            )
            return trace_id
        else:
            return None

    @staticmethod
    def _clean_b3_headers(headers):
        b3_all = [
            B3_TRACE_ID_HEADER,
            SPAN_ID_HEADER,
            PARENT_ID_HEADER,
            FLAGS_HEADER,
            SAMPLED_ID_HEADER,
        ]
        for key in b3_all:
            if key in headers:
                del headers[key]

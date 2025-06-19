import logging
from typing import Optional, Dict
from contextlib import contextmanager

from opentelemetry import trace, _logs
from opentelemetry.trace import SpanKind
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# For Logs
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

# Resource for both traces and logs
resources = Resource.create({SERVICE_NAME: "lab_lab"})

trace.set_tracer_provider(TracerProvider(resource=resources))
tracer = trace.get_tracer("lab_log")
# SigNoz default OTLP HTTP endpoint for traces
otlp_trace_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
span_processor = BatchSpanProcessor(otlp_trace_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# SigNoz default OTLP HTTP endpoint for logs
otlp_log_exporter = OTLPLogExporter(endpoint="http://localhost:4318/v1/logs")
log_processor = BatchLogRecordProcessor(otlp_log_exporter)
logger_provider = LoggerProvider(resource=resources)
logger_provider.add_log_record_processor(log_processor)
_logs.set_logger_provider(logger_provider)


class Log:
    def __init__(self, name: str, context: Optional[Dict[str, str]] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        #for handler in list(self.logger.handlers):
        #   self.logger.removeHandler(handler)

        otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
        self.logger.addHandler(otel_handler)

        self.context = context or {}
        self.tracer = tracer

    def with_context(self, **kwargs) -> 'Log':
        new_context = {**self.context, **kwargs}
        return Log(self.logger.name, new_context)

    def info(self, message: str, **kwargs):
        self.logger.info(message, extra={**self.context, **kwargs})

    def error(self, message: str, **kwargs):
        self.logger.error(message, extra={**self.context, **kwargs})

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra={**self.context, **kwargs})

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra={**self.context, **kwargs})

    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra={**self.context, **kwargs})

    @contextmanager
    def trace(self, name: str, **kwargs):
        with self.tracer.start_as_current_span(name, kind=SpanKind.INTERNAL) as span:
            span.set_attributes(self.context)
            span.set_attributes(kwargs) # Add kwargs to span attributes as well
            yield span

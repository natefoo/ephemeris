# -*- coding: utf-8 -*-
import logging
import signal
import tempfile
from functools import partial

from yaspin.core import Yaspin
from yaspin.signal_handlers import default_handler


class Logger(object):
    def _init(self, *args, **kwargs):
        self._spinning = False
        self.debug = partial(self._mlog, logging.DEBUG)
        self.info = partial(self._mlog, logging.INFO)
        self.warning = partial(self._mlog, logging.WARNING)
        self.error = partial(self._mlog, logging.ERROR)

    def _getmsg(self, msg, *args):
        if self._spinning:
            msg += self._msg_prefix + msg
        return msg % args

    def start(self, *args, **kwargs):
        self._spinning = True

    def ok(self, *args, **kwargs):
        self._spinning = False

    def skip(self, *args, **kwargs):
        self._spinning = False

    def fail(self, *args, **kwargs):
        self._spinning = False


class LoggingLogger(logging.getLoggerClass(), Logger):

    _msg_prefix = '\t'

    def __init__(self, *args, **kwargs):
        super(LoggingLogger, self).__init__(*args, **kwargs)
        self._init(*args, **kwargs)

    def _mlog(self, level, msg, *args, **kwargs):
        self.log(level, self._getmsg(msg), *args)

    def start(self, msg, *args, **kwargs):
        level = kwargs.get('level', logging.DEBUG)
        self.log(level, msg % args)
        super(LoggingLogger, self).start(*args, **kwargs)

    def ok(self, msg, *args, **kwargs):
        level = kwargs.get('level', logging.DEBUG)
        self.log(level, msg % args)
        super(LoggingLogger, self).ok(*args, **kwargs)

    skip = ok

    def fail(self, msg, *args, **kwargs):
        self.log(logging.ERROR, msg % args)
        super(LoggingLogger, self).fail(*args, **kwargs)


class SpinningLogger(Yaspin, Logger):

    _msg_prefix = '> '

    def __init__(self, *args, **kwargs):
        kwargs["sigmap"] = {signal.SIGINT: default_handler}
        super(SpinningLogger, self).__init__(*args, **kwargs)
        self._init(*args, **kwargs)

    def __append(self, kwargs):
        if 'append' in kwargs:
            self.text += ' ' + kwargs['append']

    def _mlog(self, level, msg, *args, **kwargs):
        self.write(self._getmsg(msg, *args))

    def start(self, msg, *args, **kwargs):
        self.text = msg
        self.color = kwargs.get('color', 'cyan')
        super(SpinningLogger, self).start(*args, **kwargs)

    def ok(self, *args, **kwargs):
        self.__append(kwargs)
        self.color = 'green'
        super(SpinningLogger, self).ok('✔')

    def skip(self, *args, **kwargs):
        self.__append(kwargs)
        self.color = 'yellow'
        super(SpinningLogger, self).ok('-')

    def fail(self, *args, **kwargs):
        self.__append(kwargs)
        self.color = 'red'
        super(SpinningLogger, self).fail('✘')


logging.setLoggerClass(LoggingLogger)


class ProgressConsoleHandler(logging.StreamHandler):
    """
    A handler class which allows the cursor to stay on
    one line for selected messages
    """
    on_same_line = False

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            same_line = hasattr(record, 'same_line')
            if self.on_same_line and not same_line:
                stream.write('\r\n')
            stream.write(msg)
            if same_line:
                stream.write('.')
                self.on_same_line = True
            else:
                stream.write('\r\n')
                self.on_same_line = False
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


def disable_external_library_logging():
    # Omit (most of the) logging by external libraries
    logging.getLogger('bioblend').setLevel(logging.ERROR)
    logging.getLogger('requests').setLevel(logging.ERROR)
    try:
        logging.captureWarnings(True)  # Capture HTTPS warngings from urllib3
    except AttributeError:
        pass


def setup_global_logger(name, log_file=None):
    return SpinningLogger()
    """
    formatter = logging.Formatter('%(asctime)s %(levelname)-5s - %(message)s')
    progress = ProgressConsoleHandler()
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(progress)

    if not log_file:
        # delete = false is chosen here because it is always nice to have a log file
        # ready if you need to debug. Not having the "if only I had set a log file"
        # moment after the fact.
        temp = tempfile.NamedTemporaryFile(prefix="ephemeris_", delete=False)
        log_file = temp.name
    file_handler = logging.FileHandler(log_file)
    logger.addHandler(file_handler)
    logger.info("Storing log file in: {0}".format(log_file))
    return logger
    """

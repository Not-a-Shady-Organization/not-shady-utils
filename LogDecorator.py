import functools
import logging

class LogDecorator(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def __call__(self, fn):
        @functools.wraps(fn)
        def decorated(*args, **kwargs):
            try:
                self.logger.debug(f'{fn.__name__} - {args} - {kwargs}')
                result = fn(*args, **kwargs)
                self.logger.debug(result)
                return result
            except Exception as ex:
                self.logger.debug("Exception {0}".format(ex))
                raise ex
            return result
        return decorated

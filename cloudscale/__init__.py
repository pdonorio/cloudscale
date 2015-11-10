# -*- coding: utf-8 -*-

import pkg_resources
import logging
try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = 'unknown'

myself = "Paolo D'Onorio De Meo <p.donoriodemeo@gmail.com>"

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
logging.getLogger(__name__).addHandler(NullHandler())

FORMAT = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(format=FORMAT)

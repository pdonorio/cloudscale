import pkg_resources

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = 'unknown'

myself = "Paolo D'Onorio De Meo <p.donoriodemeo@gmail.com>"

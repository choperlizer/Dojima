# Add new modules here, so they get imported by *
__all__ = ['bitstamp', 'btc-e', 'campbx']

try:
    import socketIO_client
    __all__.append('mtgox_streaming')
except ImportError:
    __all__.append('mtgox_api1')

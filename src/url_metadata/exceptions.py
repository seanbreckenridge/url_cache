class URLMetadataException(Exception):
    """Generic exception for the url_metadata package"""

    pass


class URLMetadataRequestError(Exception):
    """Encountered a unrecoverable request error while requesting a URL"""

    pass

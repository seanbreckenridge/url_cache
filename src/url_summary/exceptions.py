class URLSummaryException(Exception):
    """Generic exception for url_summary"""

    pass


class URLSummaryRequestException(URLSummaryException):
    """Encountered a request error while requesting a URL"""

    pass

from typing import Callable
from requests import Response, Session, PreparedRequest


class SaveSession(Session):
    """
    A subclass of requests.Session which runs a callback function
    after each request.

    Allows me to expose the request objects after requests using lassie
    """

    # requests.Session doesn't accept any arguments
    def __init__(self, cb_func: Callable[[Response], None]) -> None:
        """
        cb_func: A callback function which saves the response
        """
        self.cb_func = cb_func
        super().__init__()

    # type annotations for kwargs must specify kwargs for *one* of the kwargs; quite arbitrarily chosen
    # https://stackoverflow.com/a/37032111/9348376
    # https://github.com/psf/requests/blob/4f6c0187150af09d085c03096504934eb91c7a9e/requests/sessions.py#L626
    def send(self, request: PreparedRequest, **kwargs: bool) -> Response:  # type: ignore[override]
        """
        Save the latest response for a requests.Session
        """
        resp: Response = super().send(request, **kwargs)  # type: ignore[no-untyped-call,arg-type]
        self.cb_func(resp)
        return resp

Module url_cache.session
========================

Classes
-------

`SaveSession(cb_func: Callable[[requests.models.Response], NoneType])`
:   A subclass of requests.Session which runs a callback function
    after each request.
    
    Allows me to expose the request objects after requests using lassie
    
    cb_func: A callback function which saves the response

    ### Ancestors (in MRO)

    * requests.sessions.Session
    * requests.sessions.SessionRedirectMixin

    ### Methods

    `send(self, request: requests.models.PreparedRequest, **kwargs: bool) ‑> requests.models.Response`
    :   Save the latest response for a requests.Session
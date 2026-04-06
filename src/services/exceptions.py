class EventsServiceError(Exception):
    def __init__(
        self,
        status_code: int,
        detail: str | dict | list | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail

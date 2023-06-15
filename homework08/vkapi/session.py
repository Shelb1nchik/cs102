import typing as tp

import requests  # type: ignore
from requests.adapters import HTTPAdapter  # type: ignore
from requests.packages.urllib3.util.retry import Retry  # type: ignore


class Session:
    """
    Сессия.

    :param base_url: Базовый адрес, на который будут выполняться запросы.
    :param timeout: Максимальное время ожидания ответа от сервера.
    :param max_retries: Максимальное число повторных запросов.
    :param backoff_factor: Коэффициент экспоненциального нарастания задержки.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 5.0,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            allowed_methods=["GET", "POST"],
            status_forcelist=list(range(400, 600)),
        )
        self.adapter = HTTPAdapter(max_retries=self.retry_strategy)
        self.session.mount(base_url, self.adapter)

    def get(self, url: str, *args: tp.Any, **kwargs: tp.Any) -> requests.Response:
        timeout = kwargs.get("timeout", self.timeout)
        response = self.session.get(self.base_url + "/" + url, *args, timeout=timeout, **kwargs)
        return response

    def post(self, url: str, *args: tp.Any, **kwargs: tp.Any) -> requests.Response:
        timeout = kwargs.get("timeout", self.timeout)
        response = self.session.post(self.base_url + "/" + url, *args, timeout=timeout, **kwargs)
        return response

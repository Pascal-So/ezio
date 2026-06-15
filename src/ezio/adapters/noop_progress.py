from collections.abc import Iterable
from typing import override
from ezio.ports.progress import Progress


class NoopProgress(Progress):
    """
    A progress bar implementation that does nothing
    """

    @override
    def track[T](self, iter: Iterable[T], description: str) -> Iterable[T]:
        return iter

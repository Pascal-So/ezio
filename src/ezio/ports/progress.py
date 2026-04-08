from abc import ABC, abstractmethod
from collections.abc import Iterable


class Progress(ABC):
    @abstractmethod
    def track[T](self, iter: Iterable[T], description: str) -> Iterable[T]:
        """Wrap an iterable to show a progress bar"""
        ...

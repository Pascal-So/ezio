from abc import ABC, abstractmethod

from ezio.domain.model import SegmentInfo


class SegmentInfoSource(ABC):
    @abstractmethod
    def add_descriptions(self, segments: list[SegmentInfo]) -> None:
        """Add a description to every segment of the route"""
        ...

    # todo: data input for featured photos

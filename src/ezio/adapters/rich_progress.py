from collections.abc import Iterable
from typing import override

import rich.progress as rp

from ezio.ports.progress import Progress


class RichProgress(Progress):
    """Show progress bars using the `rich` library"""

    def __init__(self) -> None:
        self._progress: rp.Progress = rp.Progress(
            rp.SpinnerColumn(),
            rp.TextColumn("[progress.description]{task.description}"),
            rp.BarColumn(),
            rp.MofNCompleteColumn(),
            rp.TimeRemainingColumn(compact=True, elapsed_when_finished=True),
        )
        self._progress.start()

    @override
    def track[T](self, iter: Iterable[T], description: str) -> Iterable[T]:
        return self._progress.track(iter, description=description)

    def stop(self):
        """Call this once we don't need to show any further progress bars"""
        self._progress.stop()

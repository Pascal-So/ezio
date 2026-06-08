import sys
from typing import ClassVar, override

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Grid, Vertical
from textual.widgets import Button, Input, Label

from ezio.domain.model import SegmentInfo
from ezio.ports.segment_info_source import SegmentInfoSource


class TextualSegmentInfoSource(SegmentInfoSource):
    @override
    def add_descriptions(self, segments: list[SegmentInfo]) -> None:
        app = SegmentInfoApp(segments)
        response = app.run()
        if response is None:
            sys.exit(app.return_code)

        if not response:
            # TODO: user wants to quit the application
            pass


class SegmentInfoApp(App[bool]):
    CSS: ClassVar[str] = """
    Grid {
        grid-size: 2;
        # grid-columns: auto 3fr 2fr;
        grid-columns: auto 1fr;
        height: auto;
    }
    .segment-description {
        padding-bottom: 1;
    }
    .table-header {
        padding-bottom: 1;
    }
    Vertical {
        height: auto;
    }
    #header {
        text-align: center;
        margin-top: 1;
        margin-bottom: 1;
        width: 100%;
    }
    .shift-right {
        margin-left: 1;
    }
    .date {
        padding-right: 1;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+s", action="app.continue", priority=True)
    ]

    ENABLE_COMMAND_PALETTE: ClassVar[bool] = False

    def __init__(self, segments: list[SegmentInfo]) -> None:
        self._segments: list[SegmentInfo] = segments
        self._inputs: list[Input] = []
        return super().__init__()

    @override
    def compose(self) -> ComposeResult:
        yield Label("Enter Segment Descriptions", id="header")

        with Grid():
            yield Label("Segment", classes="table-header")
            yield Label("Description", classes="shift-right")
            # yield Label("Featured Photo", classes="shift-right")

            for seg in self._segments:
                with Vertical(classes="segment-description"):
                    yield Label(f"{seg.date.strftime('%Y-%m-%d')}", classes="date")
                    yield Label(f"{seg.dist_km:.3f} km")
                    yield Label(f"{seg.nr_photos} photos")

                input = Input(value=seg.description, placeholder="Description")
                self._inputs.append(input)
                yield input
                # yield Input(seg.featured_photo)

        yield Button(
            "Continue (ctrl-s)",
            flat=True,
            action="app.continue",
            classes="shift-right",
        )

    def action_continue(self) -> None:
        # get the updated values from the input fields
        for input, segment in zip(self._inputs, self._segments):
            segment.description = input.value

        self.app.exit(True)

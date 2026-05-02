from pathlib import Path

from ezio.domain.generator.frontend import replace_html_title


def test_title_is_replaced(data_dir: Path, tempdir: Path) -> None:
    html_path = (data_dir / "index.html").copy(tempdir / "index.html")

    replace_html_title(html_path, "My Title")

    with open(html_path) as f:
        html = f.read()

    assert "<title>My Title</title>" in html
    assert "ezio" not in html.lower()

# Maintainer: Pascal Sommer
pkgname=ezio
pkgver=0.0.1
pkgrel=1
pkgdesc="Static site generator for GPS routes"
arch=('x86_64') # limited to x86_64 because of python-pillow
url="https://github.com/Pascal-So/ezio"
license=('AGPL-3.0-or-later')
depends=(
    python
    python-gpxpy
    python-pillow
    python-requests
    python-rich
    # todo: geojson
)
makedepends=(
    python-build
    python-installer
    python-uv-build
)
source=("${pkgname}-${pkgver}::git+${url}.git")
sha256sums=('SKIP') # todo

build() {
    cd "${pkgname}-${pkgver}"
    python -m build --wheel --no-isolation
}

package() {
    cd "${pkgname}-${pkgver}"
    python -m installer --destdir="${pkgdir}" dist/*.whl
}

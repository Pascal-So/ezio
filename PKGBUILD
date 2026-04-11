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

_archive="${pkgname}-v${pkgver}"
source=(
    "${url}/archive/v${pkgver}/${pkgname}-v${pkgver}.tar.gz"
    "${url}/releases/download/v${pkgver}/frontend.zip"
)
sha256sums=(
    "e106b96ad28aa44ffc411ef181ba9322c3e7b7bf69e82dded31a8b5de78b377e"
    "6980d507e114959ce80fedfad671063b25bf3605f44cf799f6e07dc4735c6f52"
)

prepare() {
    ls
    cd "${pkgname}-${pkgver}"
    # copy the frontend into the package
    cp -r "../dist" "src/${pkgname}/domain/generator/frontend/dist"
}

build() {
    cd "${pkgname}-${pkgver}"
    python -m build --wheel --no-isolation
}

package() {
    cd "${pkgname}-${pkgver}"
    python -m installer --destdir="${pkgdir}" dist/*.whl
}

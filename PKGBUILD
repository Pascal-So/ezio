# Maintainer: Pascal Sommer
pkgname=ezio
pkgver=0.1.0
pkgrel=1
pkgdesc="Static site generator for GPS routes"
arch=(any)
url="https://github.com/Pascal-So/ezio"
license=('AGPL-3.0-or-later')
depends=(
    python
    python-gpxpy
    python-pillow
    python-requests
    python-rich
    python-pydantic
)
makedepends=(
    python-build
    python-installer
    python-uv-build
    sed
    findutils
)

_geojson_version="0.3.2"
source=(
    "${url}/archive/v${pkgver}/${pkgname}-v${pkgver}.tar.gz"
    "${url}/releases/download/v${pkgver}/frontend.zip"

    # HACK: for now we just vendor pydantic-geojson into the package because
    # there is no arch package available for it yet.
    "https://github.com/gb-libs/pydantic-geojson/archive/refs/tags/${_geojson_version}.tar.gz"
)
sha256sums=(
    "c1fb3ae167710001a8bc8f827dc73a319ee0ebab8c1f18afb47b45a8f675d94c"
    "2c4daff88949e5a749c16c028c4b3ee451583a1185bea8034405cf26ee6721d0"
    "3957a8c532885c9843430b4ba1fe705e5a3a0f35a405eb318c4f459f7b36b61a"
)

prepare() {
    ls
    cd "${pkgname}-${pkgver}"

    # vendor pydantic-geojson
    find ./src -type f -print0 | xargs -0 sed -i 's/^from pydantic_geojson/from ezio.pydantic_geojson/'
    cp -r "../pydantic-geojson-${_geojson_version}/pydantic_geojson" "src/${pkgname}/pydantic_geojson"

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

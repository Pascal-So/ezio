# Maintainer: Pascal Sommer
pkgname=ezio
pkgver=1.0.0
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
    python-textual
)
makedepends=(
    python-build
    python-installer
    python-uv-build
    sed
    findutils
)
optdepends=('brotli: precompress files for efficient static file serving')

_geojson_version="0.3.2"
source=(
    "${url}/archive/v${pkgver}/${pkgname}-v${pkgver}.tar.gz"
    "${url}/releases/download/v${pkgver}/frontend.zip"

    # HACK: for now we just vendor pydantic-geojson into the package because
    # there is no arch package available for it yet.
    "https://github.com/gb-libs/pydantic-geojson/archive/refs/tags/${_geojson_version}.tar.gz"
)
sha256sums=(
    "de4e2853750c48ebe38eda0d664d3f0eabe756a2b7d1cb49e08d9186846f14b6"
    "ff2695255ac72aee648bd714d5fb5515242e0029c441035079b9141cf9f84711"
    "3957a8c532885c9843430b4ba1fe705e5a3a0f35a405eb318c4f459f7b36b61a"
)

prepare() {
    ls
    cd "${pkgname}-${pkgver}"

    # vendor pydantic-geojson
    find ./src -type f -print0 | xargs -0 sed -i -E 's/^(from|import) pydantic_geojson/\1 ezio.pydantic_geojson/'
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

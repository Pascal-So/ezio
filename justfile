frontend-path-in-package := "src/ezio/domain/generator/frontend/dist"

check:
    uv run pytest
    uv run mypy . --strict
    uv run ruff check
    # todo: eslint & tests

# Run the frontend in development mode with hot reloading
[working-directory: 'frontend']
dev:
    npm ci
    npm run dev

[working-directory: 'frontend']
build-frontend:
    npm ci
    npm run build

# Create a zip archive of the compiled frontend. Assumes that the frontend has already been build.
[working-directory: 'frontend']
zip-frontend:
    7z a -tzip frontend.zip dist/assets/ dist/index.html

# Build a "wheel" distribution of the python package that includes the compiled frontend
build-wheel: build-frontend
    rm -rf "{{ frontend-path-in-package }}"
    mkdir -p "{{ frontend-path-in-package }}"
    cp -r frontend/dist/assets frontend/dist/index.html "{{ frontend-path-in-package }}"
    uv build --verbose --wheel

# Build the arch package based on a GitHub release. Edit PKGBUILD to bump the version
build-arch-package:
    #!/usr/bin/env bash
    TMPDIR=$(mktemp -d)
    cp PKGBUILD $TMPDIR
    cd $TMPDIR
    makepkg -s

    echo The package is located in $PWD/ezio*.pkg.tar.zst

# Remove all build artifacts and caches
[confirm]
clean:
    rm -rf "{{ frontend-path-in-package }}"
    rm -rf .venv/ dist/
    rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
    rm -rf ./**/__pycache__/
    rm -rf frontend/node_modules/ frontend/dist/

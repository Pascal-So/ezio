# Changelog

## v1.0.0 - 2026-07-25

* Make altitude plots interactive: hover over the plot to highlight the
  corresponding location on the map.
* Altitude plots are now rendered live in the frontend instead of rendering to
  SVGs in the backend.
* Store tracks as one combined geojson rather than one file per segment
* Store bounding box in geojson instead of data.json
* Precompress geojson with brotli if available
* Bugfixes for tracks without elevation data
* Add version field to data.json. For now the version is set to 1

## v0.2.0 - 2026-07-22

* Plot elevation
* Improve `--help` text
* Improve error message when no tracks were found
* Add GeoJSON support
* Allow generated website to be placed in a non-root direcotory
* Don't re-generate photos that are already present in the output directory
* Accept multiple input paths which can now be either directories or files
* Show more information during the generator process (nr. photos per day, nr. skipped tiles)
* Print total distance upon wizard completion

## v0.1.0 - 2026-05-02

Initial release

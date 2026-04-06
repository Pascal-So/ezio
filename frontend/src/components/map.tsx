import type { FeatureCollection, MultiLineString, Point } from "geojson";
import L, { LatLng, latLng, LatLngBounds, latLngBounds } from "leaflet";
import { useEffect, useMemo, useRef, type RefObject } from "react";
import {
  TileLayer,
  MapContainer,
  GeoJSON,
  Popup,
  useMap,
  Pane,
} from "react-leaflet";

import type { Segment, SegmentGeometry } from "../types";

function tileToLatLng(x: number, y: number, zoom: number): LatLng {
  const n = Math.pow(2, zoom);
  const lonDeg = (x / n) * 360.0 - 180.0;
  const latRad = Math.atan(Math.sinh(Math.PI * (1 - (2 * y) / n)));
  const latDeg = (latRad * 180) / Math.PI;
  return latLng(latDeg, lonDeg);
}

function getBounds(): LatLngBounds {
  const zoom = 5;
  const minX = 16;
  const minY = 10;
  const maxX = 19;
  const maxY = 13;

  const corner1 = tileToLatLng(minX, minY, zoom);
  const corner2 = tileToLatLng(maxX + 1, maxY + 1, zoom);
  return latLngBounds(corner1, corner2);
}

type MapViewProps = {
  segments: Segment[];
  selectedSegment: number | null;
  setSelectedSegment: (id: number | null) => void;
  backgroundSegments: FeatureCollection<MultiLineString>[];
  stays: FeatureCollection<Point> | null;
};

function MapView(props: MapViewProps) {
  return (
    <>
      <div id="popup-container" />
      <MapContainer
        center={[42.5, 26.2]}
        zoom={8}
        minZoom={6}
        maxZoom={9}
        maxBounds={getBounds()}
      >
        <MapContents {...props} />
      </MapContainer>
    </>
  );
}

function MapContents({
  segments,
  selectedSegment,
  setSelectedSegment,
  backgroundSegments,
  stays,
}: MapViewProps) {
  const map = useMap();
  const canvasRenderer = useMemo(
    () => L.canvas({ padding: 0.5, tolerance: 15 }),
    [],
  );

  useEffect(() => {
    map.createPane("fixedpane", document.getElementById("popup-container")!);
  }, [map]);

  const ref = useRef<L.GeoJSON>(null);

  useEffect(() => {
    if (!ref.current) {
      return;
    }
    // Select the first segment when we first open the map
    ref.current.openPopup();
  }, [ref]);

  return (
    <>
      <TileLayer
        attribution='Map Tiles: <a href="https://www.jawg.io/en/">jawgmaps</a>, Map Data: <a href="https://osm.org/copyright/">© OpenStreetMap contributors</a>'
        url="img/tiles/{z}-{x}-{y}.png"
      />

      {segments.map(
        // first render all of the unselected segments
        (segment, index) =>
          selectedSegment !== index  && (
            <Segment
              key={index}
              segment={segment.geometry}
              ref={index === 0 ? ref : undefined}
              index={index}
              isSelected={false}
              select={() => setSelectedSegment(index)}
              deselect={() => setSelectedSegment(null)}
              renderer={canvasRenderer}
            />
          ),
      )}

      {selectedSegment !== null && (
        <Segment
          segment={segments[selectedSegment].geometry}
          ref={selectedSegment === 0 ? ref : undefined}
          index={selectedSegment}
          isSelected={true}
          select={() => setSelectedSegment(selectedSegment)}
          deselect={() => setSelectedSegment(null)}
          renderer={canvasRenderer}
        />
      )}

      {false && (
        <Pane name={"background-stuff"} className={"pane-background"}>
          {backgroundSegments.map((segment) => (
            <GeoJSON
              interactive={false}
              data={segment}
              style={{
                color: "#bbb",
                opacity: 0.7,
                weight: 2,
              }}
            ></GeoJSON>
          ))}

          {stays !== null && (
            <GeoJSON
              interactive={false}
              data={stays}
              pointToLayer={(_geoJsonPoint, latlng) => {
                return L.marker(latlng, {
                  icon: L.icon({
                    iconUrl: "img/star.png",
                    iconSize: [26, 26],
                  }),
                  interactive: false,
                });
              }}
            />
          )}
        </Pane>
      )}
    </>
  );
}

type SegmentProps = {
  segment: SegmentGeometry;
  ref: RefObject<L.GeoJSON | null> | undefined;
  index: number;
  isSelected: boolean;
  select: () => void;
  deselect: () => void;
  renderer: L.Renderer;
};

function Segment({
  segment,
  ref,
  index,
  isSelected,
  select,
  deselect,
  renderer,
}: SegmentProps) {
  return (
    <GeoJSON
      key={index}
      pathOptions={{ renderer: renderer }}
      data={segment}
      ref={ref}
      eventHandlers={{
        popupopen: select,
        popupclose: deselect,
      }}
      style={{
        color: isSelected ? "#fd7536" : "#3388ff",
        opacity: 0.7,
        weight: isSelected ? 7 : 4,
      }}
    >
      <Popup pane="fixedpane" className="fixup">
      </Popup>
   </GeoJSON>
  );
}

export default MapView;

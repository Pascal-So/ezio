import type { FeatureCollection, MultiLineString, Point } from "geojson";
import L, { LatLng, latLng, LatLngBounds, latLngBounds } from "leaflet";
import { useEffect } from "react";
import {
  TileLayer,
  MapContainer,
  GeoJSON,
  useMap,
  LayerGroup,
} from "react-leaflet";

import type { BoundingBox, Segment, SegmentGeometry } from "../types";

type MapViewProps = {
  segments: Segment[];
  totalBoundingBox: BoundingBox;
  selectedSegment: number | null;
  setSelectedSegment: (id: number | null) => void;
  backgroundSegments: FeatureCollection<MultiLineString>[];
  stays: FeatureCollection<Point> | null;
  maxZoom: number;
};

function boundingBoxCenter(bbox: BoundingBox): LatLng {
  return latLng(
    (bbox.minLat + bbox.maxLat) / 2,
    (bbox.minLng + bbox.maxLng) / 2,
  );
}

function boundingBoxToLeaflet(
  bbox: BoundingBox,
  padding: LatLng,
): LatLngBounds {
  return latLngBounds(
    [bbox.minLat - padding.lat, bbox.minLng - padding.lng],
    [bbox.maxLat + padding.lat, bbox.maxLng + padding.lng],
  );
}

function MapView(props: MapViewProps) {
  return (
    <>
      <MapContainer
        center={boundingBoxCenter(props.totalBoundingBox)}
        zoom={8}
        minZoom={6}
        maxZoom={props.maxZoom}
        maxBounds={boundingBoxToLeaflet(props.totalBoundingBox, latLng(1, 1))}
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
  maxZoom,
}: MapViewProps) {
  const map = useMap();

  useEffect(() => {
    // deselect segments when clicking on the background
    map.on("click", () => setSelectedSegment(null));
  }, [map]);

  useEffect(() => {
    // pan to selected segment when that changes
    if (selectedSegment !== null) {
      const bounds = boundingBoxToLeaflet(
        segments[selectedSegment].boundingBox,
        latLng(0, 0),
      );
      map.flyToBounds(bounds, { maxZoom: maxZoom });
    }
  }, [map, selectedSegment, segments]);

  return (
    <>
      <LayerGroup
        eventHandlers={{
          click: () => {
            setSelectedSegment(null);
          },
        }}
      >
        <TileLayer
          attribution='Map Tiles: <a href="https://www.jawg.io/en/">jawgmaps</a>, Map Data: <a href="https://osm.org/copyright/">© OpenStreetMap contributors</a>'
          url="img/tiles/{z}-{x}-{y}.png"
        />
      </LayerGroup>

      {backgroundSegments.map((segment, index) => (
        <BackgroundSegment key={index} segment={segment} index={index} />
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

      {segments.map(
        // first render all of the unselected segments
        (segment, index) =>
          selectedSegment !== index && (
            <Segment
              key={index}
              segment={segment.geometry}
              index={index}
              isSelected={false}
              select={() => setSelectedSegment(index)}
            />
          ),
      )}

      {selectedSegment !== null && (
        // then render the selected segment in front of the others
        <Segment
          segment={segments[selectedSegment].geometry}
          index={selectedSegment}
          isSelected={true}
          select={() => {}}
        />
      )}
    </>
  );
}

type SegmentProps = {
  segment: SegmentGeometry;
  index: number;
  isSelected: boolean;
  select: () => void;
};

function Segment({ segment, index, isSelected, select }: SegmentProps) {
  return (
    <>
      <GeoJSON
        key={index}
        data={segment}
        interactive={false}
        style={{
          color: isSelected ? "#fd7536" : "#3388ff",
          opacity: 0.7,
          weight: isSelected ? 6 : 4,
        }}
      ></GeoJSON>

      {/* Invisible clickable segment with larger line weight. We use
       *  this to make it easier to click the thin lines.
       */}
      <GeoJSON
        key={index + 10000}
        data={segment}
        eventHandlers={{
          click: (ev) => {
            L.DomEvent.stopPropagation(ev);
            select();
          },
        }}
        style={{
          opacity: 0.0,
          weight: 21,
        }}
      ></GeoJSON>
    </>
  );
}

type BackgroundSegmentProps = {
  segment: SegmentGeometry;
  index: number;
};

function BackgroundSegment({ segment, index }: BackgroundSegmentProps) {
  return (
    <GeoJSON
      key={index}
      interactive={false}
      data={segment}
      style={{
        color: "#bbb",
        opacity: 0.7,
        weight: 2,
      }}
    ></GeoJSON>
  );
}

export default MapView;

import type { FeatureCollection, GeoJsonObject, Point } from "geojson";
import L, { LatLng, latLng, LatLngBounds, latLngBounds } from "leaflet";
import { useEffect, useImperativeHandle, type Ref } from "react";
import {
  TileLayer,
  MapContainer,
  GeoJSON,
  useMap,
  LayerGroup,
} from "react-leaflet";

import type { BackgroundSegmentGeometry, BoundingBox, Segment } from "../types";

export type PannableMap = { panTo: (segmentIndex: number) => void };

type MapViewProps = {
  segments: Segment[];
  totalBoundingBox: BoundingBox;
  selectedSegment: number | null;
  setSelectedSegment: (id: number | null) => void;
  backgroundSegments: BackgroundSegmentGeometry[];
  stays: FeatureCollection<Point> | null;
  maxZoom: number;
  ref: Ref<PannableMap>;
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

const minZoomLevel = 5;

function MapView(props: MapViewProps) {
  return (
    <>
      <MapContainer
        center={boundingBoxCenter(props.totalBoundingBox)}
        zoom={6}
        minZoom={minZoomLevel}
        maxZoom={props.maxZoom}
        maxBounds={boundingBoxToLeaflet(props.totalBoundingBox, latLng(2, 2))}
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
  ref,
}: MapViewProps) {
  const map = useMap();

  useEffect(() => {
    // deselect segments when clicking on the background
    map.on("click", () => setSelectedSegment(null));
  }, [map]);

  useImperativeHandle(ref, () => {
    return {
      // add an imperative method to MapView refs for panning to a segment
      panTo(segmentIndex) {
        const bounds = boundingBoxToLeaflet(
          segments[segmentIndex].boundingBox,
          latLng(0, 0),
        );
        map.flyToBounds(bounds, {
          maxZoom: maxZoom,
          duration: 0.5,
        });
      },
    };
  }, [segments, map]);

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
  segment: GeoJsonObject;
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
  segment: GeoJsonObject;
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
        opacity: 0.45,
        weight: 2,
      }}
    ></GeoJSON>
  );
}

export default MapView;

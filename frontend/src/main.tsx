import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import 'leaflet/dist/leaflet.css';
import "yet-another-react-lightbox/styles.css";
import "yet-another-react-lightbox/plugins/thumbnails.css";
import "./index.css";
import App from "./App.tsx";
import type { FeatureCollection, MultiLineString, Point } from "geojson";
import type { Segment, NetworkData, SlideWithDate } from "./types.ts";

const [segments, photos, backgroundSegments, stays] = await getData();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App
      segments={segments}
      photos={photos}
      backgroundSegments={backgroundSegments}
      stays={stays}
    />
  </StrictMode>,
);

async function getData(): Promise<
  [
    Segment[],
    SlideWithDate[],
    FeatureCollection<MultiLineString>[],
    FeatureCollection<Point> | null,
  ]
> {
  const data: NetworkData = await fetch("data.json").then((res) => res.json());

  const geojsons = await Promise.all(
    data.segments.map((segment) =>
      fetch(`tracks/${segment.date}.geojson`).then((res) => res.json()),
    ),
  );

  const backgroundSegments = await Promise.all(
    (data.backgroundSegments || []).map((segment) =>
      fetch(`background-segments/${segment}.geojson`).then((res) => res.json()),
    ),
  );

  const staysResponse = await fetch("stays.geojson");
  let stays: FeatureCollection<Point> | null = null;
  if (staysResponse.ok) {
    stays = await staysResponse.json();
  }

  const segments: Segment[] = [];

  let idx = 0;
  for (const segment of data.segments) {
    segments.push({
      ...segment,
      imageIndex: data.photos.findIndex((photo) => photo.n === segment.featured_photo),
      geometry: geojsons[idx],
    });
    idx += 1;
  }

  const photos = data.photos.map((photo) => ({
    src: `img/photos/large/${photo.n}`,
    width: photo.w,
    height: photo.h,
    srcSet: [
      { src: `img/photos/large/${photo.n}`, width: photo.w, height: photo.h },
      { src: `img/photos/thumb/${photo.n}`, width: photo.tw, height: photo.th },
    ],
    date: photo.date,
  }));

  return [segments, photos, backgroundSegments, stays];
}

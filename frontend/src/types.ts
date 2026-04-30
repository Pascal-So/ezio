import type { FeatureCollection, MultiLineString, Point } from "geojson";

export type SegmentGeometry = FeatureCollection<MultiLineString>;
export type PointsGeometry = FeatureCollection<Point>;

export type Segment = SegmentInfo & {
  imageIndex: number | null;
  geometry: SegmentGeometry;
};

export type SegmentInfo = {
  date: string;
  description: string;

  /** Length of the segment in kilometres*/
  dist: number;

  /** Climb in metres*/
  climb: number | undefined;

  featuredPhotoFilename: string | null;

  boundingBox: BoundingBox;
};

export type Resolution = {
  x: number;
  y: number;
};

export type PhotoInfo = {
  filename: string;
  date: string;
  resolution: Resolution;
  thumbnailResolution: Resolution;
};

export type BoundingBox = {
  minLat: number;
  maxLat: number;
  minLng: number;
  maxLng: number;
};

export type Data = {
  segments: Segment[];
  photos: PhotoInfo[];
  backgroundSegments: SegmentGeometry[];
  stays: PointsGeometry | null;
  totalBoundingBox: BoundingBox;
  maxZoomLevel: number;
};

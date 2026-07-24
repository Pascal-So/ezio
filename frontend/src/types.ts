import type {
  FeatureCollection,
  LineString,
  MultiLineString,
  Point,
} from "geojson";

export type SegmentGeometries = FeatureCollection<MultiLineString>;
export type SegmentGeometry = MultiLineString;
export type BackgroundSegmentGeometry = FeatureCollection<
  MultiLineString | LineString
>;
export type PointsGeometry = FeatureCollection<Point>;

export type Segment = SegmentInfo & {
  imageIndex: number | null;
  geometry: SegmentGeometry;
  boundingBox: BoundingBox;
};

export type SegmentInfo = {
  date: string;
  description: string;

  /** Length of the segment in kilometres*/
  dist: number;

  /** Climb in metres*/
  climb: number | undefined;

  featuredPhotoFilename: string | null;
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
  backgroundSegments: BackgroundSegmentGeometry[];
  stays: PointsGeometry | null;
  totalBoundingBox: BoundingBox;
  maxZoomLevel: number;
};

import type { FeatureCollection, MultiLineString } from "geojson";
import type { SlideImage } from "yet-another-react-lightbox";

type JsonSegment = {
  date: string;
  dist_km: number;
  desc: string;
  featured_photo: string;
};

export type Segment = JsonSegment & {
  imageIndex: number;
  geometry: FeatureCollection<MultiLineString>;
};

export type SlideWithDate = SlideImage & { date: string };

export type NetworkData = {
  segments: JsonSegment[];
  photos: {
    date: string;
    n: string;
    w: number;
    h: number;
    tw: number;
    th: number;
  }[];
  backgroundSegments: string[];
};

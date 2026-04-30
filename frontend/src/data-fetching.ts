import * as z from "zod/mini";
import type {
  BoundingBox,
  Data,
  PhotoInfo,
  PointsGeometry,
  Segment,
  SegmentGeometry,
  SegmentInfo,
} from "./types";

/**
 * Fetch all the data from the server and transform it into the format
 * that we need in the frontend.
 */
export async function fetchAllData(): Promise<Data> {
  const rawData = await fetch("data.json").then((res) => res.json());
  const data: JsonData = parseData(rawData);

  const [geojsons, backgroundSegments, stays] = await Promise.all([
    fetchSegments(data),
    fetchBackgroundSegments(data),
    fetchStays(),
  ]);

  const segments: Segment[] = [];

  let idx = 0;
  for (const segmentInfo of data.segments) {
    let imageIndex = null;
    // find the featured photo for this segment
    // TODO: avoid the n^2
    if (segmentInfo.featuredPhotoFilename !== null) {
      imageIndex = data.photos.findIndex(
        (photo) => photo.filename === segmentInfo.featuredPhotoFilename,
      );
    }

    // If no featured photo has been set, we default to the first
    // photo of that day.
    if (imageIndex === null || imageIndex === -1) {
      imageIndex = data.photos.findIndex(
        (photo) => photo.date === segmentInfo.date,
      );
    }

    if (imageIndex === -1) {
      imageIndex = null;
    }

    let segment = {
      ...segmentInfo,
      imageIndex,
      geometry: geojsons[idx],
    };
    if (imageIndex !== null) {
      segment.featuredPhotoFilename = data.photos[imageIndex].filename;
    }

    segments.push(segment);
    idx += 1;
  }

  return {
    segments,
    photos: data.photos,
    backgroundSegments,
    stays,
    totalBoundingBox: data.totalBoundingBox,
  };
}

export function thumbnailPath(filename: string): string {
  return `img/photos/thumb/${filename}`;
}

export function photoPath(filename: string): string {
  return `img/photos/large/${filename}`;
}

function parseData(raw: any): JsonData {
  const resSchema = z.object({ x: z.number(), y: z.number() });
  const photoInfoSchema = z.object({
    filename: z.string(),
    date: z.string(),
    res: resSchema,
    thumb_res: resSchema,
  });
  const boundingBoxSchema = z.object({
    min_lat: z.number(),
    min_lng: z.number(),
    max_lat: z.number(),
    max_lng: z.number(),
  });
  const segmentInfoSchema = z.object({
    date: z.string(),
    description: z.optional(z.string()),
    dist_km: z.number(),
    climb_m: z.optional(z.number()),
    featured_photo: z.nullable(z.string()),
    bounding_box: boundingBoxSchema,
  });
  const schema = z.object({
    segments: z.array(segmentInfoSchema),
    photos: z.array(photoInfoSchema),
    background_segments: z.optional(z.array(z.string())),
    total_bounding_box: boundingBoxSchema,
  });

  const parsed = schema.parse(raw);

  // We manually convert the names from snake case to camel case because zod
  // doesn't have that built in and also it's not worth it to do something
  // fancy here. We still get zod type checking tho.
  return {
    segments: parsed.segments.map((seg) => ({
      date: seg.date,
      description: seg.description || "",
      dist: seg.dist_km,
      climb: seg.climb_m,
      featuredPhotoFilename: seg.featured_photo || null,
      boundingBox: convertBoundingBox(seg.bounding_box),
    })),
    photos: parsed.photos.map((photo) => ({
      filename: photo.filename,
      date: photo.date,
      resolution: { ...photo.res },
      thumbnailResolution: { ...photo.thumb_res },
    })),
    backgroundSegments: parsed.background_segments || [],
    totalBoundingBox: convertBoundingBox(parsed.total_bounding_box),
  };
}

function convertBoundingBox(bbox: {
  min_lat: number;
  min_lng: number;
  max_lat: number;
  max_lng: number;
}): BoundingBox {
  return {
    minLat: bbox.min_lat,
    minLng: bbox.min_lng,
    maxLat: bbox.max_lat,
    maxLng: bbox.max_lng,
  };
}

async function fetchSegments(data: JsonData): Promise<SegmentGeometry[]> {
  return await Promise.all(
    data.segments.map((segment) =>
      fetch(`tracks/${segment.date}.geojson`).then((res) => res.json()),
    ),
  );
}

async function fetchBackgroundSegments(
  data: JsonData,
): Promise<SegmentGeometry[]> {
  return await Promise.all(
    (data.backgroundSegments || []).map((segment) =>
      fetch(`background-segments/${segment}.geojson`).then((res) => res.json()),
    ),
  );
}

async function fetchStays(): Promise<PointsGeometry | null> {
  const staysResponse = await fetch("stays.geojson");
  if (staysResponse.ok) {
    return await staysResponse.json();
  }

  return null;
}

type JsonData = {
  segments: SegmentInfo[];
  photos: PhotoInfo[];
  backgroundSegments: string[];
  totalBoundingBox: BoundingBox;
};

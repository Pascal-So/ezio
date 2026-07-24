import * as z from "zod/mini";
import type {
  BackgroundSegmentGeometry,
  BoundingBox,
  Data,
  PhotoInfo,
  PointsGeometry,
  Segment,
  SegmentGeometries,
  SegmentGeometry,
  SegmentInfo,
} from "./types";

/**
 * Fetch all the data from the server and transform it into the format
 * that we need in the frontend.
 */
export async function fetchAllData(): Promise<Data> {
  const rawData = await fetchJson("data.json");
  const data: JsonData = parseData(rawData);

  const [segmentGeometries, backgroundSegments, stays] = await Promise.all([
    fetchSegmentGeometries(),
    fetchBackgroundSegments(data),
    fetchStays(),
  ]);

  const segments: Segment[] = [];

  const segmentGeometryByDate = new Map<
    string,
    [SegmentGeometry, BoundingBox]
  >();
  for (const feature of segmentGeometries.features) {
    if (typeof feature.id !== "string" || feature.bbox === undefined) {
      console.log(
        `skipping segment feature with id ${feature.id} and bounding box ${feature.bbox}`,
      );
      continue;
    }
    const bbox = convertBboxFromGeojson(feature.bbox);

    segmentGeometryByDate.set(feature.id, [feature.geometry, bbox]);
  }

  const photoIndexByFilename = new Map<string, number>();
  for (const [index, photo] of data.photos.entries()) {
    photoIndexByFilename.set(photo.filename, index);
  }

  const firstPhotoIndexByDate = new Map<string, number>();
  for (const [index, photo] of data.photos.entries()) {
    if (!firstPhotoIndexByDate.has(photo.date)) {
      firstPhotoIndexByDate.set(photo.date, index);
    }
  }

  let idx = 0;
  for (const segmentInfo of data.segments) {
    let imageIndex: number | null = null;

    // find the featured photo for this segment
    if (segmentInfo.featuredPhotoFilename !== null) {
      imageIndex =
        photoIndexByFilename.get(segmentInfo.featuredPhotoFilename) ?? null;
    }

    // If no featured photo has been set, we default to the first
    // photo of that day.
    if (imageIndex === null) {
      imageIndex = firstPhotoIndexByDate.get(segmentInfo.date) ?? null;
    }

    let geometry = segmentGeometryByDate.get(segmentInfo.date);
    if (geometry === undefined) {
      console.warn(
        `skipping segment ${segmentInfo.date} because the geojson data does not contain that feature`,
      );
      continue;
    }
    let segment = {
      ...segmentInfo,
      boundingBox: geometry[1],
      imageIndex,
      geometry: geometry[0],
    };
    if (imageIndex !== null) {
      segment.featuredPhotoFilename = data.photos[imageIndex].filename;
    }

    segments.push(segment);
    idx += 1;
  }

  // Try to get the combined bounding box from the geojson, falling back to
  // the field in data.json.
  let totalBoundingBox =
    segmentGeometries.bbox !== undefined
      ? convertBboxFromGeojson(segmentGeometries.bbox)
      : data.totalBoundingBox;

  if (totalBoundingBox === undefined) {
    console.warn(
      "Could not get bounding box from geojson or data.json, falling back to hardcoded value instead",
    );
    totalBoundingBox = {
      minLng: -179,
      minLat: -86,
      maxLng: 179,
      maxLat: 86,
    };
  }

  return {
    segments,
    photos: data.photos,
    backgroundSegments,
    stays,
    totalBoundingBox,
    maxZoomLevel: data.maxZoomLevel,
  };
}

function convertBboxFromGeojson(geojson_bbox: number[]): BoundingBox {
  switch (geojson_bbox.length) {
    case 4:
      return {
        minLng: geojson_bbox[0],
        minLat: geojson_bbox[1],
        maxLng: geojson_bbox[2],
        maxLat: geojson_bbox[3],
      };
    case 6:
      return {
        minLng: geojson_bbox[0],
        minLat: geojson_bbox[1],
        maxLng: geojson_bbox[3],
        maxLat: geojson_bbox[4],
      };
  }

  throw new Error(`bounding box must contain 4 or 6 numbers: ${geojson_bbox}`);
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
  });
  const schema = z.object({
    segments: z.array(segmentInfoSchema),
    photos: z.array(photoInfoSchema),
    background_segments: z.optional(z.array(z.string())),
    total_bounding_box: boundingBoxSchema,
    max_zoom_level: z.number(),
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
    })),
    photos: parsed.photos.map((photo) => ({
      filename: photo.filename,
      date: photo.date,
      resolution: { ...photo.res },
      thumbnailResolution: { ...photo.thumb_res },
    })),
    backgroundSegments: parsed.background_segments || [],
    totalBoundingBox: convertBoundingBox(parsed.total_bounding_box),
    maxZoomLevel: parsed.max_zoom_level,
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

async function fetchSegmentGeometries(): Promise<SegmentGeometries> {
  return await fetchJson("segments.geojson");
}

async function fetchBackgroundSegments(
  data: JsonData,
): Promise<BackgroundSegmentGeometry[]> {
  const backgroundSegments = await Promise.all(
    (data.backgroundSegments || []).map((segment) =>
      fetchJson(`background-segments/${segment}.geojson`).catch((e) => {
        console.warn(e);
        return null;
      }),
    ),
  );

  // We just skip missing background segment since we've already
  // logged the error.
  return backgroundSegments.filter((segment) => segment !== null);
}

async function fetchStays(): Promise<PointsGeometry | null> {
  return await fetchJson("stays.geojson").catch((e) => {
    console.warn(e);
    return null;
  });
}

async function fetchJson(url: string): Promise<any> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(
      `Cannot load ${url}: Request failed with status ${res.status} - ${res.statusText}`,
    );
  }
  return res.json().catch((e) => {
    throw new Error(`Cannot parse JSON from ${url}: ${e}`);
  });
}
type JsonData = {
  segments: SegmentInfo[];
  photos: PhotoInfo[];
  backgroundSegments: string[];
  totalBoundingBox?: BoundingBox;
  maxZoomLevel: number;
};

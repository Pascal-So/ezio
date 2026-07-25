import { describe, expect, test } from "vitest";
import { parseData } from "./data-fetching";

function getData(): any {
  return {
    segments: [
      {
        date: "2026-04-21",
        description: "Segment A",
        dist_km: 100,
        climb_m: 10,
        featured_photo: null,
        nr_photos: 6,
      },
    ],
    photos: [
      {
        filename: "photo.webp",
        date: "2026-04-21",
        res: {
          x: 1920,
          y: 1282,
        },
        thumb_res: {
          x: 250,
          y: 167,
        },
      },
    ],
    background_segments: [],
    max_zoom_level: 10,
    total_bounding_box: { min_lat: 1, max_lat: 1, min_lng: 1, max_lng: 1 },
  };
}

describe("parseData", () => {
  test("rejects invalid data", () => {
    expect(() => parseData({})).toThrow();
    expect(() =>
      parseData({
        segments: [],
        photos: [],
      }),
    ).toThrow();
  });

  test("parses normal data", () => {
    const data = getData();
    const parsed = parseData(data);

    expect(parsed).toHaveProperty("segments[0].date", "2026-04-21");
    expect(parsed).toHaveProperty("segments[0].climb", 10);
    expect(parsed).toHaveProperty("photos[0].thumbnailResolution.x", 250);
  });

  test("parses data without climb", () => {
    const data = getData();

    data.segments[0].climb_m = undefined;
    expect(parseData(data).segments[0].climb).toBeUndefined();

    data.segments[0].climb_m = null;
    expect(parseData(data).segments[0].climb).toBeUndefined();

    delete data.segments[0].climb_m;
    expect(parseData(data).segments[0].climb).toBeUndefined();
  });

  test("ignores unknown fields", () => {
    const data = getData();
    data['asdf'] = 2;
    const parsed = parseData(data);
    expect(parsed.maxZoomLevel).toBe(10)
  });
});

import {
  type FC,
  type KeyboardEvent,
  useCallback,
  useState,
  useRef,
  useEffect,
} from "react";
import type { FeatureCollection, MultiLineString, Point } from "geojson";

import type { BoundingBox, PhotoInfo, Segment } from "./types";
import InfoOverlay from "./components/info-overlay";
import MapView, { type PannableMap } from "./components/map";
import PhotoGallery from "./components/photo-gallery";

type AppProps = {
  segments: Segment[];
  photos: PhotoInfo[];
  backgroundSegments: FeatureCollection<MultiLineString>[];
  stays: FeatureCollection<Point> | null;
  totalBoundingBox: BoundingBox;
  maxZoomLevel: number;
};

const App: FC<AppProps> = ({
  segments,
  photos,
  backgroundSegments,
  stays,
  totalBoundingBox,
  maxZoomLevel,
}: AppProps) => {
  const [selectedSegment, setSelectedSegment] = useState<number | null>(0);
  const [imageIndex, setImageIndex] = useState<number | null>(null);
  const mapRef = useRef<PannableMap>(null);

  const move = useCallback(
    (offset: number) => () => {
      setSelectedSegment((sel) => {
        if (sel === null) {
          return null;
        }

        const nextTrack = sel + offset;
        if (nextTrack >= 0 && nextTrack < segments.length) {
          return nextTrack;
        } else {
          return sel;
        }
      });
    },
    [setSelectedSegment],
  );

  const keyDown = useCallback(
    (ev: KeyboardEvent) => {
      let forward: boolean;

      if (ev.key === "n") {
        forward = true;
      } else if (ev.key === "p") {
        forward = false;
      } else {
        return;
      }
      ev.preventDefault();
      move(forward ? 1 : -1)();
    },
    [move],
  );

  function selectSegmentByDate(date: string) {
    const segment = segments.findIndex((s) => s.date === date);
    if (segment !== -1) {
      setSelectedSegment(segment);
    }
  }

  useEffect(() => {
    if (mapRef.current && selectedSegment !== null) {
      mapRef.current.panTo(selectedSegment);
    }
  }, [selectedSegment]);

  return (
    <div onKeyDown={keyDown}>
      {selectedSegment !== null && imageIndex === null ? (
        <InfoOverlay
          openPhotoGallery={() =>
            setImageIndex(segments[selectedSegment].imageIndex)
          }
          segment={segments[selectedSegment]}
          moveToPrevSegment={move(-1)}
          moveToNextSegment={move(1)}
        />
      ) : null}

      <PhotoGallery
        photos={photos}
        imageIndex={imageIndex}
        setImageIndex={setImageIndex}
        selectSegmentByDate={selectSegmentByDate}
      />

      <MapView
        segments={segments}
        selectedSegment={selectedSegment}
        setSelectedSegment={setSelectedSegment}
        backgroundSegments={backgroundSegments}
        stays={stays}
        totalBoundingBox={totalBoundingBox}
        maxZoom={maxZoomLevel}
        ref={mapRef}
      />
    </div>
  );
};

export default App;

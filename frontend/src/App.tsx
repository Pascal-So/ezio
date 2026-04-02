import {
  type FC,
  type KeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import type { FeatureCollection, MultiLineString, Point } from "geojson";
import { LatLng, latLng, LatLngBounds, latLngBounds } from "leaflet";
import {
  TileLayer,
  MapContainer,
  GeoJSON,
  Popup,
  useMap,
  Pane,
} from "react-leaflet";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardMedia from "@mui/material/CardMedia";
import L from "leaflet";
import StraightenIcon from "@mui/icons-material/Straighten";
import Typography from "@mui/material/Typography";
import Lightbox, { type SlideImage } from "yet-another-react-lightbox";
import Thumbnails from "yet-another-react-lightbox/plugins/thumbnails";
import Fullscreen from "yet-another-react-lightbox/plugins/fullscreen";
import Zoom from "yet-another-react-lightbox/plugins/zoom";
import "./App.css";

import type { PhotoInfo, Segment } from "./types";
import { photoPath, thumbnailPath } from "./data-fetching";

function tileToLatLng(x: number, y: number, zoom: number): LatLng {
  const n = Math.pow(2, zoom);
  const lonDeg = (x / n) * 360.0 - 180.0;
  const latRad = Math.atan(Math.sinh(Math.PI * (1 - (2 * y) / n)));
  const latDeg = (latRad * 180) / Math.PI;
  return latLng(latDeg, lonDeg);
}

function getBounds(): LatLngBounds {
  const zoom = 5;
  const minX = 16;
  const minY = 10;
  const maxX = 19;
  const maxY = 13;

  const corner1 = tileToLatLng(minX, minY, zoom);
  const corner2 = tileToLatLng(maxX + 1, maxY + 1, zoom);
  return latLngBounds(corner1, corner2);
}

type InfoOverlayProps = {
  segment: Segment;
  moveLeft: () => void;
  moveRight: () => void;
  selectSegmentByDate: (date: string) => void;
  photos: PhotoInfo[];
};

export type SlideWithDate = SlideImage & { date: string };

function photosToSlides(photos: PhotoInfo[]): SlideWithDate[] {
  return photos.map((photo) => {
    const largePath = photoPath(photo.filename);
    const thumbPath = thumbnailPath(photo.filename);

    return {
      src: largePath,
      width: photo.resolution.x,
      height: photo.resolution.y,
      srcSet: [
        {
          src: largePath,
          width: photo.resolution.x,
          height: photo.resolution.y,
        },
        {
          src: thumbPath,
          width: photo.thumbnailResolution.x,
          height: photo.thumbnailResolution.y,
        },
      ],
      date: photo.date,
    };
  });
}

const InfoOverlay: FC<InfoOverlayProps> = ({
  photos,
  segment,
  moveLeft,
  moveRight,
  selectSegmentByDate,
}) => {
  const thumbPath = thumbnailPath(segment.featuredPhotoFilename);

  const [imageIndex, setImageIndex] = useState<null | number>(null);

  const slides = photosToSlides(photos);

  return (
    <Card
      className="info-overlay"
      elevation={22}
      sx={{ m: 2, position: "absolute", bottom: 0, zIndex: 1200 }}
    >
      <CardMedia
        onClick={() => setImageIndex(segment.imageIndex)}
        className="info-overlay-thumbnail pointer"
        component="img"
        image={thumbPath}
      />

      <Lightbox
        slides={slides}
        open={imageIndex !== null}
        index={imageIndex ?? undefined}
        close={() => setImageIndex(null)}
        animation={{
          swipe: 200,
        }}
        on={{
          view({ index }) {
            selectSegmentByDate(photos[index].date);
          },
        }}
        carousel={{
          preload: 4,
          padding: "6px",
        }}
        plugins={[Fullscreen, Thumbnails, Zoom]}
        thumbnails={{
          position: "start",
          border: 0,
          gap: 3,
          width: 70,
          height: (160 * 70) / 250,
          padding: 0,
        }}
      ></Lightbox>

      <CardContent>
        <Typography variant="h5">
          <span className="pointer" onClick={moveLeft}>
            &#10094;
          </span>{" "}
          {segment.date}{" "}
          <span className="pointer" onClick={moveRight}>
            &#10095;
          </span>
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {segment.description}
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mb: -1 }}>
          <span title="Distance">
            <StraightenIcon sx={{ verticalAlign: "middle" }} /> {segment.dist.toFixed(2)}km
          </span>
        </Typography>
      </CardContent>
    </Card>
  );
};

type AppProps = {
  segments: Segment[];
  photos: PhotoInfo[];
  backgroundSegments: FeatureCollection<MultiLineString>[];
  stays: FeatureCollection<Point> | null;
};

type MapContentProps = {
  segments: Segment[];
  selectedSegment: number | null;
  setSelectedSegment: (id: number | null) => void;
  backgroundSegments: FeatureCollection<MultiLineString>[];
  stays: FeatureCollection<Point> | null;
};

const MapContent: FC<MapContentProps> = ({
  segments,
  selectedSegment,
  setSelectedSegment,
  backgroundSegments,
  stays,
}) => {
  const map = useMap();

  useEffect(() => {
    map.createPane("fixedpane", document.getElementById("popup-container")!);
  }, [map]);

  const ref = useRef<L.GeoJSON>(null);

  useEffect(() => {
    if (!ref.current) {
      return;
    }

    ref.current.openPopup();
  }, [ref]);

  return (
    <>
      <TileLayer
        attribution='Map Tiles: <a href="https://www.jawg.io/en/">jawgmaps</a>, Map Data: <a href="https://osm.org/copyright/">© OpenStreetMap contributors</a>'
        url="img/tiles/{z}-{x}-{y}.png"
      />

      {segments.map((segment, index) => (
        <Pane
          name={index.toString()}
          key={index + (selectedSegment === index ? 1000 : 0)} // hack to force an update of className
          className={
            selectedSegment === index ? "pane-foreground" : "pane-middle"
          }
        >
          <GeoJSON
            data={segment.geometry}
            ref={index === 0 ? ref : undefined}
            eventHandlers={{
              popupopen: () => {
                setSelectedSegment(index);
              },
              popupclose: () => {
                setSelectedSegment(null);
              },
            }}
            style={{
              color: selectedSegment === index ? "#fd7536" : "#3388ff",
              opacity: 0.7,
              weight: selectedSegment === index ? 6 : 4,
            }}
          >
            <Popup pane="fixedpane" className="fixup">
              {index}
            </Popup>
          </GeoJSON>
        </Pane>
      ))}

      <Pane name={"bg-stuff"} className={"pane-background"}>
        {backgroundSegments.map((segment) => (
          <GeoJSON
            interactive={false}
            data={segment}
            style={{
              color: "#bbb",
              opacity: 0.7,
              weight: 2,
            }}
          ></GeoJSON>
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
      </Pane>
    </>
  );
};

const App: FC<AppProps> = ({
  segments,
  photos,
  backgroundSegments,
  stays,
}: AppProps) => {
  const [selectedSegment, setSelectedSegment] = useState<number | null>(0);

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

  return (
    <div onKeyDown={keyDown}>
      {selectedSegment !== null ? (
        <InfoOverlay
          photos={photos}
          segment={segments[selectedSegment]}
          moveLeft={move(-1)}
          moveRight={move(1)}
          selectSegmentByDate={(date: string) => {
            const segment = segments.findIndex((s) => s.date === date);
            if (segment !== -1) {
              setSelectedSegment(segment);
            }
          }}
        />
      ) : null}

      <div id="popup-container" />

      <MapContainer
        center={[47, 8]}
        zoom={8}
        minZoom={6}
        maxZoom={9}
        maxBounds={getBounds()}
        renderer={L.canvas({
          padding: 0.5,
          tolerance: 10,
        })}
      >
        <MapContent
          segments={segments}
          selectedSegment={selectedSegment}
          setSelectedSegment={setSelectedSegment}
          backgroundSegments={backgroundSegments}
          stays={stays}
        />
      </MapContainer>
    </div>
  );
};

export default App;

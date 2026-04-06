import Lightbox, { type SlideImage } from "yet-another-react-lightbox";
import Fullscreen from "yet-another-react-lightbox/plugins/fullscreen";
import Thumbnails from "yet-another-react-lightbox/plugins/thumbnails";
import Zoom from "yet-another-react-lightbox/plugins/zoom";

import { photoPath, thumbnailPath } from "../data-fetching";
import type { PhotoInfo } from "../types";

type PhotoGalleryProps = {
  photos: PhotoInfo[];
  imageIndex: number | null;
  setImageIndex: (idx: number | null) => void;
  selectSegmentByDate: (date: string) => void;
};

function PhotoGallery({
  photos,
  imageIndex,
  setImageIndex,
  selectSegmentByDate,
}: PhotoGalleryProps) {
  const slides = photosToSlides(photos);

  return (
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
  );
}

type SlideWithDate = SlideImage & { date: string };
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

export default PhotoGallery;

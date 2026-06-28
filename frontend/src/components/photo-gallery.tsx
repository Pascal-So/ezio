import { useEffect, useState } from "react";
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
  const aspect = useAspect();

  return (
    <>
      { /* TODO: deal with overlap of text and toolbar */ }
      { /* TODO: make this work in fullscreen. possibly do a yarl plugin? */ }
      { imageIndex !== null && <div key={ photos[imageIndex].date } className="fixed z-[10000] text-slate-100 py-3 px-5 text-xl animate-[flash_4s] text-shadow-lg opacity-0">{ photos[imageIndex].date }</div> }
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
            setImageIndex(index);
            selectSegmentByDate(photos[index].date);
          },
        }}
        carousel={{
          preload: 4,
          padding: "6px",
        }}
        plugins={[Fullscreen, Thumbnails, Zoom]}
        thumbnails={{
          position: aspect === "landscape" ? "end" : "bottom",
          border: 0,
          gap: 3,
          width: 70,
          height: (160 * 70) / 250,
          padding: 0,
          vignette: false,
        }}
      ></Lightbox>
    </>
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

// Custom hook to detect aspect ratio
const useAspect = () => {
  const getAspect = (): "landscape" | "portrait" =>
    window.innerWidth > window.innerHeight ? "landscape" : "portrait";
  const [aspect, setAspect] = useState(getAspect());

  useEffect(() => {
    const listener = () => setAspect(getAspect());

    window.addEventListener("resize", listener);

    // clean up the event listener in the end
    return () => {
      window.removeEventListener("resize", listener);
    };
  }, [setAspect]);

  return aspect;
};

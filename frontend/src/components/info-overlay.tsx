import { thumbnailPath } from "../data-fetching";
import type { SegmentInfo } from "../types";
import RulerIcon from "../assets/ruler.svg";
import MountainsIcon from "../assets/mountains.svg";

type InfoOverlayProps = {
  segment: SegmentInfo;
  moveToNextSegment: () => void;
  moveToPrevSegment: () => void;
  openPhotoGallery: () => void;
};

function InfoOverlay({
  segment,
  moveToNextSegment,
  moveToPrevSegment,
  openPhotoGallery,
}: InfoOverlayProps) {
  const featuredPhotoPath = thumbnailPath(segment.featuredPhotoFilename);

  return (
    <div className="shadow-lg flex flex-col max-w-60 bg-slate-100 rounded-lg absolute z-[1000] bottom-3 left-3 overflow-hidden">
      <img
        className="w-full"
        onClick={openPhotoGallery}
        src={featuredPhotoPath}
      />

      <div className="p-2">
        <div className="flex flex-row justify-start font-normal text-slate-800 text-xl">
          <Arrow
            direction="left"
            title="previous segment"
            onClick={moveToPrevSegment}
          />
          <h2>{segment.date}</h2>
          <Arrow
            direction="right"
            title="next segment"
            onClick={moveToNextSegment}
          />
        </div>

        <span className="text-slate-500 text-sm ml-[1px]">
          {segment.description}
        </span>

        <div className="text-slate-500 text-sm">
          <DetailWithIcon
            icon={RulerIcon}
            text={`${segment.dist.toFixed(2)}km`}
            title="Distance"
          />

          {segment.climb !== undefined && (
            <DetailWithIcon
              icon={MountainsIcon}
              text={`${segment.climb.toFixed(2)}m`}
              title="Climb"
            />
          )}
        </div>
      </div>
    </div>
  );
}

type DetailWithIconProps = {
  icon: string;
  text: string;
  title: string;
};
function DetailWithIcon({ icon, text, title }: DetailWithIconProps) {
  return (
    <span title={title} className="mr-2 mt-2">
      <img src={icon} className="h-[1.8em] align-middle inline-block" />{" "}
      <span className="align-middle">{text}</span>
    </span>
  );
}

type ArrowProps = {
  direction: "left" | "right";
  title: string;
  onClick: () => void;
};

function Arrow({ direction, title, onClick }: ArrowProps) {
  const arrowChar = direction === "left" ? "&#10094" : "&#10095";
  const padding = direction === "left" ? "pr-2" : "pl-2";

  return (
    <span
      className={`select-none cursor-pointer ${padding}`}
      onClick={onClick}
      dangerouslySetInnerHTML={{ __html: arrowChar }}
      title={title}
    />
  );
}

export default InfoOverlay;

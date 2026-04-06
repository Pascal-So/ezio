import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "leaflet/dist/leaflet.css";
import "yet-another-react-lightbox/styles.css";
import "yet-another-react-lightbox/plugins/thumbnails.css";
import "./index.css";
import App from "./App.tsx";
import { fetchAllData } from "./data-fetching";

// TODO: handle errors from fetching, maybe through a react error boundary?
let data = undefined;
try {
  data = await fetchAllData();
} catch {}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App
      segments={data.segments}
      photos={data.photos}
      backgroundSegments={data.backgroundSegments}
      stays={data.stays}
      totalBoundingBox={data.totalBoundingBox}
    />
  </StrictMode>,
);

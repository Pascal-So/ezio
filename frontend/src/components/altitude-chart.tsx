import type { SegmentGeometry } from "../types";
import { CartesianGrid, Line, LineChart, YAxis } from "recharts";

type AltitudeChartProps = {
  geometry: SegmentGeometry;
};

function AltitudeChart({ geometry }: AltitudeChartProps) {
  const alt = geometry.coordinates
    .flatMap((track) => track.map((pos) => ({ alt: pos[2] })))
    .map((obj, idx) => ({ x: idx, ...obj }));

  const minAlt = alt.reduce(
    (acc, { alt: current }) => Math.min(acc, current),
    Infinity,
  );
  const maxAlt = alt.reduce(
    (acc, { alt: current }) => Math.max(acc, current),
    -Infinity,
  );

  let tickSpacing = 100;
  const minRange = 215;

  if (maxAlt - minAlt > 600) {
    tickSpacing = 200;
  }

  const lowestLine = Math.max(
    Math.floor(minAlt / tickSpacing) * tickSpacing,
    0,
  );
  if (maxAlt - lowestLine < minRange) {
    tickSpacing = 50;
  }

  let upper = Math.max(maxAlt, lowestLine + minRange);
  const padding = (upper - lowestLine) * 0.1;

  const lower = lowestLine - padding * 0.3;
  upper += padding * 0.7;

  const horizontalValues: number[] = [];
  for (let i = lowestLine; i < upper; i += tickSpacing) {
    horizontalValues.push(i);
  }

  return (
    <LineChart data={alt} style={{ width: "250px", height: "110px" }}>
      <YAxis
        axisLine={false}
        tickLine={false}
        width={1}

        domain={[lower, upper]}
        allowDataOverflow
        orientation="right"
        ticks={horizontalValues}

        tick={(props) => {
          const toFloat = (num: number | string) =>
            typeof num === "string" ? parseFloat(num) : num;

          return (
            <text
              x={toFloat(props.x) - 5}
              y={toFloat(props.y) - 2}
              text-anchor="end"
              fill="#abb"
              fontSize={15}
            >
              {props.payload.value}m
            </text>
          );
        }}
        interval={0} // prevent ticks that are close together from being filtered out
      />
      <CartesianGrid stroke="#ccc" vertical={false} syncWithTicks={true} />

      <Line
        animationDuration={200}
        dataKey="alt"
        dot={false}
        stroke="#9aa"
        strokeWidth={2}
      />
    </LineChart>
  );
}

export default AltitudeChart;

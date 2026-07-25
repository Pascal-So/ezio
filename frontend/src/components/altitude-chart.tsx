import {
  useCallback,
  useEffect,
  useState,
  type TouchEvent,
  type MouseEvent,
  useMemo,
} from "react";
import type { AltitudeData } from "../types";
import {
  CartesianGrid,
  getRelativeCoordinate,
  Line,
  LineChart,
  Tooltip,
  useXAxisInverseScale,
  YAxis,
  type InverseScaleFunction,
  type RelativePointer,
} from "recharts";
import { throttle } from "es-toolkit";

type AltitudeChartProps = {
  altitudeData: AltitudeData;
  setHoveredCoordinateIndex: (index: number | null) => void;
};

function AltitudeChart({
  altitudeData,
  setHoveredCoordinateIndex,
}: AltitudeChartProps) {
  const [xAxisInverseScale, setXAxisInverseScale] =
    useState<InverseScaleFunction | null>(null);

  let tickSpacing = 100;
  const minRange = 215;

  const minAlt = altitudeData.minAlt;
  const maxAlt = altitudeData.maxAlt;

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

  const updateHover = useMemo(
    () =>
      throttle(
        (relativeX: number | null) => {
          if (relativeX === null) {
            setHoveredCoordinateIndex(null);
            return;
          }

          if (xAxisInverseScale !== null) {
            const downsampledXIndex = xAxisInverseScale(relativeX) as number;

            // convert back to the index in the non-downsampled data
            const originalXIndex = Math.min(
              Math.floor(
                (altitudeData.originalLength / altitudeData.altitudes.length) *
                  downsampledXIndex,
              ),
              altitudeData.originalLength - 1,
            );

            setHoveredCoordinateIndex(originalXIndex);
          }
        },
        50,
        { edges: ["trailing"] },
      ),
    [xAxisInverseScale, setHoveredCoordinateIndex, altitudeData],
  );
  const handleTouchMove = useCallback(
    (_data: unknown, event: TouchEvent<SVGGraphicsElement>) => {
      const chartPointers: RelativePointer[] = getRelativeCoordinate(event);
      if (chartPointers.length > 0) {
        updateHover(chartPointers[0].relativeX);
      }
    },
    [updateHover],
  );
  const handleMouseMove = useCallback(
    (_data: unknown, event: MouseEvent<SVGGraphicsElement>) => {
      updateHover(getRelativeCoordinate(event).relativeX);
    },
    [updateHover],
  );

  return (
    <LineChart
      data={altitudeData.altitudes}
      style={{ width: "250px", height: "110px" }}
      onTouchMove={handleTouchMove}
      onMouseMove={handleMouseMove}
      onTouchEnd={() => updateHover(null)}
      onMouseLeave={() => updateHover(null)}
    >
      <GetXAxisInverseScale setXAxisInverseScale={setXAxisInverseScale} />

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
              textAnchor="end"
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
      <Tooltip
        animationDuration={200}
        content={({ payload }) => {
          if (payload.length === 0) {
            return null;
          }

          const alt = payload[0].payload.alt;
          return (
            <span
              style={{
                color: "#677",
                padding: "0.5px",
                backgroundColor: "#fff8",
                borderRadius: "2px",
              }}
            >
              {alt.toFixed(0)}m
            </span>
          );
        }}
      />
    </LineChart>
  );
}

type GetXAxisInverseScaleProps = {
  setXAxisInverseScale: (scale: InverseScaleFunction | null) => void;
};
// HACK: this component just extracts the function to map relative coordinates
// to data coordinates. The mapping is only available inside LineChart, but we
// need to transport it to the outside so that we can use it in the touch and
// mouse callbacks on LineChart.
function GetXAxisInverseScale({
  setXAxisInverseScale,
}: GetXAxisInverseScaleProps) {
  const xAxisInverseScale = useXAxisInverseScale();
  const hasScale = xAxisInverseScale !== undefined;

  useEffect(() => {
    setXAxisInverseScale(() => xAxisInverseScale ?? null);
  }, [setXAxisInverseScale, hasScale]);

  return <></>;
}

export default AltitudeChart;

import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { background, c, fontFamily, monoFamily } from "./theme";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Fade + rise in, `delay` in frames from the start of the enclosing scene.
export const Reveal: React.FC<{
  delay?: number;
  rise?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({ delay = 0, rise = 40, style, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div style={{ opacity: p, translate: `0 ${(1 - p) * rise}px`, ...style }}>
      {children}
    </div>
  );
};

// Linear 0→1 progress between two frames, eased.
export const useProgress = (from: number, to: number) => {
  const frame = useCurrentFrame();
  return interpolate(frame, [from, to], [0, 1], {
    ...clamp,
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
};

export const Scene: React.FC<{
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ children, style }) => (
  <AbsoluteFill
    style={{
      background,
      color: c.white,
      fontFamily,
      padding: "120px 150px",
      ...style,
    }}
  >
    {children}
  </AbsoluteFill>
);

export const Eyebrow: React.FC<{ children: React.ReactNode; color?: string }> = ({
  children,
  color = c.green,
}) => (
  <div
    style={{
      color,
      fontSize: 30,
      fontWeight: 800,
      letterSpacing: "0.18em",
      textTransform: "uppercase",
    }}
  >
    {children}
  </div>
);

export const Headline: React.FC<{
  children: React.ReactNode;
  size?: number;
  style?: React.CSSProperties;
}> = ({ children, size = 104, style }) => (
  <h1
    style={{
      margin: 0,
      fontSize: size,
      fontWeight: 800,
      lineHeight: 1.02,
      letterSpacing: "-0.05em",
      ...style,
    }}
  >
    {children}
  </h1>
);

export const Card: React.FC<{
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ children, style }) => (
  <div
    style={{
      background: "linear-gradient(145deg, rgba(21,56,52,.95), rgba(11,40,37,.95))",
      border: "2px solid #245249",
      borderRadius: 28,
      padding: 40,
      boxShadow: "0 30px 60px rgba(0,0,0,.25)",
      ...style,
    }}
  >
    {children}
  </div>
);

const statusColors: Record<string, [string, string]> = {
  WITHIN_TOLERANCE: ["#a9f6cd", "#1a5b43"],
  REVIEW_REQUIRED: ["#ffdda1", "#60481d"],
  INSUFFICIENT_EVIDENCE: ["#f7b0aa", "#603532"],
};

export const StatusPill: React.FC<{ status: string; size?: number }> = ({
  status,
  size = 26,
}) => {
  const [fg, bg] = statusColors[status];
  return (
    <span
      style={{
        color: fg,
        background: bg,
        fontFamily: monoFamily,
        fontWeight: 600,
        fontSize: size,
        padding: `${size * 0.45}px ${size * 0.8}px`,
        borderRadius: 999,
        whiteSpace: "nowrap",
      }}
    >
      {status}
    </span>
  );
};

export const Leaf: React.FC<{ size: number; color?: string }> = ({
  size,
  color = c.green,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path
      d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"
      stroke={color}
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"
      stroke={color}
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

// Slowly rotating dashed orbit rings, echoing the sign-in page art.
export const Orbits: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {[900, 1400].map((d, i) => (
        <div
          key={d}
          style={{
            position: "absolute",
            width: d,
            height: d,
            left: 960 - d / 2,
            top: 540 - d / 2,
            borderRadius: "50%",
            border: `2px dashed ${i ? "#72d7ad22" : "#80ffc133"}`,
            rotate: `${frame * (i ? -0.08 : 0.12)}deg`,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

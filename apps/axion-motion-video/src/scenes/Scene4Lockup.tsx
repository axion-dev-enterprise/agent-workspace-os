import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";

export const Scene4Lockup: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const logoSpring = spring({
    frame,
    fps,
    config: { damping: 12, mass: 0.9 },
  });

  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  const letterSpacing = interpolate(frame, [0, 50], [14, 30], {
    easing: Easing.bezier(0.16, 1, 0.3, 1),
    extrapolateRight: "clamp",
  });

  // Light flare sweep across logo
  const flareX = interpolate(frame, [25, 75], [-200, 1280], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Pulse glow on final tag
  const pulseScale = 1 + 0.04 * Math.sin(frame * 0.12);

  return (
    <AbsoluteFill
      style={{
        opacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        color: "#ffffff",
        fontFamily: "'Segoe UI', -apple-system, sans-serif",
      }}
    >
      {/* Top Statement */}
      <div
        style={{
          fontSize: 22,
          fontWeight: 700,
          letterSpacing: 6,
          color: "#7ab8f5",
          marginBottom: 28,
          textTransform: "uppercase",
          opacity: interpolate(frame, [10, 30], [0, 1], { extrapolateRight: "clamp" }),
        }}
      >
        O FUTURO É DETERMINÍSTICO.
      </div>

      {/* Main Logo with Flare Overflow Container */}
      <div
        style={{
          position: "relative",
          transform: `scale(${logoSpring})`,
          overflow: "hidden",
          padding: "20px 60px",
        }}
      >
        <h1
          style={{
            fontSize: 124,
            fontWeight: 900,
            letterSpacing: `${letterSpacing}px`,
            margin: 0,
            paddingLeft: `${letterSpacing}px`,
            background: "linear-gradient(180deg, #ffffff 0%, #b2d2f7 50%, #4a8ee0 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            filter: "drop-shadow(0 0 35px rgba(60, 150, 255, 0.6))",
          }}
        >
          AXION
        </h1>

        {/* Diagonal Light Sweep Flare */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: `${flareX}px`,
            width: 80,
            height: "100%",
            background:
              "linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.7), transparent)",
            transform: "skewX(-25deg)",
            pointerEvents: "none",
          }}
        />
      </div>

      {/* Corporate Tagline */}
      <div
        style={{
          fontSize: 22,
          fontWeight: 700,
          letterSpacing: 8,
          color: "#a4c4ea",
          marginTop: 18,
          textTransform: "uppercase",
          opacity: interpolate(frame, [25, 45], [0, 1], { extrapolateRight: "clamp" }),
        }}
      >
        THE AUTONOMOUS OPERATING SYSTEM
      </div>

      <p
        style={{
          fontSize: 42,
          fontWeight: 500,
          color: "#dce8f8",
          marginTop: 36,
          marginBottom: 48,
          transform: `scale(${pulseScale})`,
          opacity: interpolate(frame, [35, 55], [0, 1], { extrapolateRight: "clamp" }),
        }}
      >
        Construa o próximo.
      </p>

      {/* Domain Badge CTA */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          padding: "14px 28px",
          background: "rgba(30, 80, 160, 0.25)",
          border: "1px solid rgba(80, 160, 255, 0.5)",
          borderRadius: 999,
          boxShadow: "0 0 30px rgba(40, 130, 255, 0.2)",
          opacity: interpolate(frame, [45, 65], [0, 1], { extrapolateRight: "clamp" }),
        }}
      >
        <span
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            backgroundColor: "#4ade80",
            boxShadow: "0 0 8px #4ade80",
          }}
        />
        <span
          style={{
            fontSize: 20,
            fontWeight: 700,
            letterSpacing: 2,
            color: "#ffffff",
            fontFamily: "monospace",
          }}
        >
          example.com
        </span>
      </div>
    </AbsoluteFill>
  );
};

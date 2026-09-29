import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

export const BackgroundGrid: React.FC = () => {
  const frame = useCurrentFrame();

  // Continuous subtle drift
  const gridOffsetY = (frame * 1.5) % 40;
  const sweepAngle = (frame * 2.4) % 360;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#05070d",
        overflow: "hidden",
      }}
    >
      {/* Deep Radial Ambient Glow */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 50% 40%, rgba(20, 50, 95, 0.45) 0%, rgba(8, 18, 36, 0.3) 45%, #05070d 80%)",
        }}
      />

      {/* Conic Ambient Sweep */}
      <div
        style={{
          position: "absolute",
          inset: "-30%",
          background: `conic-gradient(from ${sweepAngle}deg at 50% 50%, transparent, rgba(40, 140, 255, 0.08), transparent 30%)`,
          pointerEvents: "none",
        }}
      />

      {/* Perspective Ground Grid */}
      <div
        style={{
          position: "absolute",
          width: "180%",
          height: "80%",
          left: "-40%",
          bottom: "-25%",
          transform: "perspective(360px) rotateX(68deg)",
          transformOrigin: "bottom center",
          backgroundImage: `
            linear-gradient(rgba(50, 140, 255, 0.16) 1px, transparent 1px),
            linear-gradient(90deg, rgba(50, 140, 255, 0.16) 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
          backgroundPosition: `0px ${gridOffsetY}px`,
          maskImage: "linear-gradient(to bottom, transparent, rgba(0,0,0,0.9) 30%, #000 100%)",
          WebkitMaskImage: "linear-gradient(to bottom, transparent, rgba(0,0,0,0.9) 30%, #000 100%)",
        }}
      />

      {/* Star Particles */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "radial-gradient(circle, rgba(220, 240, 255, 0.6) 1px, transparent 1.6px)",
          backgroundSize: "48px 64px",
          opacity: 0.5,
          transform: `translateY(-${(frame * 0.4) % 64}px)`,
        }}
      />
    </AbsoluteFill>
  );
};

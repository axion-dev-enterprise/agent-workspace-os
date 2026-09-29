import React from "react";
import {
  AbsoluteFill,
  Audio,
  Composition,
  Sequence,
  staticFile,
  useCurrentFrame,
} from "remotion";

import { BackgroundGrid } from "./components/BackgroundGrid";
import { Scene1Genesis } from "./scenes/Scene1Genesis";
import { Scene2Pillars } from "./scenes/Scene2Pillars";
import { Scene3Telemetry } from "./scenes/Scene3Telemetry";
import { Scene4Lockup } from "./scenes/Scene4Lockup";

export const TOTAL_DURATION_IN_FRAMES = 450; // 15.0 seconds @ 30 FPS
export const VIDEO_FPS = 30;
export const VIDEO_WIDTH = 1080;
export const VIDEO_HEIGHT = 1920;

export const MainVideoComponent: React.FC = () => {
  const frame = useCurrentFrame();
  const progressPct = (frame / TOTAL_DURATION_IN_FRAMES) * 100;

  return (
    <AbsoluteFill style={{ backgroundColor: "#05070d", overflow: "hidden" }}>
      {/* 1. Procedural Audio Track */}
      <Audio src={staticFile("audio.wav")} />

      {/* 2. Global Persistent Background Grid & Ambient Sweeps */}
      <BackgroundGrid />

      {/* 3. Top Editorial Header */}
      <div
        style={{
          position: "absolute",
          top: 60,
          left: 60,
          right: 60,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          zIndex: 50,
          fontFamily: "'Segoe UI', -apple-system, sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span
            style={{
              fontSize: 22,
              fontWeight: 800,
              letterSpacing: 4,
              color: "#ffffff",
            }}
          >
            A X I O N
          </span>
          <span
            style={{
              fontSize: 12,
              fontWeight: 700,
              color: "#5db4ff",
              background: "rgba(45, 130, 255, 0.2)",
              border: "1px solid rgba(80, 160, 255, 0.4)",
              padding: "3px 8px",
              borderRadius: 6,
            }}
          >
            SYSTEM v2.2
          </span>
        </div>

        <div style={{ fontSize: 16, fontWeight: 600, color: "#8aa0bd", letterSpacing: 2 }}>
          4K / 30 FPS
        </div>
      </div>

      {/* 4. Sequential Scenes */}
      <Sequence from={0} durationInFrames={95} name="Ato 1: Origem">
        <Scene1Genesis />
      </Sequence>

      <Sequence from={85} durationInFrames={155} name="Ato 2: Arquitetura">
        <Scene2Pillars />
      </Sequence>

      <Sequence from={230} durationInFrames={130} name="Ato 3: Telemetria">
        <Scene3Telemetry />
      </Sequence>

      <Sequence from={350} durationInFrames={100} name="Ato 4: Brand Lockup">
        <Scene4Lockup />
      </Sequence>

      {/* 5. Bottom Architectural Baseline & Progress Indicator */}
      <div
        style={{
          position: "absolute",
          bottom: 50,
          left: 60,
          right: 60,
          height: 2,
          backgroundColor: "rgba(100, 150, 220, 0.15)",
          zIndex: 50,
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progressPct}%`,
            background: "linear-gradient(90deg, #2575fc, #00d2ff)",
            boxShadow: "0 0 10px rgba(0, 210, 255, 0.6)",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

export const MyComposition: React.FC = () => {
  return (
    <Composition
      id="AxionHeroVideo"
      component={MainVideoComponent}
      durationInFrames={TOTAL_DURATION_IN_FRAMES}
      fps={VIDEO_FPS}
      width={VIDEO_WIDTH}
      height={VIDEO_HEIGHT}
    />
  );
};

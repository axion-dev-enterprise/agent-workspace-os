import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";

export const Scene3Telemetry: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sceneOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });
  const exitOpacity = interpolate(frame, [105, 120], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Animated metric counters
  const skillsCount = Math.round(
    interpolate(frame, [15, 65], [0, 58], {
      easing: Easing.bezier(0.16, 1, 0.3, 1),
      extrapolateRight: "clamp",
    })
  );

  const uptimeCount = interpolate(frame, [15, 65], [90, 99.99], {
    easing: Easing.bezier(0.16, 1, 0.3, 1),
    extrapolateRight: "clamp",
  }).toFixed(2);

  const renderSpeed = interpolate(frame, [15, 65], [0, 18], {
    easing: Easing.bezier(0.16, 1, 0.3, 1),
    extrapolateRight: "clamp",
  }).toFixed(1);

  // Radar sweep angle
  const radarAngle = (frame * 5.5) % 360;

  return (
    <AbsoluteFill
      style={{
        opacity: sceneOpacity * exitOpacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 60px",
        color: "#ffffff",
        fontFamily: "'Segoe UI', -apple-system, sans-serif",
      }}
    >
      <div
        style={{
          fontSize: 18,
          fontWeight: 600,
          letterSpacing: 4,
          color: "#7ab8f5",
          marginBottom: 12,
          textTransform: "uppercase",
        }}
      >
        03 / ESCALA & TELEMETRIA
      </div>

      <h2
        style={{
          fontSize: 56,
          fontWeight: 800,
          letterSpacing: -1,
          textAlign: "center",
          margin: "0 0 54px 0",
          maxWidth: 900,
          lineHeight: 1.15,
        }}
      >
        Do conceito à escala global.
      </h2>

      {/* SVG Global Radar Network Mesh */}
      <div
        style={{
          position: "relative",
          width: 380,
          height: 380,
          marginBottom: 64,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg
          width="380"
          height="380"
          viewBox="0 0 380 380"
          style={{ position: "absolute", inset: 0 }}
        >
          {/* Concentric Radar Rings */}
          <circle cx="190" cy="190" r="170" fill="none" stroke="rgba(70, 150, 255, 0.18)" strokeWidth="1.5" strokeDasharray="4 4" />
          <circle cx="190" cy="190" r="120" fill="none" stroke="rgba(70, 150, 255, 0.28)" strokeWidth="1.5" />
          <circle cx="190" cy="190" r="65" fill="none" stroke="rgba(70, 150, 255, 0.4)" strokeWidth="1.5" />

          {/* Sweeping Beam */}
          <line
            x1="190"
            y1="190"
            x2={190 + Math.cos((radarAngle * Math.PI) / 180) * 170}
            y2={190 + Math.sin((radarAngle * Math.PI) / 180) * 170}
            stroke="url(#beamGrad)"
            strokeWidth="2.5"
          />

          <defs>
            <linearGradient id="beamGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="100%" stopColor="rgba(40, 150, 255, 0.1)" />
            </linearGradient>
          </defs>

          {/* Connected Network Nodes */}
          {[
            [190, 70],
            [290, 140],
            [270, 270],
            [120, 260],
            [90, 130],
          ].map(([nx, ny], idx) => (
            <g key={idx}>
              <line x1="190" y1="190" x2={nx} y2={ny} stroke="rgba(60, 140, 255, 0.25)" strokeWidth="1" />
              <circle cx={nx} cy={ny} r="5" fill="#67baff" />
              <circle cx={nx} cy={ny} r="12" fill="none" stroke="#67baff" strokeWidth="1" opacity="0.6" />
            </g>
          ))}
          <circle cx="190" cy="190" r="9" fill="#ffffff" />
        </svg>
      </div>

      {/* Metric Counters Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: 20,
          width: "100%",
          maxWidth: 920,
        }}
      >
        <div
          style={{
            background: "rgba(15, 23, 40, 0.8)",
            border: "1px solid rgba(70, 150, 255, 0.25)",
            borderRadius: 16,
            padding: "24px 16px",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 48, fontWeight: 900, color: "#5bb2ff", fontFamily: "monospace" }}>
            {skillsCount}
          </div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#9db3cf", marginTop: 6 }}>
            SKILLS CANÔNICAS
          </div>
        </div>

        <div
          style={{
            background: "rgba(15, 23, 40, 0.8)",
            border: "1px solid rgba(70, 150, 255, 0.25)",
            borderRadius: 16,
            padding: "24px 16px",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 48, fontWeight: 900, color: "#ffffff", fontFamily: "monospace" }}>
            {uptimeCount}%
          </div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#9db3cf", marginTop: 6 }}>
            UPTIME SRE LOCAL
          </div>
        </div>

        <div
          style={{
            background: "rgba(15, 23, 40, 0.8)",
            border: "1px solid rgba(70, 150, 255, 0.25)",
            borderRadius: 16,
            padding: "24px 16px",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 48, fontWeight: 900, color: "#38e0a0", fontFamily: "monospace" }}>
            {renderSpeed}s
          </div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#9db3cf", marginTop: 6 }}>
            TEMPO DE RENDER
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

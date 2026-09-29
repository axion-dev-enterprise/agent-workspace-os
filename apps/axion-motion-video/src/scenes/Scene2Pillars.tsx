import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

interface Pillar {
  number: string;
  title: string;
  tag: string;
  desc: string;
  iconSvg: React.ReactNode;
}

export const Scene2Pillars: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const sceneOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: "clamp",
  });
  const exitOpacity = interpolate(frame, [135, 150], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const pillars: Pillar[] = [
    {
      number: "01",
      title: "Deterministic 3D Engine",
      tag: "GPU NATIVE / OPENGL",
      desc: "Renderização determinística acelerada por hardware local e síntese de áudio matemática.",
      iconSvg: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#5cb3ff" strokeWidth="2">
          <polygon points="12 2 2 7 12 12 22 7 12 2" />
          <polyline points="2 17 12 22 22 17" />
          <polyline points="2 12 12 17 22 12" />
        </svg>
      ),
    },
    {
      number: "02",
      title: "Autonomous Governance",
      tag: "SELF-HEALING / ZERO LEAK",
      desc: "Supervisão contínua de integridade, cofre criptográfico e auditoria factual automatizada.",
      iconSvg: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#5cb3ff" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      ),
    },
    {
      number: "03",
      title: "Cloud-to-Edge Mesh",
      tag: "ZERO TRUST / MULTI-NODE",
      desc: "Distribuição unificada entre Cloudflare Edge, nós remotos de computação e storage seguro.",
      iconSvg: (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#5cb3ff" strokeWidth="2">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      ),
    },
  ];

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
      {/* Chapter header */}
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
        02 / ARQUITETURA MODULAR
      </div>

      <h2
        style={{
          fontSize: 54,
          fontWeight: 800,
          letterSpacing: -1,
          textAlign: "center",
          margin: "0 0 48px 0",
          maxWidth: 900,
          lineHeight: 1.15,
        }}
      >
        Autonomia. Precisão. Governança.
      </h2>

      {/* Staggered Cards */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 24,
          width: "100%",
          maxWidth: 920,
        }}
      >
        {pillars.map((item, idx) => {
          const cardSpring = spring({
            frame: frame - 15 - idx * 14,
            fps,
            config: { damping: 14, mass: 0.8 },
          });

          const translateY = interpolate(cardSpring, [0, 1], [40, 0]);
          const cardOpacity = interpolate(cardSpring, [0, 1], [0, 1]);

          return (
            <div
              key={idx}
              style={{
                opacity: cardOpacity,
                transform: `translateY(${translateY}px)`,
                background: "rgba(14, 22, 38, 0.75)",
                border: "1px solid rgba(80, 160, 255, 0.25)",
                borderRadius: 18,
                padding: "26px 32px",
                display: "flex",
                alignItems: "center",
                gap: 28,
                boxShadow: "0 12px 30px rgba(0, 0, 0, 0.4)",
              }}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 14,
                  background: "rgba(35, 95, 185, 0.25)",
                  border: "1px solid rgba(80, 160, 255, 0.4)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                {item.iconSvg}
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
                  <span
                    style={{
                      fontSize: 14,
                      fontWeight: 700,
                      color: "#5db4ff",
                      background: "rgba(45, 130, 255, 0.15)",
                      padding: "3px 8px",
                      borderRadius: 6,
                    }}
                  >
                    {item.tag}
                  </span>
                </div>
                <div style={{ fontSize: 26, fontWeight: 700, color: "#ffffff", marginBottom: 6 }}>
                  {item.title}
                </div>
                <div style={{ fontSize: 18, color: "#92a6c2", lineHeight: 1.35 }}>
                  {item.desc}
                </div>
              </div>

              <div
                style={{
                  fontSize: 34,
                  fontWeight: 900,
                  color: "rgba(120, 180, 255, 0.2)",
                  fontFamily: "monospace",
                }}
              >
                {item.number}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

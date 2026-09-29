import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";

export const Scene1Genesis: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance spring
  const scale = spring({
    frame,
    fps,
    config: { damping: 14, mass: 0.9 },
  });

  const opacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: "clamp",
  });

  const exitOpacity = interpolate(frame, [80, 95], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Letter spacing expansion
  const letterSpacing = interpolate(frame, [0, 60], [12, 28], {
    easing: Easing.bezier(0.16, 1, 0.3, 1),
    extrapolateRight: "clamp",
  });

  // Orbital ring rotation
  const ringRot1 = frame * 1.8;
  const ringRot2 = -frame * 2.4;
  const orbPulse = 1 + 0.08 * Math.sin(frame * 0.15);

  return (
    <AbsoluteFill
      style={{
        opacity: opacity * exitOpacity,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        color: "#ffffff",
        fontFamily: "'Segoe UI', -apple-system, sans-serif",
      }}
    >
      {/* 3D Geometric Gyro Visualization */}
      <div
        style={{
          position: "relative",
          width: 320,
          height: 320,
          marginBottom: 60,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transform: `scale(${scale})`,
        }}
      >
        {/* Outer Ring 1 */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            border: "2px solid rgba(80, 160, 255, 0.35)",
            boxShadow: "0 0 30px rgba(40, 140, 255, 0.25), inset 0 0 20px rgba(40, 140, 255, 0.15)",
            transform: `rotateX(65deg) rotateZ(${ringRot1}deg)`,
          }}
        />

        {/* Middle Ring 2 */}
        <div
          style={{
            position: "absolute",
            inset: 35,
            borderRadius: "50%",
            border: "2px solid rgba(130, 200, 255, 0.5)",
            boxShadow: "0 0 25px rgba(60, 160, 255, 0.3)",
            transform: `rotateY(70deg) rotateZ(${ringRot2}deg)`,
          }}
        />

        {/* Inner Glowing Orb */}
        <div
          style={{
            width: 100,
            height: 100,
            borderRadius: "50%",
            background:
              "radial-gradient(circle at 32% 28%, #ffffff, #6ebcff 20%, #1765c9 55%, #051a4a 85%)",
            boxShadow:
              "0 0 40px rgba(60, 160, 255, 0.8), 0 0 100px rgba(25, 100, 230, 0.5), inset -16px -20px 28px rgba(0, 5, 20, 0.8)",
            transform: `scale(${orbPulse})`,
          }}
        />

        {/* Orbiting Satellites */}
        {[0, 90, 180, 270].map((deg, idx) => {
          const curDeg = (deg + frame * 2.2) * (Math.PI / 180);
          const px = Math.cos(curDeg) * 155;
          const py = Math.sin(curDeg) * 60;
          return (
            <div
              key={idx}
              style={{
                position: "absolute",
                width: 12,
                height: 12,
                borderRadius: 3,
                backgroundColor: "#7eccff",
                boxShadow: "0 0 15px #4da6ff",
                transform: `translate(${px}px, ${py}px)`,
              }}
            />
          );
        })}
      </div>

      {/* Chapter Tag */}
      <div
        style={{
          fontSize: 20,
          fontWeight: 600,
          letterSpacing: 4,
          color: "#7ab8f5",
          marginBottom: 16,
          textTransform: "uppercase",
        }}
      >
        01 / ORIGEM
      </div>

      {/* Main Title */}
      <h1
        style={{
          fontSize: 92,
          fontWeight: 900,
          letterSpacing: `${letterSpacing}px`,
          textShadow: "0 0 45px rgba(50, 150, 255, 0.5)",
          margin: 0,
          paddingLeft: `${letterSpacing}px`, // balance optical center
        }}
      >
        AXION
      </h1>

      {/* Subtitle */}
      <p
        style={{
          fontSize: 28,
          fontWeight: 400,
          color: "#9db3cf",
          marginTop: 20,
          letterSpacing: 2,
          maxWidth: 720,
          textAlign: "center",
          lineHeight: 1.4,
        }}
      >
        Uma nova ordem de inteligência autônoma.
      </p>
    </AbsoluteFill>
  );
};

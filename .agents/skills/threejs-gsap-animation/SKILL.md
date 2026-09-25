---
name: threejs-gsap-animation
description: >-
  Operational skill for 2D and 3D visual experiences, WebGL/WebGPU rendering with Three.js,
  React Three Fiber (R3F), Drei, shaders, and complex scroll-driven choreographies with GSAP ScrollTrigger.
  Use when developing 3D product viewports, landing page animations, particle systems,
  canvas interactions, and smooth timeline transitions.
---

# Three.js, R3F & GSAP Animation Skill

Skill operacional para desenvolvimento de experiências visuais imersivas 2D/3D, renderização WebGL e orquestração de animações de alto desempenho.

---

## 1. Princípios de Performance 3D na Web

1. **Draco Compression**: Sempre comprimir malhas 3D (.gltf/.glb) usando Draco ou Meshopt para downloads rápidos.
2. **Controle de Draw Calls**: Agrupar geometrias similares com `InstancedMesh` ou mesclar geometrias com `BufferGeometryUtils.mergeGeometries`.
3. **Disposal de Recursos**: Desalocar texturas e geometrias manualmente (`geometry.dispose()`, `texture.dispose()`) quando o componente for desmontado para evitar vazamentos de memória na GPU.
4. **Resolução Adaptativa**: Ajustar `dpr` (device pixel ratio) com limite de `Math.min(window.devicePixelRatio, 2)` para evitar travamentos em telas Retina 4K/5K.

---

## 2. Padrão Canônico: React Three Fiber (R3F)

```tsx
import React, { useRef, Suspense } from "react"
import { Canvas, useFrame } from "@react-three/fiber"
import { OrbitControls, Float, MeshDistortMaterial, Environment } from "@react-three/drei"
import * as THREE from "three"

function InteractiveSphere() {
  const meshRef = useRef<THREE.Mesh>(null!)

  useFrame((state, delta) => {
    meshRef.current.rotation.x += delta * 0.2
    meshRef.current.rotation.y += delta * 0.3
  })

  return (
    <Float speed={2} rotationIntensity={1} floatIntensity={1.5}>
      <mesh ref={meshRef} castShadow receiveShadow>
        <sphereGeometry args={[1.5, 64, 64]} />
        <MeshDistortMaterial
          color="#0066FF"
          roughness={0.15}
          metalness={0.8}
          distort={0.4}
          speed={2}
        />
      </mesh>
    </Float>
  )
}

export function Visual3DHero() {
  return (
    <div className="relative h-[600px] w-full overflow-hidden bg-black">
      <Canvas
        camera={{ position: [0, 0, 5], fov: 45 }}
        dpr={[1, 2]}
        gl={{ antialias: true, powerPreference: "high-performance" }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1.5} castShadow />
        <Suspense fallback={null}>
          <InteractiveSphere />
          <Environment preset="city" />
        </Suspense>
        <OrbitControls enableZoom={false} enablePan={false} maxPolarAngle={Math.PI / 2} />
      </Canvas>
    </div>
  )
}
```

---

## 3. Padrão GSAP ScrollTrigger

Para animações controladas pelo scroll do usuário em landing pages:

```typescript
import gsap from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"

gsap.registerPlugin(ScrollTrigger)

export function initHeroScrollAnimation(containerSelector: string) {
  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: containerSelector,
      start: "top top",
      end: "+=150%",
      pin: true,
      scrub: 1, // Suavização de 1 segundo
    },
  })

  tl.to(".hero-title", { opacity: 0, y: -50, duration: 1 })
    .to(".hero-3d-model", { scale: 1.5, rotateY: 180, duration: 2 }, "<")
    .fromTo(".feature-card", { opacity: 0, y: 100, stagger: 0.2 }, { opacity: 1, y: 0, duration: 1.5 })

  return () => {
    tl.kill()
    ScrollTrigger.getAll().forEach((t) => t.kill())
  }
}
```

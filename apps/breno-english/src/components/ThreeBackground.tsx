import React, { useEffect, useRef } from 'react'
import * as THREE from 'three'

export const ThreeBackground: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return
    const container = containerRef.current

    // Scene & Camera
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(
      50,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    )
    camera.position.z = 30

    // WebGL Renderer with pixel ratio cap
    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance'
    })
    renderer.setSize(container.clientWidth, container.clientHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(renderer.domElement)

    // Soft circular bokeh particle texture via 2D Canvas for light theme
    const canvas = document.createElement('canvas')
    canvas.width = 64
    canvas.height = 64
    const ctx = canvas.getContext('2d')
    if (ctx) {
      const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32)
      gradient.addColorStop(0, 'rgba(217, 119, 6, 0.55)')
      gradient.addColorStop(0.4, 'rgba(245, 158, 11, 0.25)')
      gradient.addColorStop(0.8, 'rgba(203, 213, 225, 0.15)')
      gradient.addColorStop(1, 'rgba(255, 255, 255, 0)')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, 64, 64)
    }
    const circleTexture = new THREE.CanvasTexture(canvas)

    // Master group for mouse parallax
    const masterGroup = new THREE.Group()
    scene.add(masterGroup)

    // Gentle ambient floating motes
    const particleCount = 120
    const geometry = new THREE.BufferGeometry()
    const positions = new Float32Array(particleCount * 3)

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 60
      positions[i * 3 + 1] = (Math.random() - 0.5) * 45
      positions[i * 3 + 2] = (Math.random() - 0.5) * 25
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))

    const material = new THREE.PointsMaterial({
      size: 1.4,
      map: circleTexture,
      transparent: true,
      opacity: 0.45,
      blending: THREE.NormalBlending,
      depthWrite: false,
    })

    const particles = new THREE.Points(geometry, material)
    masterGroup.add(particles)

    // Mouse movement parallax
    let mouseX = 0
    let mouseY = 0
    let targetX = 0
    let targetY = 0

    const handleMouseMove = (e: MouseEvent) => {
      const halfX = window.innerWidth / 2
      const halfY = window.innerHeight / 2
      mouseX = (e.clientX - halfX) * 0.0003
      mouseY = (e.clientY - halfY) * 0.0003
    }

    window.addEventListener('mousemove', handleMouseMove, { passive: true })

    const handleResize = () => {
      if (!container) return
      camera.aspect = container.clientWidth / container.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(container.clientWidth, container.clientHeight)
    }

    window.addEventListener('resize', handleResize)

    let animId: number
    const clock = new THREE.Clock()

    const animate = () => {
      animId = requestAnimationFrame(animate)
      const t = clock.getElapsedTime()

      targetX += (mouseX - targetX) * 0.04
      targetY += (mouseY - targetY) * 0.04

      masterGroup.rotation.y = targetX + Math.sin(t * 0.08) * 0.03
      masterGroup.rotation.x = targetY + Math.cos(t * 0.06) * 0.02
      particles.rotation.y = t * 0.01

      renderer.render(scene, camera)
    }

    animate()

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('resize', handleResize)
      geometry.dispose()
      material.dispose()
      circleTexture.dispose()
      renderer.dispose()
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
    }
  }, [])

  return (
    <>
      {/* Light theme ambient background gradients */}
      <div 
        className="fixed inset-0 pointer-events-none z-0"
        style={{
          background: `
            radial-gradient(ellipse 70% 40% at 50% -10%, rgba(245, 158, 11, 0.08) 0%, transparent 70%),
            radial-gradient(circle at 90% 20%, rgba(59, 130, 246, 0.04) 0%, transparent 50%),
            radial-gradient(circle at 10% 60%, rgba(241, 245, 249, 0.8) 0%, transparent 60%),
            #ffffff
          `
        }}
      />
      {/* Subtle WebGL canvas */}
      <div 
        ref={containerRef}
        className="fixed inset-0 pointer-events-none z-0 overflow-hidden"
        aria-hidden="true"
      />
    </>
  )
}

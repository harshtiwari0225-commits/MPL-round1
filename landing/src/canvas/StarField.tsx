import React, { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { scrollState } from '../state/scrollController';

export const StarField: React.FC = () => {
  const pointsRef = useRef<THREE.Points>(null);

  const { geometry, material } = useMemo(() => {
    const count = 4000;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    const sizes = new Float32Array(count);
    const phases = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      // Distribute on a large sphere shell
      const phi = Math.random() * Math.PI * 2;
      const cosTheta = Math.random() * 2 - 1;
      const sinTheta = Math.sqrt(1 - cosTheta * cosTheta);
      const r = 150 + Math.random() * 100;

      positions[i * 3] = r * sinTheta * Math.cos(phi);
      positions[i * 3 + 1] = r * cosTheta + 8; // center around y=8
      positions[i * 3 + 2] = r * sinTheta * Math.sin(phi);

      // Mix of warm white, cool blue, faint gold
      const colorType = Math.random();
      if (colorType < 0.5) {
        // Cool white
        colors[i * 3] = 0.85 + Math.random() * 0.15;
        colors[i * 3 + 1] = 0.88 + Math.random() * 0.12;
        colors[i * 3 + 2] = 0.95 + Math.random() * 0.05;
      } else if (colorType < 0.8) {
        // Cool blue
        colors[i * 3] = 0.4 + Math.random() * 0.2;
        colors[i * 3 + 1] = 0.6 + Math.random() * 0.2;
        colors[i * 3 + 2] = 0.9 + Math.random() * 0.1;
      } else {
        // Faint gold
        colors[i * 3] = 0.9 + Math.random() * 0.1;
        colors[i * 3 + 1] = 0.75 + Math.random() * 0.15;
        colors[i * 3 + 2] = 0.2 + Math.random() * 0.2;
      }

      // Hero stars are brighter and larger
      const isHero = i < 25;
      sizes[i] = isHero ? 2.5 + Math.random() * 2.0 : 0.6 + Math.random() * 1.2;
      phases[i] = Math.random() * Math.PI * 2;
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geo.setAttribute('aColor', new THREE.Float32BufferAttribute(colors, 3));
    geo.setAttribute('aSize', new THREE.Float32BufferAttribute(sizes, 1));
    geo.setAttribute('aPhase', new THREE.Float32BufferAttribute(phases, 1));

    const mat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: {
        uTime: { value: 0 },
        uPixelRatio: { value: Math.min(window.devicePixelRatio, 2) },
      },
      vertexShader: `
        attribute vec3 aColor;
        attribute float aSize;
        attribute float aPhase;
        uniform float uTime;
        uniform float uPixelRatio;
        varying vec3 vColor;
        varying float vAlpha;

        void main() {
          vColor = aColor;
          float twinkle = 0.6 + 0.4 * sin(uTime * (0.8 + aPhase * 0.5) + aPhase * 6.2831);
          vAlpha = twinkle * (aSize > 2.0 ? 0.9 : 0.55);

          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = aSize * uPixelRatio * (200.0 / -mvPosition.z);
          gl_PointSize = clamp(gl_PointSize, 0.5, 8.0);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        varying float vAlpha;

        void main() {
          vec2 center = gl_PointCoord - 0.5;
          float dist = length(center);
          float alpha = vAlpha * smoothstep(0.5, 0.1, dist);
          if (alpha < 0.01) discard;
          gl_FragColor = vec4(vColor * 1.3, alpha);
        }
      `,
    });

    return { geometry: geo, material: mat };
  }, []);

  useFrame((state) => {
    material.uniforms.uTime.value = state.clock.getElapsedTime();
    if (pointsRef.current) {
      // Very slow counter-rotation for parallax
      pointsRef.current.rotation.y = scrollState.sp * 0.08;
      pointsRef.current.rotation.x = scrollState.sp * 0.03;
    }
  });

  return <points ref={pointsRef} geometry={geometry} material={material} frustumCulled={false} />;
};

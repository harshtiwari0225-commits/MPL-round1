import React, { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { scrollState } from '../state/scrollController';

const createNebulaPlane = (color1: string, color2: string, seed: number) => {
  return new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    uniforms: {
      uTime: { value: 0 },
      uColor1: { value: new THREE.Color(color1) },
      uColor2: { value: new THREE.Color(color2) },
      uSeed: { value: seed },
      uOpacity: { value: 0.055 },
    },
    vertexShader: `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uTime;
      uniform vec3 uColor1;
      uniform vec3 uColor2;
      uniform float uSeed;
      uniform float uOpacity;
      varying vec2 vUv;

      // Simplex-style noise
      vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
      vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
      vec3 permute(vec3 x) { return mod289(((x * 34.0) + 1.0) * x); }

      float snoise(vec2 v) {
        const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
        vec2 i = floor(v + dot(v, C.yy));
        vec2 x0 = v - i + dot(i, C.xx);
        vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
        vec4 x12 = x0.xyxy + C.xxzz;
        x12.xy -= i1;
        i = mod289(i);
        vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
        vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
        m = m * m;
        m = m * m;
        vec3 x = 2.0 * fract(p * C.www) - 1.0;
        vec3 h = abs(x) - 0.5;
        vec3 ox = floor(x + 0.5);
        vec3 a0 = x - ox;
        m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
        vec3 g;
        g.x = a0.x * x0.x + h.x * x0.y;
        g.yz = a0.yz * x12.xz + h.yz * x12.yw;
        return 130.0 * dot(m, g);
      }

      void main() {
        vec2 uv = vUv;
        float t = uTime * 0.04;

        float n1 = snoise(uv * 2.0 + vec2(uSeed, t));
        float n2 = snoise(uv * 4.0 + vec2(t * 0.7, uSeed * 2.0));
        float n3 = snoise(uv * 1.2 + vec2(uSeed * 3.0, -t * 0.3));

        float noise = n1 * 0.5 + n2 * 0.3 + n3 * 0.2;
        noise = smoothstep(-0.2, 0.8, noise);

        // Soft radial falloff
        float radial = 1.0 - smoothstep(0.2, 0.5, length(uv - 0.5));

        vec3 color = mix(uColor1, uColor2, noise * 0.6 + 0.2);
        float alpha = noise * radial * uOpacity;

        if (alpha < 0.003) discard;
        gl_FragColor = vec4(color, alpha);
      }
    `,
  });
};

interface NebulaCloud {
  position: [number, number, number];
  rotation: [number, number, number];
  scale: number;
  color1: string;
  color2: string;
  seed: number;
}

const CLOUDS: NebulaCloud[] = [
  { position: [-40, 15, -30], rotation: [0.2, 0.3, 0.1], scale: 80, color1: '#1a0a2e', color2: '#06b6d4', seed: 1.0 },
  { position: [35, 5, -60], rotation: [-0.1, 0.5, 0.2], scale: 90, color1: '#2d0a3e', color2: '#a855f7', seed: 2.3 },
  { position: [-20, -5, -100], rotation: [0.3, -0.2, 0.4], scale: 100, color1: '#0a1a2e', color2: '#2dd4bf', seed: 3.7 },
  { position: [50, 20, -140], rotation: [-0.2, 0.1, -0.3], scale: 85, color1: '#1e0a28', color2: '#ec4899', seed: 4.1 },
  { position: [-45, 0, -170], rotation: [0.1, -0.4, 0.2], scale: 95, color1: '#0a0e2e', color2: '#6366f1', seed: 5.5 },
  { position: [30, 12, -20], rotation: [0.4, 0.2, -0.1], scale: 70, color1: '#1a0520', color2: '#f59e0b', seed: 6.8 },
];

export const NebulaFog: React.FC = () => {
  const materialsRef = useRef<THREE.ShaderMaterial[]>([]);
  const groupRef = useRef<THREE.Group>(null);

  const materials = useMemo(() => {
    const mats = CLOUDS.map(c => createNebulaPlane(c.color1, c.color2, c.seed));
    materialsRef.current = mats;
    return mats;
  }, []);

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    materialsRef.current.forEach(m => {
      m.uniforms.uTime.value = t;
    });
    if (groupRef.current) {
      // Very subtle drift with scroll
      groupRef.current.position.x = scrollState.sp * 2.0;
      groupRef.current.position.y = Math.sin(scrollState.sp * Math.PI) * 1.5;
    }
  });

  return (
    <group ref={groupRef}>
      {CLOUDS.map((cloud, i) => (
        <mesh
          key={i}
          position={cloud.position}
          rotation={cloud.rotation}
          material={materials[i]}
          frustumCulled={false}
        >
          <planeGeometry args={[cloud.scale, cloud.scale]} />
        </mesh>
      ))}
    </group>
  );
};

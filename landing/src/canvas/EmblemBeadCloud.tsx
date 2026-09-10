import React, { useMemo, useEffect, useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { scrollState, smoothstep } from '../state/scrollController';

// Color utilities for palette remapping
// Primitives:
// Gold: #eab308 (h ~0.12), Starlight: #f8fafc (S < 0.12), Deep Navy: #0b0f20 / #1b2552 (h ~0.62)
const remapColor = (r: number, g: number, b: number): [number, number, number] => {
  const color = new THREE.Color(r / 255, g / 255, b / 255);
  const hsl = { h: 0, s: 0, l: 0 };
  color.getHSL(hsl);

  // Preserve specular highlights (S < 0.12) as raw starlight white (#f8fafc)
  if (hsl.s < 0.12 || hsl.l > 0.85) {
    return [0.97, 0.98, 0.99];
  }

  // Determine whether to pull toward Gold (h ~0.12) or Deep Celestial Navy (h ~0.62)
  // Warm hues (yellows, golds, oranges) -> Gold
  const isGoldCandidate = (hsl.h < 0.22 || hsl.h > 0.92) && hsl.l > 0.3;
  const targetH = isGoldCandidate ? 0.12 : 0.62;
  const targetS = isGoldCandidate ? 0.92 : 0.65;

  // 85% pull while preserving native luminescence
  const finalH = hsl.h * 0.15 + targetH * 0.85;
  const finalS = hsl.s * 0.15 + targetS * 0.85;
  const finalL = Math.max(0.08, Math.min(0.92, hsl.l));

  const remapped = new THREE.Color().setHSL(finalH, finalS, finalL);
  return [remapped.r, remapped.g, remapped.b];
};

// Generic sampler from pixel data
export const sampleFromImageData = (
  data: Uint8ClampedArray,
  width: number,
  height: number,
  count: number
) => {
  const validPixels: { x: number; y: number; r: number; g: number; b: number }[] = [];
  let minX = width;
  let maxX = 0;
  let minY = height;
  let maxY = 0;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4;
      const r = data[idx];
      const g = data[idx + 1];
      const b = data[idx + 2];
      const a = data[idx + 3];

      // Keep beads wherever alpha > 0.3 (76 / 255)
      if (a > 76) {
        validPixels.push({ x, y, r, g, b });
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }

  if (validPixels.length === 0) return null;

  const positions = new Float32Array(count * 3);
  const dispersePositions = new Float32Array(count * 3);
  const normals = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const randoms = new Float32Array(count * 4);

  const boundHeight = Math.max(1, maxY - minY);
  // Scale to bounding height of 14 units
  const scale = 14.0 / boundHeight;
  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const totalValid = validPixels.length;
  const step = totalValid / count;

  for (let i = 0; i < count; i++) {
    const pIdx = Math.floor((i * step) % totalValid);
    const p = validPixels[pIdx];

    // Canvas to world space centered at (0, 8, 0) with height 14 units
    const wx = (p.x - centerX) * scale;
    const wy = 8.0 - (p.y - centerY) * scale;

    // Subtle 3D dome curvature: crest curves outward in Z
    const distFromCenter = Math.sqrt(wx * wx + (wy - 8.0) * (wy - 8.0));
    const maxR = 7.0;
    const dome = Math.max(0, 1.0 - (distFromCenter / maxR) ** 2);
    const wz = dome * 1.6 + (Math.random() - 0.5) * 0.25;

    positions[i * 3 + 0] = wx;
    positions[i * 3 + 1] = wy;
    positions[i * 3 + 2] = wz;

    // Form normals calculated as bead offsets from the EMBLEM'S OWN local centroid:
    // n.set(x, (y - 8.0) * 0.15, z).normalize(), preventing flat radial shading
    const nx = wx;
    const ny = (wy - 8.0) * 0.15;
    const nz = wz + 0.3;
    const len = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1.0;
    normals[i * 3 + 0] = nx / len;
    normals[i * 3 + 1] = ny / len;
    normals[i * 3 + 2] = nz / len;

    // Remap sampled logo colors to primary palette
    const [cr, cg, cb] = remapColor(p.r, p.g, p.b);
    colors[i * 3 + 0] = cr;
    colors[i * 3 + 1] = cg;
    colors[i * 3 + 2] = cb;

    // Cosmic Dispersal coordinates for Act 1 synthesis
    const phi = Math.random() * Math.PI * 2;
    const theta = Math.acos(Math.random() * 2 - 1);
    const r = 25.0 + Math.random() * 35.0;
    dispersePositions[i * 3 + 0] = r * Math.sin(theta) * Math.cos(phi);
    dispersePositions[i * 3 + 1] = 8.0 + r * Math.sin(theta) * Math.sin(phi);
    dispersePositions[i * 3 + 2] = r * Math.cos(theta);

    randoms[i * 4 + 0] = Math.random();
    randoms[i * 4 + 1] = Math.random();
    randoms[i * 4 + 2] = Math.random();
    randoms[i * 4 + 3] = 0.5 + Math.random() * 1.5;
  }

  return { positions, dispersePositions, normals, colors, randoms };
};

// Fallback procedural canvas plate
const generateFallbackPlateAndSample = (count: number) => {
  const width = 512;
  const height = 512;
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('2D context unavailable');

  ctx.clearRect(0, 0, width, height);

  // Shield plate
  ctx.beginPath();
  ctx.moveTo(256, 470);
  ctx.bezierCurveTo(150, 420, 90, 310, 90, 180);
  ctx.lineTo(90, 140);
  ctx.lineTo(256, 110);
  ctx.lineTo(422, 140);
  ctx.lineTo(422, 180);
  ctx.bezierCurveTo(422, 310, 362, 420, 256, 470);
  ctx.closePath();
  ctx.fillStyle = '#0b0f20';
  ctx.fill();
  ctx.lineWidth = 14;
  ctx.strokeStyle = '#eab308';
  ctx.stroke();

  // Crown
  ctx.beginPath();
  ctx.moveTo(170, 115);
  ctx.lineTo(150, 50);
  ctx.lineTo(210, 85);
  ctx.lineTo(256, 35);
  ctx.lineTo(302, 85);
  ctx.lineTo(362, 50);
  ctx.lineTo(342, 115);
  ctx.closePath();
  ctx.fillStyle = '#eab308';
  ctx.fill();

  // Banner
  ctx.font = '900 64px "Space Grotesk", sans-serif';
  ctx.fillStyle = '#f8fafc';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('MPL', 256, 280);

  const imgData = ctx.getImageData(0, 0, width, height);
  return sampleFromImageData(imgData.data, width, height, count)!;
};

// 40,000 Instanced Spheres Shader Material
const createBeadShaderMaterial = () => {
  return new THREE.ShaderMaterial({
    uniforms: {
      uSp: { value: 0 },
      uCursor: { value: new THREE.Vector2(0, 0) },
      uReducedMotion: { value: 0 },
      uTime: { value: 0 },
    },
    vertexShader: `
      attribute vec3 aDispersePos;
      attribute vec3 aTargetPos;
      attribute vec3 aCustomNormal;
      attribute vec3 aColor;
      attribute vec4 aRandom;

      uniform float uSp;
      uniform vec2 uCursor;
      uniform float uReducedMotion;

      varying vec3 vColor;
      varying vec3 vNormal;
      varying vec3 vViewPosition;

      void main() {
        vColor = aColor;

        // Act 1 Singularity: Crest forms the razor-sharp official Math Premier League logo plate.
        // As the user scrolls toward Act 2 (sp 0.14 -> 0.32), beads accelerate and disperse into the tunnel
        float disperseProgress = smoothstep(0.14, 0.32, uSp);
        vec3 worldPos = mix(aTargetPos, aDispersePos, disperseProgress);

        // Idle micro-float and gentle cursor parallax tilt around local centroid (0, 8, 0)
        vec3 local = worldPos - vec3(0.0, 8.0, 0.0);

        float tiltFactor = (1.0 - uReducedMotion);
        float tiltX = uCursor.y * 0.18 * tiltFactor;
        float tiltY = uCursor.x * 0.25 * tiltFactor;

        // Subtle rotation around Y with sp
        float rotY = tiltY + (uSp * 0.9);
        float cY = cos(rotY);
        float sY = sin(rotY);
        vec3 rotated = vec3(
          local.x * cY + local.z * sY,
          local.y,
          -local.x * sY + local.z * cY
        );

        // Pitch tilt around X
        float cX = cos(tiltX);
        float sX = sin(tiltX);
        rotated = vec3(
          rotated.x,
          rotated.y * cX - rotated.z * sX,
          rotated.y * sX + rotated.z * cX
        );

        // Micro float
        float microFloat = sin(uSp * 12.0 + aRandom.y * 6.28) * 0.15 * tiltFactor;
        rotated.y += microFloat;

        vec3 finalPos = rotated + vec3(0.0, 8.0, 0.0);

        // Scale sphere bead instance (r 0.45)
        // Scaled for crisp legibility and bead density
        float instanceScale = 0.075 * mix(1.0, 0.5, disperseProgress);
        vec3 transformed = position * instanceScale + finalPos;

        vNormal = normalize(normalMatrix * aCustomNormal);
        vec4 mvPosition = modelViewMatrix * vec4(transformed, 1.0);
        vViewPosition = -mvPosition.xyz;
        gl_Position = projectionMatrix * mvPosition;
      }
    `,
    fragmentShader: `
      varying vec3 vColor;
      varying vec3 vNormal;
      varying vec3 vViewPosition;

      void main() {
        vec3 N = normalize(vNormal);
        vec3 V = normalize(vViewPosition);

        // Stellar key light (from top-front-right)
        vec3 L1 = normalize(vec3(0.5, 0.8, 0.7));
        float diff1 = max(dot(N, L1), 0.0);

        // Ambient cosmic navy fill light (from below)
        vec3 L2 = normalize(vec3(-0.4, -0.6, -0.5));
        float diff2 = max(dot(N, L2), 0.0) * 0.35;

        // Blinn-Phong specular highlight
        vec3 H = normalize(L1 + V);
        float spec = pow(max(dot(N, H), 0.0), 32.0) * 0.85;

        // Radiant color assembly
        vec3 diffuseColor = vColor * (diff1 * 0.95 + 0.15) + vec3(0.04, 0.08, 0.18) * diff2;
        vec3 finalColor = diffuseColor + vec3(0.98, 0.95, 0.85) * spec;

        gl_FragColor = vec4(finalColor, 1.0);
      }
    `,
  });
};

export const EmblemBeadCloud: React.FC = () => {
  const COUNT = 40000;

  // Initial setup with fallback plate
  const initialData = useMemo(() => generateFallbackPlateAndSample(COUNT), [COUNT]);

  const sphereGeo = useMemo(() => new THREE.SphereGeometry(0.45, 8, 6), []);
  const shaderMat = useMemo(() => createBeadShaderMaterial(), []);

  // Set instanced attributes
  const instancedGeo = useMemo(() => {
    const geo = new THREE.InstancedBufferGeometry();
    geo.index = sphereGeo.index;
    geo.attributes.position = sphereGeo.attributes.position;
    geo.attributes.normal = sphereGeo.attributes.normal;
    geo.attributes.uv = sphereGeo.attributes.uv;
    geo.instanceCount = COUNT;
    geo.setAttribute('aTargetPos', new THREE.InstancedBufferAttribute(new Float32Array(initialData.positions), 3));
    geo.setAttribute('aDispersePos', new THREE.InstancedBufferAttribute(new Float32Array(initialData.dispersePositions), 3));
    geo.setAttribute('aCustomNormal', new THREE.InstancedBufferAttribute(new Float32Array(initialData.normals), 3));
    geo.setAttribute('aColor', new THREE.InstancedBufferAttribute(new Float32Array(initialData.colors), 3));
    geo.setAttribute('aRandom', new THREE.InstancedBufferAttribute(new Float32Array(initialData.randoms), 4));
    return geo;
  }, [sphereGeo, initialData, COUNT]);

  // Asynchronously sample from the uploaded logo image (/mpl_logo.png)
  useEffect(() => {
    const img = new Image();
    img.src = '/mpl_logo.png';
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.drawImage(img, 0, 0);
      const imgData = ctx.getImageData(0, 0, img.width, img.height);
      const sampled = sampleFromImageData(imgData.data, img.width, img.height, COUNT);
      if (!sampled || !instancedGeo) return;

      const targetPosAttr = instancedGeo.getAttribute('aTargetPos') as THREE.BufferAttribute;
      const normalAttr = instancedGeo.getAttribute('aCustomNormal') as THREE.BufferAttribute;
      const colorAttr = instancedGeo.getAttribute('aColor') as THREE.BufferAttribute;

      if (targetPosAttr && normalAttr && colorAttr) {
        targetPosAttr.copyArray(sampled.positions);
        targetPosAttr.needsUpdate = true;

        normalAttr.copyArray(sampled.normals);
        normalAttr.needsUpdate = true;

        colorAttr.copyArray(sampled.colors);
        colorAttr.needsUpdate = true;
      }
    };
  }, [instancedGeo, COUNT]);

  useFrame(() => {
    // Read strictly from single mutable scrollState ref (zero React re-renders)
    shaderMat.uniforms.uSp.value = scrollState.sp;
    shaderMat.uniforms.uCursor.value.set(scrollState.cursor.x, scrollState.cursor.y);
    shaderMat.uniforms.uReducedMotion.value = scrollState.reducedMotion ? 1.0 : 0.0;
  });

  return (
    <mesh geometry={instancedGeo} material={shaderMat} frustumCulled={false} />
  );
};

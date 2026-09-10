import React, { useEffect, useRef } from 'react';
import { scrollState, smoothstep, clamp01 } from '../state/scrollController';
import { TournamentDock } from './TournamentDock';
import { Compass, Gauge, Activity, Radio, Cpu, Target, Zap, Swords } from 'lucide-react';

export const HudOverlay: React.FC = () => {
  // Direct DOM references for zero React re-renders on scroll
  const spRef = useRef<HTMLSpanElement>(null);
  const pRef = useRef<HTMLSpanElement>(null);
  const velRef = useRef<HTMLSpanElement>(null);
  const altRef = useRef<HTMLSpanElement>(null);
  const actBadgeRef = useRef<HTMLDivElement>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);

  // Act text overlays
  const act1TextRef = useRef<HTMLDivElement>(null);
  const act2TextRef = useRef<HTMLDivElement>(null);
  const act3TextRef = useRef<HTMLDivElement>(null);
  const act4TextRef = useRef<HTMLDivElement>(null);
  const act5TextRef = useRef<HTMLDivElement>(null);

  // Realm Teasers in Act 4/5
  const realmTeasersRef = useRef<HTMLDivElement>(null);

  // Tournament Dock container
  const dockContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let animId: number;

    const updateHud = () => {
      const p = scrollState.p;
      const sp = scrollState.sp;
      const vel = Math.abs(scrollState.velocity * 1000);

      // 1. Numeric telemetry updates
      if (spRef.current) spRef.current.textContent = sp.toFixed(3);
      if (pRef.current) pRef.current.textContent = p.toFixed(3);
      if (velRef.current) velRef.current.textContent = `${(12.4 + vel * 2.8).toFixed(1)} km/s`;
      if (altRef.current) {
        const alt = Math.max(0, 320 - sp * 290);
        altRef.current.textContent = `${alt.toFixed(1)} AU`;
      }

      // 2. Progress bar
      if (progressBarRef.current) {
        progressBarRef.current.style.width = `${p * 100}%`;
      }

      // 3. Dynamic Act Badge text
      if (actBadgeRef.current) {
        let label = 'ACT I // THE SINGULARITY';
        let badgeColor = '#eab308';

        if (p >= 0.80) {
          label = 'ACT VI // HORIZON BREAK';
          badgeColor = '#fde047';
        } else if (sp > 0.68) {
          label = 'ACT V // TOURNAMENT CORE';
          badgeColor = '#eab308';
        } else if (sp > 0.48) {
          label = 'ACT IV // REALM CONVERGENCE';
          badgeColor = '#2dd4bf';
        } else if (sp > 0.32) {
          label = 'ACT III // GRAVITY SLINGSHOT';
          badgeColor = '#06b6d4';
        } else if (sp > 0.16) {
          label = 'ACT II // CELESTIAL TUNNEL';
          badgeColor = '#06b6d4';
        }
        actBadgeRef.current.textContent = label;
        actBadgeRef.current.style.color = badgeColor;
        actBadgeRef.current.style.borderColor = badgeColor;
      }

      // 4. Act 1 Typography Overlay (sp 0.00 -> 0.20)
      if (act1TextRef.current) {
        const a1In = 1.0 - smoothstep(0.12, 0.20, sp);
        act1TextRef.current.style.opacity = `${a1In}`;
        act1TextRef.current.style.transform = `translateY(${-sp * 60}px)`;
      }

      // 5. Act 2 Typography Overlay (sp 0.18 -> 0.36)
      if (act2TextRef.current) {
        const a2In = smoothstep(0.16, 0.24, sp);
        const a2Out = 1.0 - smoothstep(0.32, 0.38, sp);
        const a2Alpha = a2In * a2Out;
        act2TextRef.current.style.opacity = `${a2Alpha}`;
        act2TextRef.current.style.transform = `translateY(${(1 - a2In) * 30 - smoothstep(0.30, 0.38, sp) * 30}px)`;
      }

      // 6. Act 3 Typography Overlay (sp 0.34 -> 0.54)
      if (act3TextRef.current) {
        const a3In = smoothstep(0.32, 0.40, sp);
        const a3Out = 1.0 - smoothstep(0.48, 0.56, sp);
        const a3Alpha = a3In * a3Out;
        act3TextRef.current.style.opacity = `${a3Alpha}`;
        act3TextRef.current.style.transform = `translateY(${(1 - a3In) * 30 - smoothstep(0.46, 0.56, sp) * 30}px)`;
      }

      // 7. Act 4 Typography Overlay (sp 0.52 -> 0.72)
      if (act4TextRef.current) {
        const a4In = smoothstep(0.50, 0.58, sp);
        const a4Out = 1.0 - smoothstep(0.68, 0.75, sp);
        const a4Alpha = a4In * a4Out;
        act4TextRef.current.style.opacity = `${a4Alpha}`;
        act4TextRef.current.style.transform = `translateY(${(1 - a4In) * 30 - smoothstep(0.66, 0.75, sp) * 30}px)`;
      }

      // 8. Act 5 Typography Overlay (sp 0.70 -> 0.86)
      if (act5TextRef.current) {
        const a5In = smoothstep(0.68, 0.76, sp);
        const a5Out = 1.0 - smoothstep(0.82, 0.90, sp);
        const a5Alpha = a5In * a5Out;
        act5TextRef.current.style.opacity = `${a5Alpha}`;
        act5TextRef.current.style.transform = `translateY(${(1 - a5In) * 30}px)`;
      }

      // 9. Act 4 & 5 Realm Preview Cards (smooth CSS transform + blur without React re-render)
      if (realmTeasersRef.current) {
        const rIn = smoothstep(0.54, 0.64, sp);
        const rOut = 1.0 - smoothstep(0.80, 0.88, sp);
        const rAlpha = rIn * rOut;
        const blur = (1.0 - rIn) * 8;
        const translateY = (1.0 - rIn) * 40;
        realmTeasersRef.current.style.opacity = `${rAlpha}`;
        realmTeasersRef.current.style.filter = `blur(${blur}px)`;
        realmTeasersRef.current.style.transform = `translateY(${translateY}px)`;
      }

      // 10. Act 6 Tournament Dock (runs on real p: 0.80 -> 1.0)
      if (dockContainerRef.current) {
        const dockAlpha = smoothstep(0.80, 0.94, p);
        const dockY = (1.0 - dockAlpha) * 40;
        dockContainerRef.current.style.opacity = `${dockAlpha}`;
        dockContainerRef.current.style.transform = `translateY(${dockY}px)`;
        dockContainerRef.current.style.pointerEvents = dockAlpha > 0.4 ? 'auto' : 'none';
      }

      animId = requestAnimationFrame(updateHud);
    };

    animId = requestAnimationFrame(updateHud);
    return () => cancelAnimationFrame(animId);
  }, []);

  return (
    <div className="hud-layer">
      {/* ── TOP HUD NAVIGATION / TELEMETRY ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', width: '100%' }}>
        {/* Brand & Badge */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <img
              src="/mpl_logo.png"
              alt="MPL Crest"
              style={{
                width: '34px',
                height: '34px',
                objectFit: 'contain',
                filter: 'drop-shadow(0 0 10px rgba(234, 179, 8, 0.6))',
              }}
            />
            <span style={{ fontWeight: 800, fontSize: '15px', letterSpacing: '0.12em', color: '#f8fafc' }}>
              MATH PREMIER LEAGUE
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              ref={actBadgeRef}
              className="mono-label"
              style={{
                border: '1px solid #eab308',
                borderRadius: '6px',
                padding: '3px 8px',
                fontSize: '10px',
                background: 'rgba(7, 9, 19, 0.7)',
              }}
            >
              ACT I // THE SINGULARITY
            </span>
            <span className="mono-label" style={{ color: '#64748b' }}>
              STAGE 2200vh
            </span>
          </div>
        </div>

        {/* Live Flight Telemetry Readouts */}
        <div
          className="glass-panel"
          style={{
            padding: '10px 18px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            gap: '20px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Compass size={14} color="#06b6d4" />
            <div>
              <div className="mono-label" style={{ fontSize: '9px' }}>AXIS [sp]</div>
              <span ref={spRef} className="mono-value" style={{ color: '#06b6d4' }}>0.000</span>
            </div>
          </div>

          <div style={{ width: '1px', height: '22px', background: 'rgba(148, 163, 184, 0.15)' }} />

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Gauge size={14} color="#2dd4bf" />
            <div>
              <div className="mono-label" style={{ fontSize: '9px' }}>TRACK [p]</div>
              <span ref={pRef} className="mono-value" style={{ color: '#2dd4bf' }}>0.000</span>
            </div>
          </div>

          <div style={{ width: '1px', height: '22px', background: 'rgba(148, 163, 184, 0.15)' }} />

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={14} color="#fde047" />
            <div>
              <div className="mono-label" style={{ fontSize: '9px' }}>VELOCITY</div>
              <span ref={velRef} className="mono-value" style={{ color: '#fde047' }}>12.4 km/s</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── CENTER CINEMATIC ACT TEXT OVERLAYS ── */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', textAlign: 'center' }}>
        {/* ACT 1: The Singularity / Logo Synthesis */}
        <div
          ref={act1TextRef}
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'flex-end',
            paddingBottom: '55px',
            opacity: 1,
            transform: 'translateY(0px)',
          }}
        >
          <span className="mono-label" style={{ color: '#fde047', letterSpacing: '0.25em', marginBottom: '6px' }}>
            COSMIC HACKATHON ARENA
          </span>
          <h1
            className="gold-glow-text"
            style={{
              fontSize: 'clamp(1.5rem, 3.2vw, 2.5rem)',
              fontWeight: 800,
              lineHeight: 1.1,
              maxWidth: '850px',
              textTransform: 'uppercase',
            }}
          >
            MATH PREMIER LEAGUE
          </h1>
          <p style={{ color: '#94a3b8', maxWidth: '520px', marginTop: '6px', fontSize: '0.85rem', lineHeight: 1.4 }}>
            40,000 Instanced Celestial Spheres // Fixed-frame deterministic scroll flight
          </p>
          <div className="scroll-hint" style={{ marginTop: '12px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#eab308' }} />
            SCROLL TO ENGAGE FLIGHT CORRIDOR
          </div>
        </div>

        {/* ACT 2: Cosmic Coordinate Acceleration */}
        <div
          ref={act2TextRef}
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: 0,
          }}
        >
          <span className="mono-label" style={{ color: '#06b6d4', letterSpacing: '0.25em', marginBottom: '8px' }}>
            ACT II // COORDINATE VECTOR
          </span>
          <h2 style={{ fontSize: 'clamp(2rem, 5vw, 3.8rem)', fontWeight: 700, color: '#f8fafc', textTransform: 'uppercase' }}>
            COSMIC ACCELERATION
          </h2>
          <p style={{ color: '#94a3b8', maxWidth: '480px', marginTop: '12px', fontSize: '0.95rem' }}>
            Concentric celestial cylinders align. Archimedean geodesics ignite along the speed corridor.
          </p>
        </div>

        {/* ACT 3: Gravitational Slingshot */}
        <div
          ref={act3TextRef}
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: 0,
          }}
        >
          <span className="mono-label" style={{ color: '#fde047', letterSpacing: '0.25em', marginBottom: '8px' }}>
            ACT III // GRAVITATIONAL SLINGSHOT
          </span>
          <h2 style={{ fontSize: 'clamp(2rem, 5vw, 3.8rem)', fontWeight: 700, color: '#f8fafc', textTransform: 'uppercase' }}>
            RODRIGUES VIEW BANK
          </h2>
          <p style={{ color: '#94a3b8', maxWidth: '500px', marginTop: '12px', fontSize: '0.95rem' }}>
            Dynamic lateral & dip vectors engaged. Camera up-vector rolls around the flight trajectory axis.
          </p>
        </div>

        {/* ACT 4: Convergence of Realms */}
        <div
          ref={act4TextRef}
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: 0,
          }}
        >
          <span className="mono-label" style={{ color: '#2dd4bf', letterSpacing: '0.25em', marginBottom: '8px' }}>
            ACT IV // REALM CONVERGENCE
          </span>
          <h2 style={{ fontSize: 'clamp(2rem, 5vw, 3.8rem)', fontWeight: 700, color: '#f8fafc', textTransform: 'uppercase' }}>
            THE THREE REALMS
          </h2>
          <p style={{ color: '#94a3b8', maxWidth: '520px', marginTop: '12px', fontSize: '0.95rem' }}>
            Main Problem Reticle • Bonus Bidding Nexus • Challenge Dueling Arena
          </p>
        </div>

        {/* ACT 5: Tournament Core */}
        <div
          ref={act5TextRef}
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: 0,
          }}
        >
          <span className="mono-label" style={{ color: '#eab308', letterSpacing: '0.25em', marginBottom: '8px' }}>
            ACT V // TOURNAMENT CORE
          </span>
          <h2 className="gold-glow-text" style={{ fontSize: 'clamp(2rem, 5vw, 3.8rem)', fontWeight: 800, textTransform: 'uppercase' }}>
            EQUATION LOCKED
          </h2>
          <p style={{ color: '#94a3b8', maxWidth: '480px', marginTop: '12px', fontSize: '0.95rem' }}>
            Accretion ring dust settles. Battle arena nodes synchronize with real-time Judge0 cluster.
          </p>
        </div>
      </div>

      {/* ── ACT 4/5 FLOATING REALM TEASER CARDS ── */}
      <div
        ref={realmTeasersRef}
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'center',
          gap: '16px',
          opacity: 0,
          pointerEvents: 'none',
          paddingBottom: '20px',
        }}
      >
        <div className="glass-panel" style={{ padding: '12px 20px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Target size={16} color="#06b6d4" />
          <span className="mono-label" style={{ color: '#f8fafc' }}>I. DEBUG & ALGO</span>
        </div>
        <div className="glass-panel" style={{ padding: '12px 20px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Zap size={16} color="#2dd4bf" />
          <span className="mono-label" style={{ color: '#f8fafc' }}>II. BONUS WAGER</span>
        </div>
        <div className="glass-panel" style={{ padding: '12px 20px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Swords size={16} color="#eab308" />
          <span className="mono-label" style={{ color: '#f8fafc' }}>III. ARENA DUEL</span>
        </div>
      </div>

      {/* ── ACT 6 TOURNAMENT DOCK OVERLAY ── */}
      <TournamentDock dockRef={dockContainerRef} />

      {/* ── BOTTOM GLOBAL PROGRESS BAR ── */}
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#64748b' }}>
          <span className="mono-label" style={{ fontSize: '9px', color: '#64748b' }}>SINGULARITY</span>
          <span className="mono-label" style={{ fontSize: '9px', color: '#64748b' }}>TRAJECTORY</span>
          <span className="mono-label" style={{ fontSize: '9px', color: '#64748b' }}>CONVERGENCE</span>
          <span className="mono-label" style={{ fontSize: '9px', color: '#eab308' }}>DOCK PORTAL</span>
        </div>
        <div
          style={{
            width: '100%',
            height: '3px',
            background: 'rgba(148, 163, 184, 0.12)',
            borderRadius: '2px',
            overflow: 'hidden',
          }}
        >
          <div
            ref={progressBarRef}
            style={{
              width: '0%',
              height: '100%',
              background: 'linear-gradient(90deg, #06b6d4, #2dd4bf, #eab308)',
              boxShadow: '0 0 10px rgba(234, 179, 8, 0.5)',
            }}
          />
        </div>
      </div>
    </div>
  );
};

import React, { useEffect, useRef } from 'react';
import { scrollState, smoothstep } from '../state/scrollController';
import { LoginPortal } from './LoginPortal';
import { Compass, Gauge, Activity, Lock } from 'lucide-react';

export const HudOverlay: React.FC = () => {
  // Direct DOM references for zero React re-renders on scroll
  const spRef = useRef<HTMLSpanElement>(null);
  const pRef = useRef<HTMLSpanElement>(null);
  const velRef = useRef<HTMLSpanElement>(null);
  const actBadgeRef = useRef<HTMLDivElement>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);

  // Act typography overlays
  const act1TextRef = useRef<HTMLDivElement>(null);
  const act2TextRef = useRef<HTMLDivElement>(null);
  const act3TextRef = useRef<HTMLDivElement>(null);

  // Act 4 Login Portal ref
  const loginPortalRef = useRef<HTMLDivElement>(null);

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

      // 2. Progress bar
      if (progressBarRef.current) {
        progressBarRef.current.style.width = `${p * 100}%`;
      }

      // 3. Dynamic Act Badge text
      if (actBadgeRef.current) {
        let label = 'ACT I // THE SINGULARITY';
        let badgeColor = '#eab308';

        if (sp >= 0.48) {
          label = 'ACT IV // TEAM LOGIN';
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

      // 4. Act 1: Center text removed per user specification
      if (act1TextRef.current) {
        act1TextRef.current.style.display = 'none';
      }

      // 5. Act 2 Typography Overlay (sp 0.18 -> 0.36)
      if (act2TextRef.current) {
        const a2In = smoothstep(0.16, 0.24, sp);
        const a2Out = 1.0 - smoothstep(0.32, 0.38, sp);
        const a2Alpha = a2In * a2Out;
        act2TextRef.current.style.opacity = `${a2Alpha}`;
        act2TextRef.current.style.transform = `translateY(${(1 - a2In) * 30 - smoothstep(0.30, 0.38, sp) * 30}px)`;
      }

      // 6. Act 3 Typography Overlay (sp 0.34 -> 0.52)
      if (act3TextRef.current) {
        const a3In = smoothstep(0.32, 0.40, sp);
        const a3Out = 1.0 - smoothstep(0.48, 0.54, sp);
        const a3Alpha = a3In * a3Out;
        act3TextRef.current.style.opacity = `${a3Alpha}`;
        act3TextRef.current.style.transform = `translateY(${(1 - a3In) * 30 - smoothstep(0.46, 0.54, sp) * 30}px)`;
      }

      // 7. Act 4: Team Login Portal (docks in smoothly at sp >= 0.48 -> 1.0)
      if (loginPortalRef.current) {
        const a4In = smoothstep(0.46, 0.60, sp);
        loginPortalRef.current.style.opacity = `${a4In}`;
        loginPortalRef.current.style.transform = `translateY(${(1.0 - a4In) * 35}px)`;
        loginPortalRef.current.style.pointerEvents = a4In > 0.5 ? 'auto' : 'none';
        loginPortalRef.current.style.visibility = a4In < 0.01 ? 'hidden' : 'visible';
      }

      animId = requestAnimationFrame(updateHud);
    };

    animId = requestAnimationFrame(updateHud);
    return () => cancelAnimationFrame(animId);
  }, []);

  const scrollToLogin = () => {
    const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
    window.scrollTo({
      top: scrollHeight * 0.70,
      behavior: 'smooth',
    });
  };

  return (
    <div className="hud-layer">
      {/* ── TOP HUD NAVIGATION / TELEMETRY ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', width: '100%', pointerEvents: 'auto' }}>
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
                color: '#eab308',
              }}
            >
              ACT I // THE SINGULARITY
            </span>
            <span className="mono-label" style={{ color: '#64748b' }}>
              ONLINE ARENA
            </span>
          </div>
        </div>

        {/* Live Flight Telemetry Readouts + Quick Login Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            className="glass-panel"
            style={{
              padding: '8px 16px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Compass size={13} color="#06b6d4" />
              <div>
                <div className="mono-label" style={{ fontSize: '8px' }}>AXIS [sp]</div>
                <span ref={spRef} className="mono-value" style={{ color: '#06b6d4', fontSize: '11px' }}>0.000</span>
              </div>
            </div>

            <div style={{ width: '1px', height: '18px', background: 'rgba(148, 163, 184, 0.15)' }} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Gauge size={13} color="#2dd4bf" />
              <div>
                <div className="mono-label" style={{ fontSize: '8px' }}>TRACK [p]</div>
                <span ref={pRef} className="mono-value" style={{ color: '#2dd4bf', fontSize: '11px' }}>0.000</span>
              </div>
            </div>

            <div style={{ width: '1px', height: '18px', background: 'rgba(148, 163, 184, 0.15)' }} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Activity size={13} color="#fde047" />
              <div>
                <div className="mono-label" style={{ fontSize: '8px' }}>VELOCITY</div>
                <span ref={velRef} className="mono-value" style={{ color: '#fde047', fontSize: '11px' }}>12.4 km/s</span>
              </div>
            </div>
          </div>

          <button
            onClick={scrollToLogin}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '7px',
              padding: '9px 16px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, rgba(234, 179, 8, 0.25), rgba(202, 138, 4, 0.15))',
              border: '1px solid rgba(234, 179, 8, 0.5)',
              color: '#fde047',
              fontWeight: 700,
              fontSize: '0.80rem',
              cursor: 'pointer',
              letterSpacing: '0.06em',
              boxShadow: '0 0 15px rgba(234, 179, 8, 0.25)',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'linear-gradient(135deg, #eab308, #ca8a04)';
              e.currentTarget.style.color = '#070913';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'linear-gradient(135deg, rgba(234, 179, 8, 0.25), rgba(202, 138, 4, 0.15))';
              e.currentTarget.style.color = '#fde047';
            }}
          >
            <Lock size={12} />
            <span>LOGIN</span>
          </button>
        </div>
      </div>

      {/* ── CENTER CINEMATIC ACT TEXT OVERLAYS ── */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', textAlign: 'center' }}>
        {/* ACT 1: Hidden div to prevent layout overhead */}
        <div ref={act1TextRef} style={{ display: 'none' }} />

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
      </div>

      {/* ── ACT 4: TEAM LOGIN PAGE ── */}
      <LoginPortal portalRef={loginPortalRef} />

      {/* ── BOTTOM GLOBAL PROGRESS BAR ── */}
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '6px', pointerEvents: 'none' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#64748b' }}>
          <span className="mono-label" style={{ fontSize: '9px', color: '#eab308' }}>I: SINGULARITY</span>
          <span className="mono-label" style={{ fontSize: '9px', color: '#06b6d4' }}>II: ACCELERATION</span>
          <span className="mono-label" style={{ fontSize: '9px', color: '#06b6d4' }}>III: SLINGSHOT</span>
          <span className="mono-label" style={{ fontSize: '9px', color: '#2dd4bf' }}>IV: TEAM LOGIN</span>
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
              background: 'linear-gradient(90deg, #eab308, #06b6d4, #2dd4bf)',
              boxShadow: '0 0 10px rgba(45, 212, 191, 0.5)',
            }}
          />
        </div>
      </div>
    </div>
  );
};

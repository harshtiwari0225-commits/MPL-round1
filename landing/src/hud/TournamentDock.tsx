import React from 'react';
import { Terminal, Swords, Zap, Trophy, ArrowUpRight, Shield } from 'lucide-react';

interface TournamentDockProps {
  dockRef: React.RefObject<HTMLDivElement>;
}

export const TournamentDock: React.FC<TournamentDockProps> = ({ dockRef }) => {
  return (
    <div
      ref={dockRef}
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        opacity: 0,
        pointerEvents: 'none',
        transform: 'translateY(40px)',
        transition: 'none', // Managed strictly as pure function of p in RAF
      }}
    >
      <div
        className="glass-panel-gold"
        style={{
          width: '100%',
          maxWidth: '1100px',
          borderRadius: '24px',
          padding: '36px 32px',
          display: 'flex',
          flexDirection: 'column',
          gap: '28px',
          boxShadow: '0 25px 50px -12px rgba(7, 9, 19, 0.9), 0 0 40px rgba(234, 179, 8, 0.2)',
          pointerEvents: 'auto',
        }}
      >
        {/* Header bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(234, 179, 8, 0.25)', paddingBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <img
              src="/mpl_logo.png"
              alt="MPL Crest"
              style={{
                width: '54px',
                height: '54px',
                objectFit: 'contain',
                filter: 'drop-shadow(0 0 15px rgba(234, 179, 8, 0.7))',
              }}
            />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span className="mono-label" style={{ color: '#fde047', letterSpacing: '0.2em' }}>
                  HORIZON BREAK // ACT VI
                </span>
              </div>
              <h2 style={{ fontSize: 'clamp(1.6rem, 3.5vw, 2.4rem)', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
                MATH PREMIER LEAGUE ARENA
              </h2>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span className="mono-label">SESSION STATUS</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#2dd4bf', boxShadow: '0 0 10px #2dd4bf' }} />
              <span className="mono-value" style={{ color: '#2dd4bf' }}>LIVE JUDGE CLUSTER</span>
            </div>
          </div>
        </div>

        {/* 4 Tournament Realm Cards */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '18px',
          }}
        >
          {/* Card 1: Main Arena */}
          <a
            href="/ui/main.html"
            className="glass-panel"
            style={{
              padding: '22px 20px',
              borderRadius: '16px',
              textDecoration: 'none',
              color: 'inherit',
              border: '1px solid rgba(234, 179, 8, 0.35)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '16px',
              background: 'linear-gradient(145deg, rgba(17, 24, 54, 0.85), rgba(11, 15, 32, 0.95))',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div style={{ padding: '8px', borderRadius: '10px', background: 'rgba(234, 179, 8, 0.15)', color: '#fde047' }}>
                  <Terminal size={22} />
                </div>
                <ArrowUpRight size={18} color="#eab308" />
              </div>
              <span className="mono-label" style={{ color: '#eab308' }}>MAIN CONSOLE</span>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: '#f8fafc', marginTop: '4px' }}>
                Coding Arena
              </h3>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '6px', lineHeight: 1.5 }}>
                3 Live Tracks: Debugging, Math Formulas, & LeetCode DSA with instant Judge0 feedback.
              </p>
            </div>
            <div style={{ borderTop: '1px solid rgba(148, 163, 184, 0.1)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <span style={{ color: '#64748b' }}>Weight</span>
              <span style={{ color: '#fde047', fontWeight: 600 }}>1200 PTS MAX</span>
            </div>
          </a>

          {/* Card 2: Challenge Arena */}
          <a
            href="/ui/challenge.html"
            className="glass-panel"
            style={{
              padding: '22px 20px',
              borderRadius: '16px',
              textDecoration: 'none',
              color: 'inherit',
              border: '1px solid rgba(6, 182, 212, 0.3)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '16px',
              background: 'linear-gradient(145deg, rgba(11, 15, 32, 0.9), rgba(7, 9, 19, 0.95))',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div style={{ padding: '8px', borderRadius: '10px', background: 'rgba(6, 182, 212, 0.15)', color: '#06b6d4' }}>
                  <Swords size={22} />
                </div>
                <ArrowUpRight size={18} color="#06b6d4" />
              </div>
              <span className="mono-label" style={{ color: '#06b6d4' }}>ROUND II</span>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: '#f8fafc', marginTop: '4px' }}>
                Challenge Mode
              </h3>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '6px', lineHeight: 1.5 }}>
                Head-to-head tactical dueling. Rapid submission speed and test case domination.
              </p>
            </div>
            <div style={{ borderTop: '1px solid rgba(148, 163, 184, 0.1)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <span style={{ color: '#64748b' }}>Format</span>
              <span style={{ color: '#67e8f9', fontWeight: 600 }}>1v1 DUEL</span>
            </div>
          </a>

          {/* Card 3: Bonus Bidding */}
          <a
            href="/ui/boost.html"
            className="glass-panel"
            style={{
              padding: '22px 20px',
              borderRadius: '16px',
              textDecoration: 'none',
              color: 'inherit',
              border: '1px solid rgba(45, 212, 191, 0.3)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '16px',
              background: 'linear-gradient(145deg, rgba(11, 15, 32, 0.9), rgba(7, 9, 19, 0.95))',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div style={{ padding: '8px', borderRadius: '10px', background: 'rgba(45, 212, 191, 0.15)', color: '#2dd4bf' }}>
                  <Zap size={22} />
                </div>
                <ArrowUpRight size={18} color="#2dd4bf" />
              </div>
              <span className="mono-label" style={{ color: '#2dd4bf' }}>TACTICAL POWER</span>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: '#f8fafc', marginTop: '4px' }}>
                Time Boost & Bids
              </h3>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '6px', lineHeight: 1.5 }}>
                Wager points for critical clock extensions and unlock strategic problem clues.
              </p>
            </div>
            <div style={{ borderTop: '1px solid rgba(148, 163, 184, 0.1)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <span style={{ color: '#64748b' }}>Wager</span>
              <span style={{ color: '#2dd4bf', fontWeight: 600 }}>POINT MULTIPLIER</span>
            </div>
          </a>

          {/* Card 4: Admin Deck */}
          <a
            href="/ui/admin.html"
            className="glass-panel"
            style={{
              padding: '22px 20px',
              borderRadius: '16px',
              textDecoration: 'none',
              color: 'inherit',
              border: '1px solid rgba(148, 163, 184, 0.25)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '16px',
              background: 'linear-gradient(145deg, rgba(11, 15, 32, 0.9), rgba(7, 9, 19, 0.95))',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div style={{ padding: '8px', borderRadius: '10px', background: 'rgba(148, 163, 184, 0.15)', color: '#f8fafc' }}>
                  <Trophy size={22} />
                </div>
                <ArrowUpRight size={18} color="#94a3b8" />
              </div>
              <span className="mono-label" style={{ color: '#94a3b8' }}>OPERATIONS</span>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: '#f8fafc', marginTop: '4px' }}>
                Live Leaderboard
              </h3>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '6px', lineHeight: 1.5 }}>
                Real-time team standings, admin judge controls, time bonuses, and re-judge queue.
              </p>
            </div>
            <div style={{ borderTop: '1px solid rgba(148, 163, 184, 0.1)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <span style={{ color: '#64748b' }}>Access</span>
              <span style={{ color: '#f8fafc', fontWeight: 600 }}>ALL TEAMS</span>
            </div>
          </a>
        </div>

        {/* Action button bar */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '14px', justifyContent: 'flex-end', paddingTop: '10px' }}>
          <a
            href="/ui/index.html"
            className="scroll-hint"
            style={{ textDecoration: 'none', color: '#94a3b8', padding: '10px 20px', borderRadius: '12px' }}
          >
            ARENA HUB
          </a>
          <a
            href="/ui/main.html"
            style={{
              textDecoration: 'none',
              padding: '10px 24px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #eab308, #ca8a04)',
              color: '#070913',
              fontWeight: 700,
              fontSize: '13px',
              letterSpacing: '0.08em',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 0 25px rgba(234, 179, 8, 0.4)',
            }}
          >
            ENTER CODING CONSOLE →
          </a>
        </div>
      </div>
    </div>
  );
};

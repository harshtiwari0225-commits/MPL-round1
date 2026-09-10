import React, { useState, useEffect } from 'react';
import { Shield, Key, ArrowRight, AlertCircle, CheckCircle2, Target, Zap, Swords, Eye, EyeOff, LogOut, Radio, RefreshCw } from 'lucide-react';

interface LoginPortalProps {
  portalRef: React.RefObject<HTMLDivElement>;
}

export const LoginPortal: React.FC<LoginPortalProps> = ({ portalRef }) => {
  const [teamName, setTeamName] = useState('');
  const [passcode, setPasscode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [selectedArena, setSelectedArena] = useState<'/ui/main.html' | '/ui/boost.html' | '/ui/challenge.html'>('/ui/main.html');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [savedTeam, setSavedTeam] = useState<string | null>(null);
  const [showManualForm, setShowManualForm] = useState(false);

  useEffect(() => {
    const existing = localStorage.getItem('mpl_team_name');
    const token = localStorage.getItem('mpl_session_token');
    if (existing && token) {
      setSavedTeam(existing);
    }
  }, []);

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);

    const name = teamName.trim();
    const pass = passcode.trim();

    if (!name || !pass) {
      setError('Please enter both team name and passcode.');
      return;
    }

    setLoading(true);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, passcode: pass }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || 'Invalid team name or passcode. Check your credentials.');
        setLoading(false);
        return;
      }

      const teamData = await res.json();
      localStorage.setItem('mpl_team_name', teamData.name);
      localStorage.setItem('mpl_passcode', pass);
      localStorage.setItem('mpl_session_token', teamData.session_token);

      const sessionObj = { id: teamData.id, name: teamData.name, token: teamData.session_token };
      sessionStorage.setItem('mpl_team', JSON.stringify(sessionObj));
      sessionStorage.setItem('mpl_boost_team', JSON.stringify(teamData));
      sessionStorage.setItem('mpl_challenge_team', JSON.stringify(teamData));

      setSuccess(true);
      setTimeout(() => {
        window.location.href = selectedArena;
      }, 700);
    } catch (err) {
      setError('Server connection error. Please verify backend status.');
      setLoading(false);
    }
  };

  const handleContinueSaved = () => {
    window.location.href = selectedArena;
  };

  const handleLogout = () => {
    localStorage.removeItem('mpl_team_name');
    localStorage.removeItem('mpl_passcode');
    localStorage.removeItem('mpl_session_token');
    sessionStorage.removeItem('mpl_team');
    sessionStorage.removeItem('mpl_boost_team');
    sessionStorage.removeItem('mpl_challenge_team');
    setSavedTeam(null);
    setShowManualForm(true);
    setTeamName('');
    setPasscode('');
  };

  return (
    <div
      ref={portalRef}
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        opacity: 0,
        pointerEvents: 'none',
        transform: 'translateY(30px)',
        zIndex: 50,
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '440px',
          borderRadius: '24px',
          padding: '28px 26px 22px 26px',
          background: 'linear-gradient(165deg, rgba(10, 15, 30, 0.94) 0%, rgba(5, 8, 18, 0.97) 100%)',
          backdropFilter: 'blur(32px) saturate(190%)',
          border: '1px solid rgba(234, 179, 8, 0.35)',
          boxShadow: '0 25px 65px -15px rgba(0, 0, 0, 0.95), 0 0 35px rgba(234, 179, 8, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.12)',
          pointerEvents: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '18px',
          position: 'relative',
        }}
      >
        {/* Subtle glowing top accent line */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: '15%',
            right: '15%',
            height: '2px',
            background: 'linear-gradient(90deg, transparent, #eab308, #2dd4bf, transparent)',
            borderRadius: '2px',
          }}
        />

        {/* ── HEADER ── */}
        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          {/* Logo Badge with luminous aura */}
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '16px',
              background: 'radial-gradient(circle, rgba(234, 179, 8, 0.20) 0%, rgba(15, 23, 42, 0.6) 80%)',
              border: '1px solid rgba(234, 179, 8, 0.45)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '10px',
              boxShadow: '0 0 20px rgba(234, 179, 8, 0.25)',
            }}
          >
            <img
              src="/mpl_logo.png"
              alt="MPL Logo"
              style={{ width: '40px', height: '40px', objectFit: 'contain', filter: 'drop-shadow(0 0 6px rgba(234, 179, 8, 0.8))' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#22c55e', boxShadow: '0 0 6px #22c55e' }} />
            <span className="mono-label" style={{ color: '#fde047', letterSpacing: '0.18em', fontSize: '10px' }}>
              ACT IV // ARENA ACCESS
            </span>
          </div>

          <h2 style={{ fontSize: '1.65rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '0.02em', margin: 0 }}>
            Team Access Portal
          </h2>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '4px', marginBottom: 0 }}>
            Enter authorized credentials to deploy into live arena
          </p>
        </div>

        {/* ── ACTIVE SESSION CARD (IF LOGGED IN AND NOT SWITCHING) ── */}
        {savedTeam && !showManualForm && !success && (
          <div
            style={{
              padding: '16px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, rgba(45, 212, 191, 0.12) 0%, rgba(15, 23, 42, 0.6) 100%)',
              border: '1px solid rgba(45, 212, 191, 0.40)',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
              boxShadow: '0 0 20px rgba(45, 212, 191, 0.10)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Shield size={16} color="#2dd4bf" />
                <span style={{ fontSize: '0.90rem', color: '#f8fafc', fontWeight: 700 }}>
                  Active Flight: <span style={{ color: '#2dd4bf' }}>{savedTeam}</span>
                </span>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '2px 6px',
                  borderRadius: '6px',
                }}
                onMouseOver={(e) => (e.currentTarget.style.color = '#ef4444')}
                onMouseOut={(e) => (e.currentTarget.style.color = '#94a3b8')}
              >
                <LogOut size={12} /> Log out
              </button>
            </div>

            {/* Target Arena Selector in Saved Session */}
            <div>
              <div className="mono-label" style={{ fontSize: '9px', color: '#cbd5e1', marginBottom: '6px' }}>
                TARGET ARENA
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setSelectedArena('/ui/main.html')}
                  style={{
                    padding: '8px 6px',
                    borderRadius: '10px',
                    border: selectedArena === '/ui/main.html' ? '1px solid #eab308' : '1px solid rgba(148, 163, 184, 0.2)',
                    background: selectedArena === '/ui/main.html' ? 'rgba(234, 179, 8, 0.2)' : 'rgba(15, 23, 42, 0.6)',
                    color: selectedArena === '/ui/main.html' ? '#fde047' : '#94a3b8',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px',
                    transition: 'all 0.2s',
                  }}
                >
                  <Target size={14} color={selectedArena === '/ui/main.html' ? '#fde047' : '#64748b'} />
                  <span>Main Arena</span>
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedArena('/ui/boost.html')}
                  style={{
                    padding: '8px 6px',
                    borderRadius: '10px',
                    border: selectedArena === '/ui/boost.html' ? '1px solid #06b6d4' : '1px solid rgba(148, 163, 184, 0.2)',
                    background: selectedArena === '/ui/boost.html' ? 'rgba(6, 182, 212, 0.2)' : 'rgba(15, 23, 42, 0.6)',
                    color: selectedArena === '/ui/boost.html' ? '#67e8f9' : '#94a3b8',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px',
                    transition: 'all 0.2s',
                  }}
                >
                  <Zap size={14} color={selectedArena === '/ui/boost.html' ? '#67e8f9' : '#64748b'} />
                  <span>Bonus Bidding</span>
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedArena('/ui/challenge.html')}
                  style={{
                    padding: '8px 6px',
                    borderRadius: '10px',
                    border: selectedArena === '/ui/challenge.html' ? '1px solid #a855f7' : '1px solid rgba(148, 163, 184, 0.2)',
                    background: selectedArena === '/ui/challenge.html' ? 'rgba(168, 85, 247, 0.2)' : 'rgba(15, 23, 42, 0.6)',
                    color: selectedArena === '/ui/challenge.html' ? '#c084fc' : '#94a3b8',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px',
                    transition: 'all 0.2s',
                  }}
                >
                  <Swords size={14} color={selectedArena === '/ui/challenge.html' ? '#c084fc' : '#64748b'} />
                  <span>Duel Arena</span>
                </button>
              </div>
            </div>

            <button
              type="button"
              onClick={handleContinueSaved}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '12px',
                background: 'linear-gradient(135deg, #0d9488, #14b8a6)',
                color: '#f8fafc',
                border: 'none',
                fontWeight: 700,
                fontSize: '0.88rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                boxShadow: '0 4px 18px rgba(20, 184, 166, 0.35)',
                transition: 'all 0.2s',
              }}
              onMouseOver={(e) => (e.currentTarget.style.filter = 'brightness(1.1)')}
              onMouseOut={(e) => (e.currentTarget.style.filter = 'none')}
            >
              <span>Continue Arena Deployment</span>
              <ArrowRight size={15} />
            </button>

            <button
              type="button"
              onClick={() => setShowManualForm(true)}
              style={{
                background: 'none',
                border: 'none',
                color: '#64748b',
                fontSize: '0.78rem',
                cursor: 'pointer',
                textAlign: 'center',
                textDecoration: 'underline',
              }}
            >
              Sign in with different credentials
            </button>
          </div>
        )}

        {/* ── ALERTS ── */}
        {error && (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '12px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.45)',
              color: '#fca5a5',
              fontSize: '0.82rem',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <AlertCircle size={15} color="#ef4444" style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '12px',
              background: 'rgba(34, 197, 94, 0.15)',
              border: '1px solid rgba(34, 197, 94, 0.45)',
              color: '#86efac',
              fontSize: '0.84rem',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <CheckCircle2 size={16} color="#22c55e" style={{ flexShrink: 0 }} />
            <span>Authenticated! Initializing arena flight...</span>
          </div>
        )}

        {/* ── LOGIN CREDENTIALS FORM ── */}
        {(!savedTeam || showManualForm) && (
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* Team Callsign Input */}
            <div>
              <label
                htmlFor="mpl-team-name"
                className="mono-label"
                style={{ display: 'block', marginBottom: '6px', fontSize: '9px', color: '#cbd5e1' }}
              >
                TEAM CALLSIGN
              </label>
              <div style={{ position: 'relative' }}>
                <div style={{ position: 'absolute', left: '13px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }}>
                  <Shield size={15} />
                </div>
                <input
                  id="mpl-team-name"
                  type="text"
                  value={teamName}
                  onChange={(e) => setTeamName(e.target.value)}
                  placeholder="Enter assigned team callsign"
                  autoComplete="off"
                  disabled={loading || success}
                  style={{
                    width: '100%',
                    padding: '11px 14px 11px 40px',
                    borderRadius: '12px',
                    background: 'rgba(15, 23, 42, 0.80)',
                    border: '1px solid rgba(148, 163, 184, 0.25)',
                    color: '#f8fafc',
                    fontSize: '0.90rem',
                    outline: 'none',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                    boxSizing: 'border-box',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#eab308';
                    e.target.style.boxShadow = '0 0 12px rgba(234, 179, 8, 0.25)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = 'rgba(148, 163, 184, 0.25)';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              </div>
            </div>

            {/* Passcode Input */}
            <div>
              <label
                htmlFor="mpl-passcode"
                className="mono-label"
                style={{ display: 'block', marginBottom: '6px', fontSize: '9px', color: '#cbd5e1' }}
              >
                TEAM PASSCODE
              </label>
              <div style={{ position: 'relative' }}>
                <div style={{ position: 'absolute', left: '13px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }}>
                  <Key size={15} />
                </div>
                <input
                  id="mpl-passcode"
                  type={showPassword ? 'text' : 'password'}
                  value={passcode}
                  onChange={(e) => setPasscode(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading || success}
                  style={{
                    width: '100%',
                    padding: '11px 38px 11px 40px',
                    borderRadius: '12px',
                    background: 'rgba(15, 23, 42, 0.80)',
                    border: '1px solid rgba(148, 163, 184, 0.25)',
                    color: '#f8fafc',
                    fontSize: '0.90rem',
                    outline: 'none',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                    boxSizing: 'border-box',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#eab308';
                    e.target.style.boxShadow = '0 0 12px rgba(234, 179, 8, 0.25)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = 'rgba(148, 163, 184, 0.25)';
                    e.target.style.boxShadow = 'none';
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                  style={{
                    position: 'absolute',
                    right: '11px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    color: '#64748b',
                    cursor: 'pointer',
                    padding: '4px',
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            {/* Arena Destination Selector */}
            <div>
              <label className="mono-label" style={{ display: 'block', marginBottom: '6px', fontSize: '9px', color: '#cbd5e1' }}>
                TARGET ARENA
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setSelectedArena('/ui/main.html')}
                  style={{
                    padding: '8px 6px',
                    borderRadius: '10px',
                    border: selectedArena === '/ui/main.html' ? '1px solid #eab308' : '1px solid rgba(148, 163, 184, 0.18)',
                    background: selectedArena === '/ui/main.html' ? 'rgba(234, 179, 8, 0.18)' : 'rgba(15, 23, 42, 0.55)',
                    color: selectedArena === '/ui/main.html' ? '#fde047' : '#94a3b8',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px',
                    transition: 'all 0.2s',
                  }}
                >
                  <Target size={14} color={selectedArena === '/ui/main.html' ? '#fde047' : '#64748b'} />
                  <span>Main Arena</span>
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedArena('/ui/boost.html')}
                  style={{
                    padding: '8px 6px',
                    borderRadius: '10px',
                    border: selectedArena === '/ui/boost.html' ? '1px solid #06b6d4' : '1px solid rgba(148, 163, 184, 0.18)',
                    background: selectedArena === '/ui/boost.html' ? 'rgba(6, 182, 212, 0.18)' : 'rgba(15, 23, 42, 0.55)',
                    color: selectedArena === '/ui/boost.html' ? '#67e8f9' : '#94a3b8',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px',
                    transition: 'all 0.2s',
                  }}
                >
                  <Zap size={14} color={selectedArena === '/ui/boost.html' ? '#67e8f9' : '#64748b'} />
                  <span>Bonus Bidding</span>
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedArena('/ui/challenge.html')}
                  style={{
                    padding: '8px 6px',
                    borderRadius: '10px',
                    border: selectedArena === '/ui/challenge.html' ? '1px solid #a855f7' : '1px solid rgba(148, 163, 184, 0.18)',
                    background: selectedArena === '/ui/challenge.html' ? 'rgba(168, 85, 247, 0.18)' : 'rgba(15, 23, 42, 0.55)',
                    color: selectedArena === '/ui/challenge.html' ? '#c084fc' : '#94a3b8',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '4px',
                    transition: 'all 0.2s',
                  }}
                >
                  <Swords size={14} color={selectedArena === '/ui/challenge.html' ? '#c084fc' : '#64748b'} />
                  <span>Duel Arena</span>
                </button>
              </div>
            </div>

            {/* Submit Hero Button */}
            <button
              type="submit"
              disabled={loading || success}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '12px',
                background: 'linear-gradient(135deg, #f59e0b 0%, #eab308 50%, #ca8a04 100%)',
                color: '#060913',
                border: 'none',
                fontWeight: 800,
                fontSize: '0.88rem',
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                cursor: loading || success ? 'default' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                boxShadow: '0 4px 22px rgba(234, 179, 8, 0.45)',
                marginTop: '4px',
                transition: 'transform 0.2s, box-shadow 0.2s, filter 0.2s',
              }}
              onMouseOver={(e) => {
                if (!loading && !success) {
                  e.currentTarget.style.transform = 'translateY(-1px)';
                  e.currentTarget.style.boxShadow = '0 6px 28px rgba(234, 179, 8, 0.6)';
                }
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 22px rgba(234, 179, 8, 0.45)';
              }}
            >
              {loading ? (
                <span>Authenticating Credentials...</span>
              ) : success ? (
                <span>Authenticated!</span>
              ) : (
                <>
                  <span>Enter Arena</span>
                  <ArrowRight size={15} />
                </>
              )}
            </button>
          </form>
        )}

        {/* ── FOOTER LINK ── */}
        <div style={{ textAlign: 'center', borderTop: '1px solid rgba(148, 163, 184, 0.12)', paddingTop: '12px' }}>
          <a
            href="/ui/admin.html"
            style={{
              fontSize: '0.78rem',
              color: '#64748b',
              textDecoration: 'none',
              transition: 'color 0.2s',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = '#eab308')}
            onMouseOut={(e) => (e.currentTarget.style.color = '#64748b')}
          >
            Organizers & Judges // Admin Gateway →
          </a>
        </div>
      </div>
    </div>
  );
};


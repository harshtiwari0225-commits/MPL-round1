import React, { useState, useEffect } from 'react';
import { Shield, Key, ArrowRight, AlertCircle, CheckCircle2, Target, Zap, Swords, Eye, EyeOff, LogOut } from 'lucide-react';

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

  // Active session detection
  const [savedTeam, setSavedTeam] = useState<string | null>(null);

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

      // Store in sessionStorage for all 3 arena modules (Main, Boost, Challenge)
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
        padding: '20px',
        opacity: 0,
        pointerEvents: 'none',
        transform: 'translateY(30px)',
      }}
    >
      <div
        className="glass-panel-gold"
        style={{
          width: '100%',
          maxWidth: '480px',
          borderRadius: '24px',
          padding: '36px 32px',
          background: 'rgba(11, 15, 32, 0.90)',
          backdropFilter: 'blur(28px)',
          border: '1px solid rgba(234, 179, 8, 0.40)',
          boxShadow: '0 30px 70px -15px rgba(0, 0, 0, 0.9), 0 0 50px rgba(234, 179, 8, 0.18)',
          pointerEvents: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '22px',
        }}
      >
        {/* Header with mini logo */}
        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div
            style={{
              width: '60px',
              height: '60px',
              borderRadius: '16px',
              background: 'rgba(234, 179, 8, 0.1)',
              border: '1px solid rgba(234, 179, 8, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '10px',
            }}
          >
            <img
              src="/mpl_logo.png"
              alt="MPL Logo"
              style={{ width: '44px', height: '44px', objectFit: 'contain' }}
            />
          </div>
          <span className="mono-label" style={{ color: '#fde047', letterSpacing: '0.2em', fontSize: '11px' }}>
            ACT IV // ARENA GATEWAY
          </span>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', marginTop: '2px' }}>
            Team Access Portal
          </h2>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '3px' }}>
            Enter team credentials to initialize synchronized arena flight
          </p>
        </div>

        {/* Existing Logged-in Session Banner */}
        {savedTeam && !success && (
          <div
            style={{
              padding: '12px 16px',
              borderRadius: '14px',
              background: 'rgba(45, 212, 191, 0.10)',
              border: '1px solid rgba(45, 212, 191, 0.35)',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#2dd4bf', boxShadow: '0 0 8px #2dd4bf' }} />
                <span style={{ fontSize: '0.85rem', color: '#f8fafc', fontWeight: 600 }}>
                  Active Session: <span style={{ color: '#2dd4bf' }}>{savedTeam}</span>
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
                }}
              >
                <LogOut size={12} /> Log out
              </button>
            </div>
            <button
              type="button"
              onClick={handleContinueSaved}
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #0d9488, #14b8a6)',
                color: '#f8fafc',
                border: 'none',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                boxShadow: '0 4px 14px rgba(20, 184, 166, 0.3)',
              }}
            >
              Continue to Selected Arena <ArrowRight size={14} />
            </button>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div
            style={{
              padding: '11px 15px',
              borderRadius: '12px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              color: '#fca5a5',
              fontSize: '0.82rem',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <AlertCircle size={16} color="#ef4444" style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Success Alert */}
        {success && (
          <div
            style={{
              padding: '11px 15px',
              borderRadius: '12px',
              background: 'rgba(34, 197, 94, 0.15)',
              border: '1px solid rgba(34, 197, 94, 0.4)',
              color: '#86efac',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <CheckCircle2 size={16} color="#22c55e" style={{ flexShrink: 0 }} />
            <span>Authenticated! Entering arena corridor...</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {/* Team Name Input */}
          <div>
            <label
              htmlFor="mpl-team-name"
              className="mono-label"
              style={{ display: 'block', marginBottom: '6px', fontSize: '10px', color: '#cbd5e1' }}
            >
              TEAM IDENTIFIER
            </label>
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }}>
                <Shield size={16} />
              </div>
              <input
                id="mpl-team-name"
                type="text"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                placeholder="e.g. Team Alpha"
                autoComplete="off"
                disabled={loading || success}
                style={{
                  width: '100%',
                  padding: '12px 14px 12px 42px',
                  borderRadius: '12px',
                  background: 'rgba(15, 23, 42, 0.75)',
                  border: '1px solid rgba(148, 163, 184, 0.25)',
                  color: '#f8fafc',
                  fontSize: '0.92rem',
                  outline: 'none',
                  transition: 'border-color 0.2s, box-shadow 0.2s',
                  boxSizing: 'border-box',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#eab308')}
                onBlur={(e) => (e.target.style.borderColor = 'rgba(148, 163, 184, 0.25)')}
              />
            </div>
          </div>

          {/* Passcode Input */}
          <div>
            <label
              htmlFor="mpl-passcode"
              className="mono-label"
              style={{ display: 'block', marginBottom: '6px', fontSize: '10px', color: '#cbd5e1' }}
            >
              TEAM PASSCODE
            </label>
            <div style={{ position: 'relative' }}>
              <div style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }}>
                <Key size={16} />
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
                  padding: '12px 42px 12px 42px',
                  borderRadius: '12px',
                  background: 'rgba(15, 23, 42, 0.75)',
                  border: '1px solid rgba(148, 163, 184, 0.25)',
                  color: '#f8fafc',
                  fontSize: '0.92rem',
                  outline: 'none',
                  transition: 'border-color 0.2s, box-shadow 0.2s',
                  boxSizing: 'border-box',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#eab308')}
                onBlur={(e) => (e.target.style.borderColor = 'rgba(148, 163, 184, 0.25)')}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                style={{
                  position: 'absolute',
                  right: '12px',
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
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Arena Destination Selector */}
          <div>
            <label className="mono-label" style={{ display: 'block', marginBottom: '6px', fontSize: '10px', color: '#cbd5e1' }}>
              TARGET ARENA
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
              <button
                type="button"
                onClick={() => setSelectedArena('/ui/main.html')}
                style={{
                  padding: '10px 8px',
                  borderRadius: '10px',
                  border: selectedArena === '/ui/main.html' ? '1px solid #eab308' : '1px solid rgba(148, 163, 184, 0.15)',
                  background: selectedArena === '/ui/main.html' ? 'rgba(234, 179, 8, 0.15)' : 'rgba(15, 23, 42, 0.5)',
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
                  padding: '10px 8px',
                  borderRadius: '10px',
                  border: selectedArena === '/ui/boost.html' ? '1px solid #06b6d4' : '1px solid rgba(148, 163, 184, 0.15)',
                  background: selectedArena === '/ui/boost.html' ? 'rgba(6, 182, 212, 0.15)' : 'rgba(15, 23, 42, 0.5)',
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
                  padding: '10px 8px',
                  borderRadius: '10px',
                  border: selectedArena === '/ui/challenge.html' ? '1px solid #a855f7' : '1px solid rgba(148, 163, 184, 0.15)',
                  background: selectedArena === '/ui/challenge.html' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(15, 23, 42, 0.5)',
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

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || success}
            style={{
              width: '100%',
              padding: '13px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #eab308, #ca8a04)',
              color: '#070913',
              border: 'none',
              fontWeight: 800,
              fontSize: '0.92rem',
              letterSpacing: '0.05em',
              textTransform: 'uppercase',
              cursor: loading || success ? 'default' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              boxShadow: '0 4px 20px rgba(234, 179, 8, 0.4)',
              marginTop: '4px',
              transition: 'transform 0.2s, box-shadow 0.2s',
            }}
          >
            {loading ? (
              <span>Authenticating Session...</span>
            ) : success ? (
              <span>Authenticated!</span>
            ) : (
              <>
                <span>Enter Arena</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* Organizer link */}
        <div style={{ textAlign: 'center', borderTop: '1px solid rgba(148, 163, 184, 0.12)', paddingTop: '14px' }}>
          <a
            href="/ui/admin.html"
            style={{
              fontSize: '0.80rem',
              color: '#64748b',
              textDecoration: 'none',
              transition: 'color 0.2s',
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = '#eab308')}
            onMouseOut={(e) => (e.currentTarget.style.color = '#64748b')}
          >
            Organizers & Judges // Admin Control Panel →
          </a>
        </div>
      </div>
    </div>
  );
};

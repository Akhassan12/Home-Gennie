import { Sparkles, Github, Mail } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer style={{ borderTop: '1px solid rgba(255,255,255,0.05)', background: 'rgba(13,17,23,0.9)' }}>
      <div className="section-container" style={{ paddingTop: '3rem', paddingBottom: '3rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '2.5rem', marginBottom: '2.5rem' }}>
          {/* Brand */}
          <div>
            <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', textDecoration: 'none', marginBottom: '0.75rem' }}>
              <div style={{
                width: '2rem', height: '2rem', borderRadius: '8px',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }} className="gradient-bg">
                <Sparkles size={14} style={{ color: '#fff' }} />
              </div>
              <span style={{ fontFamily: 'var(--font-display)', fontWeight: '700', color: '#fff' }}>
                Home <span style={{ color: '#748ffc' }}>Gennie</span>
              </span>
            </Link>
            <p style={{ fontSize: '0.82rem', color: '#495057', lineHeight: '1.6', maxWidth: '260px' }}>
              Transform your living spaces with AI-powered design suggestions and immersive AR visualization.
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 style={{ fontSize: '0.82rem', fontWeight: '600', color: '#dee2e6', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Platform</h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {[
                { label: 'Dashboard', to: '/dashboard' },
                { label: 'Upload', to: '/upload' },
                { label: 'Gallery', to: '/gallery' },
                { label: '3D Viewer', to: '/viewer' },
              ].map((item) => (
                <li key={item.label} style={{ marginBottom: '0.5rem' }}>
                  <Link to={item.to} style={{ fontSize: '0.82rem', color: '#495057', textDecoration: 'none', transition: 'color 0.2s' }}
                    onMouseEnter={(e) => e.target.style.color = '#748ffc'}
                    onMouseLeave={(e) => e.target.style.color = '#495057'}>
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Connect */}
          <div>
            <h4 style={{ fontSize: '0.82rem', fontWeight: '600', color: '#dee2e6', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Connect</h4>
            <div style={{ display: 'flex', gap: '0.6rem' }}>
              {[Github, Mail].map((Icon, i) => (
                <a key={i} href="#" style={{
                  width: '2.2rem', height: '2.2rem', borderRadius: '8px',
                  background: 'rgba(255,255,255,0.05)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', color: '#495057',
                  transition: 'all 0.2s', textDecoration: 'none'
                }}
                onMouseEnter={(e) => { e.currentTarget.style.color = '#748ffc'; e.currentTarget.style.background = 'rgba(255,255,255,0.1)' }}
                onMouseLeave={(e) => { e.currentTarget.style.color = '#495057'; e.currentTarget.style.background = 'rgba(255,255,255,0.05)' }}>
                  <Icon size={15} />
                </a>
              ))}
            </div>
          </div>
        </div>

        <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '1.5rem', textAlign: 'center' }}>
          <p style={{ fontSize: '0.75rem', color: '#495057' }}>
            © {new Date().getFullYear()} Home Gennie. AI-Enhanced Interior Design with Augmented Reality.
          </p>
        </div>
      </div>
    </footer>
  )
}

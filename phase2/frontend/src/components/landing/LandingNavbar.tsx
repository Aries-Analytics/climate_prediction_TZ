import { useState, useEffect } from 'react'

const NAV_LINKS = [
  { label: 'About', href: '#about' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Features', href: '#features' },
]

export default function LandingNavbar() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  return (
    <nav
      className={`fixed top-0 w-full z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-[#0a1628]/95 backdrop-blur-md border-b border-teal-600/20 shadow-lg shadow-black/20'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-28">
          {/* Logo */}
          <a href="/" className="flex items-center group">
            <img
              src="/hewasense-logo.png"
              alt="HewaSense"
              className="h-24 transition-transform duration-200 group-hover:scale-105"
              onError={(e) => {
                const target = e.currentTarget
                target.style.display = 'none'
                const fallback = target.nextElementSibling as HTMLElement | null
                if (fallback) fallback.style.display = 'flex'
              }}
            />
            {/* Fallback if image fails */}
            <span className="hidden items-center gap-2">
              <span className="w-9 h-9 rounded-lg bg-gradient-to-br from-teal-500 to-cyan-400 flex items-center justify-center text-[#0a1628] font-bold text-sm">
                HS
              </span>
              <span className="text-white font-bold text-lg tracking-tight">
                Hewa<span className="text-teal-400">Sense</span>
              </span>
            </span>
          </a>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map(({ label, href }) => (
              <a
                key={label}
                href={href}
                className="text-slate-300 hover:text-teal-400 transition-colors text-sm font-medium"
              >
                {label}
              </a>
            ))}
          </div>


        </div>
      </div>
    </nav>
  )
}

const NAV_LINKS = [
  { label: 'About',        href: '#about' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Features',     href: '#features' },
]

export default function LandingFooter() {
  return (
    <footer className="bg-[#040d1a] border-t border-teal-600/10 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">

          {/* Brand */}
          <div className="flex items-center gap-2">
            <img
              src="/hewasense-logo.svg"
              alt="HewaSense"
              className="h-7 w-7"
              onError={(e) => { e.currentTarget.style.display = 'none' }}
            />
            <span className="text-white font-bold">
              Hewa<span className="text-teal-400">Sense</span>
            </span>
          </div>

          {/* Nav links */}
          <div className="flex items-center gap-6 text-sm text-slate-500">
            {NAV_LINKS.map(({ label, href }) => (
              <a key={label} href={href} className="hover:text-teal-400 transition-colors">
                {label}
              </a>
            ))}
          </div>

          {/* Copyright */}
          <p className="text-slate-600 text-xs text-center">
            © 2025 HewaSense · Tanzania Climate Parametric Insurance
          </p>

        </div>
      </div>
    </footer>
  )
}

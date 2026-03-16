import { ArrowRight, ChevronDown } from 'lucide-react'

// Deterministic positions for constellation dots (avoids random re-renders)
const DOTS = [
  { top: '25%', left: '88%', delay: '0.4s' },
  { top: '45%', left: '5%',  delay: '0.8s' },
  { top: '60%', left: '92%', delay: '1.2s' },
  { top: '75%', left: '12%', delay: '1.6s' },
  { top: '20%', left: '72%', delay: '0.2s' },
  { top: '55%', left: '78%', delay: '0.6s' },
  { top: '80%', left: '85%', delay: '1.0s' },
  { top: '35%', left: '95%', delay: '1.4s' },
  { top: '65%', left: '3%',  delay: '1.8s' },
  { top: '88%', left: '45%', delay: '0.9s' },
]

export default function HeroSection() {

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#040d1a] via-[#0a1628] to-[#0f2040]" />

      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(13,148,136,0.6) 1px, transparent 1px),
            linear-gradient(90deg, rgba(13,148,136,0.6) 1px, transparent 1px)
          `,
          backgroundSize: '64px 64px',
        }}
      />

      {/* Constellation dots — amber accent matching logo */}
      {DOTS.map((dot, i) => (
        <div
          key={i}
          className="absolute w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse-slow opacity-50"
          style={{ top: dot.top, left: dot.left, animationDelay: dot.delay }}
        />
      ))}

      {/* Content */}
      <div className="relative z-10 text-center max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 sm:pt-24 lg:pt-32">
        {/* Pill badge */}
        <div className="inline-flex items-center gap-2 bg-teal-600/20 border border-teal-500/40 rounded-full px-3 py-1 sm:px-4 sm:py-1.5 mb-6 sm:mb-8 animate-fade-in-up">
          <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse flex-shrink-0" />
          <span className="text-teal-300 text-xs sm:text-sm font-medium whitespace-nowrap">
            HewaSense · Tanzania Pilot · Kilombero Basin
          </span>
        </div>

        {/* Headline */}
        <h1 className="text-4xl sm:text-5xl lg:text-7xl font-extrabold text-white leading-[1.1] mb-6 animate-fade-in-up tracking-tight">
          AI-Powered{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-cyan-400">
            Parametric Insurance
          </span>
          <br />for Tanzania Farmers
        </h1>

        {/* Sub-headline */}
        <p className="text-slate-300 text-lg sm:text-xl max-w-3xl mx-auto mb-10 leading-relaxed animate-fade-in-up">
          Built for smallholder farmers in Tanzania's Kilombero Basin. When a climate
          trigger is breached, payouts are automatically calculated by formula —
          no loss adjuster, no claim filing, no delay.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center animate-fade-in-up">
          <button
            onClick={() => window.open('/login', '_blank', 'noopener,noreferrer')}
            className="flex items-center gap-2 bg-teal-600 hover:bg-teal-500 text-white px-8 py-3.5 rounded-xl font-semibold text-base transition-all duration-200 hover:scale-105 hover:shadow-xl hover:shadow-teal-500/25"
          >
            Access Dashboard
            <ArrowRight className="w-5 h-5" />
          </button>
          <a
            href="#how-it-works"
            className="flex items-center gap-2 text-slate-300 hover:text-teal-400 transition-colors font-medium text-base"
          >
            See How It Works
            <ChevronDown className="w-4 h-4" />
          </a>
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <ChevronDown className="w-6 h-6 text-teal-400/60" />
      </div>
    </section>
  )
}

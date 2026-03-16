import { BarChart3, Shield, FileText, Activity, CloudRain, Coins } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface Feature {
  icon: LucideIcon
  title: string
  description: string
  badge: string
}

const FEATURES: Feature[] = [
  {
    icon: BarChart3,
    title: 'ML Forecasting',
    description:
      'Probabilistic forecasts for drought, flood, and crop failure — issued ahead of the season with confidence metrics, so insurers and agronomists can become proactive, not reactive.',
    badge: 'Model Performance',
  },
  {
    icon: Shield,
    title: 'Parametric Triggers',
    description:
      'Independently verifiable strike thresholds for drought, flood, and crop failure — calibrated against historical climate data so trigger frequency is actuarially sound and commercially viable.',
    badge: 'Trigger Events',
  },
  {
    icon: FileText,
    title: 'Evidence Packs',
    description:
      'For every trigger event, the platform auto-generates a structured evidence report — documenting the forecast, the threshold breach, and the basis for payout. Ready to download for regulatory review or stakeholder reporting.',
    badge: 'Evidence Pack',
  },
  {
    icon: Activity,
    title: 'Real-time Monitoring',
    description:
      'Executive snapshot KPIs, live trigger alerts, and portfolio loss ratio tracking in a role-based dashboard interface.',
    badge: 'Executive',
  },
  {
    icon: CloudRain,
    title: 'Multi-peril Coverage',
    description:
      'Simultaneous drought (SPI), flood (precipitation exceedance), and crop failure (NDVI composite index) peril monitoring.',
    badge: 'Climate Insights',
  },
  {
    icon: Coins,
    title: 'Payout Analytics',
    description:
      'Track cumulative payout exposure, loss ratios, and per-peril trigger frequency across the active policy portfolio with season-over-season comparison.',
    badge: 'Analytics',
  },
]

export default function FeaturesSection() {
  return (
    <section id="features" className="py-24 bg-[#040d1a]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <span className="text-teal-400 text-sm font-semibold uppercase tracking-widest">Platform</span>
          <h2 className="mt-2 text-3xl sm:text-4xl font-bold text-white">Everything You Need</h2>
          <p className="mt-4 text-slate-400 max-w-2xl mx-auto">
            Six integrated modules built for climate insurance professionals.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map(({ icon: Icon, title, description, badge }) => (
            <div
              key={title}
              className="group bg-[#0a1628] border border-teal-600/20 rounded-2xl p-6 hover:border-teal-500/40 hover:bg-[#0f2040] transition-all duration-300"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-10 h-10 rounded-lg bg-teal-600/20 group-hover:bg-teal-600/30 flex items-center justify-center transition-colors flex-shrink-0">
                  <Icon className="w-5 h-5 text-teal-400" />
                </div>
                <span className="text-xs font-medium text-teal-500 bg-teal-500/10 px-2 py-0.5 rounded-full border border-teal-500/20 ml-2">
                  {badge}
                </span>
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">{title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

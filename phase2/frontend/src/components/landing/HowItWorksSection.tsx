import { CloudDownload, Brain, Zap, DollarSign } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface Step {
  step: string
  icon: LucideIcon
  title: string
  description: string
  gradient: string
  isLast?: boolean
}

const STEPS: Step[] = [
  {
    step: '01',
    icon: CloudDownload,
    title: 'Ingest Climate Data',
    description:
      'ERA5 reanalysis, CHIRPS precipitation, and Google Earth Engine satellite data are ingested daily via the automated pipeline at 6 AM EAT.',
    gradient: 'from-cyan-500 to-teal-500',
  },
  {
    step: '02',
    icon: Brain,
    title: 'ML Forecast Engine',
    description:
      'The forecast engine produces probabilistic risk assessments for drought, flood, and crop failure — each with confidence metrics that quantify model certainty before a trigger decision is made.',
    gradient: 'from-teal-500 to-teal-600',
  },
  {
    step: '03',
    icon: Zap,
    title: 'Parametric Trigger',
    description:
      'When forecast probability exceeds the agreed strike threshold for a given peril and location, a trigger event is logged with full evidence traceability.',
    gradient: 'from-teal-600 to-amber-500',
  },
  {
    step: '04',
    icon: DollarSign,
    title: 'Automated Payout',
    description:
      'The payout amount is calculated by formula based on the breach magnitude — farmer receives funds directly, with no claim filing, no loss adjuster, and no delay.',
    gradient: 'from-amber-500 to-amber-400',
    isLast: true,
  },
]

export default function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-24 bg-[#0a1628]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <span className="text-teal-400 text-sm font-semibold uppercase tracking-widest">Process</span>
          <h2 className="mt-2 text-3xl sm:text-4xl font-bold text-white">How It Works</h2>
          <p className="mt-4 text-slate-400 max-w-2xl mx-auto">
            From raw satellite data to farmer payout in four automated steps.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {STEPS.map(({ step, icon: Icon, title, description, gradient, isLast }) => (
            <div
              key={step}
              className="relative bg-[#0f2040] border border-teal-600/20 rounded-2xl p-6 hover:border-teal-500/50 transition-all duration-300 hover:-translate-y-1"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${gradient} flex items-center justify-center flex-shrink-0`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <span className="text-slate-600 font-mono font-bold text-lg">{step}</span>
              </div>
              <h3 className="text-white font-semibold text-lg mb-2">{title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{description}</p>

              {/* Connector line between cards on large screens */}
              {!isLast && (
                <div className="hidden lg:block absolute -right-3 top-1/2 -translate-y-1/2 z-10">
                  <div className="w-6 h-px bg-teal-600/40" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

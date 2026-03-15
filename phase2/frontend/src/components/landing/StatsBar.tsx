import { Users, Database, TrendingUp, Award } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface Stat {
  icon: LucideIcon
  value: string
  label: string
  sublabel: string
}

const STATS: Stat[] = [
  { icon: Users,      value: '1,000+', label: 'Smallholder Farmers', sublabel: 'Kilombero Basin pilot' },
  { icon: Database,   value: '25 yrs', label: 'Climate Data',        sublabel: 'ERA5 + CHIRPS reanalysis' },
  { icon: TrendingUp, value: '12',     label: 'Forecast Horizons',   sublabel: 'Monthly probability runs' },
  { icon: Award,      value: '86.7%',  label: 'Model R² Score',      sublabel: 'XGBoost primary model' },
]

export default function StatsBar() {
  return (
    <section className="bg-[#0f2040]/80 border-y border-teal-600/20 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
          {STATS.map(({ icon: Icon, value, label, sublabel }) => (
            <div key={label} className="text-center">
              <div className="flex justify-center mb-3">
                <div className="w-10 h-10 rounded-lg bg-teal-600/20 flex items-center justify-center">
                  <Icon className="w-5 h-5 text-teal-400" />
                </div>
              </div>
              <div className="text-3xl font-bold text-white mb-1">{value}</div>
              <div className="text-teal-300 font-medium text-sm mb-0.5">{label}</div>
              <div className="text-slate-500 text-xs">{sublabel}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

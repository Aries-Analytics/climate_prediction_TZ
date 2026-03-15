import { ArrowRight, BarChart2 } from 'lucide-react'

export default function AccessCTASection() {
  return (
    <section className="py-24 bg-gradient-to-b from-[#040d1a] to-[#0a1628]">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="bg-gradient-to-br from-teal-600/20 to-cyan-600/10 border border-teal-500/30 rounded-3xl p-12">
          <div className="w-14 h-14 rounded-2xl bg-teal-600/30 flex items-center justify-center mx-auto mb-6">
            <BarChart2 className="w-7 h-7 text-teal-400" />
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Your Crop Risk. Quantified. In Real Time.
          </h2>
          <p className="text-slate-400 text-lg mb-8 leading-relaxed">
            Track drought and flood risk probability in the Kilombero Basin,
            monitor whether payout triggers have been breached this season, and download
            auto-generated evidence packs — all from one dashboard built for
            insurers, agronomists, and regulators who need answers, not guesswork.
          </p>
          <button
            onClick={() => window.open('/login', '_blank', 'noopener,noreferrer')}
            className="inline-flex items-center gap-3 bg-teal-600 hover:bg-teal-500 text-white px-8 py-4 rounded-xl font-semibold text-base transition-all duration-200 hover:scale-105 hover:shadow-xl hover:shadow-teal-500/30"
          >
            Access Dashboard
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </section>
  )
}

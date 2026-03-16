import { MapPin, Users, Leaf } from 'lucide-react'

const SPECS = [
  { label: 'Primary Peril',       value: 'Drought (SPI-based)' },
  { label: 'Secondary Peril',     value: 'Flood (Precipitation exceedance)' },
  { label: 'Tertiary Peril',      value: 'Crop Failure (NDVI composite)' },
  { label: 'Regulatory Framework',value: 'TIRA (Tanzania)' },
  { label: 'Forecast Engine',     value: 'XGBoost (probabilistic)' },
  { label: 'Data Sources',        value: 'ERA5, CHIRPS, GEE' },
]

const HIGHLIGHTS = [
  { icon: MapPin,  text: 'Kilombero Basin, Morogoro Region, Tanzania' },
  { icon: Users,   text: '1,000 rice farmers in initial pilot coverage area' },
  { icon: Leaf,    text: 'Rice crop calendar aligned trigger seasons' },
]

export default function AboutSection() {
  return (
    <section id="about" className="py-24 bg-[#0a1628]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

          {/* Text column */}
          <div>
            <span className="text-teal-400 text-sm font-semibold uppercase tracking-widest">Mission</span>
            <h2 className="mt-2 text-3xl sm:text-4xl font-bold text-white mb-6">
              Built for Tanzania's<br />Smallholder Farmers
            </h2>
            <p className="text-slate-400 leading-relaxed mb-6">
              HewaSense applies machine learning to one of sub-Saharan Africa's most pressing
              challenges: giving smallholder farmers financial protection against the climate
              events that devastate their crops and livelihoods.
            </p>
            <p className="text-slate-400 leading-relaxed mb-8">
              The pilot focuses on the Kilombero Basin, Morogoro Region — a high-value
              rice-growing area with high climate variability and minimal insurance penetration.
              Our models are trained on 25 years of ERA5 reanalysis data combined with
              CHIRPS precipitation and Google Earth Engine NDVI indices.
            </p>

            <div className="space-y-3">
              {HIGHLIGHTS.map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-center gap-3 text-slate-300 text-sm">
                  <Icon className="w-4 h-4 text-teal-400 flex-shrink-0" />
                  {text}
                </div>
              ))}
            </div>
          </div>

          {/* Spec table column */}
          <div className="bg-[#0f2040] border border-teal-600/20 rounded-2xl p-8">
            <div className="text-center mb-6">
              <div className="inline-block bg-teal-600/20 rounded-xl px-4 py-2 text-teal-300 text-sm font-medium">
                HewaSense Pilot 2025–2026
              </div>
            </div>
            <div className="space-y-0">
              {SPECS.map(({ label, value }) => (
                <div
                  key={label}
                  className="flex items-center justify-between py-3 border-b border-teal-600/10 last:border-0"
                >
                  <span className="text-slate-400 text-sm">{label}</span>
                  <span className="text-teal-300 text-sm font-medium text-right ml-4">{value}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}

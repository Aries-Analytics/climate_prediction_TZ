import LandingNavbar from '../components/landing/LandingNavbar'
import HeroSection from '../components/landing/HeroSection'
import StatsBar from '../components/landing/StatsBar'
import HowItWorksSection from '../components/landing/HowItWorksSection'
import FeaturesSection from '../components/landing/FeaturesSection'
import AboutSection from '../components/landing/AboutSection'
import AccessCTASection from '../components/landing/AccessCTASection'
import LandingFooter from '../components/landing/LandingFooter'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a1628] text-white" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
      <LandingNavbar />
      <main>
        <HeroSection />
        <StatsBar />
        <HowItWorksSection />
        <FeaturesSection />
        <AboutSection />
        <AccessCTASection />
      </main>
      <LandingFooter />
    </div>
  )
}

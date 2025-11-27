import { LandingHero } from "@/components/landing/LandingHero";
import { LandingFeatures } from "@/components/landing/LandingFeatures";
import { LandingAI } from "@/components/landing/LandingAI";
import { LandingPerformance } from "@/components/landing/LandingPerformance";
import { LandingCTA } from "@/components/landing/LandingCTA";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { ThemeToggle } from "@/components/landing/ThemeToggle";

export default function LandingPage() {
  return (
    <ThemeProvider>
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 transition-colors duration-300">
        <ThemeToggle />
        <LandingHero />
        <LandingFeatures />
        <LandingAI />
        <LandingPerformance />
        <LandingCTA />
        <LandingFooter />
      </div>
    </ThemeProvider>
  );
}

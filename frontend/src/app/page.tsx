import Link from "next/link";
import { ArrowRight, Calendar, Database, Sparkles } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-black text-white selection:bg-white/30 font-sans">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-white/10 bg-black/50 backdrop-blur-md">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-white flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-black" />
            </div>
            <span className="font-bold text-xl tracking-tight">HeliX</span>
          </div>
          <nav>
            <Link
              href="/auth/login"
              className="px-4 py-2 text-sm font-medium border border-white/20 rounded-md hover:bg-white hover:text-black transition-colors"
            >
              Log in
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-6 pt-32 pb-24 text-center">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight max-w-4xl mx-auto mb-8 bg-gradient-to-br from-white to-white/40 bg-clip-text text-transparent">
          The Autonomous Multi-Agent Fitness Orchestrator
        </h1>
        <p className="text-lg md:text-xl text-white/50 max-w-2xl mx-auto mb-12">
          Your personal AI coaching team that adapts in real-time. HeliX
          orchestrates specialists to manage your fatigue, schedule, and progress.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link
            href="/auth/login"
            className="px-6 py-3 bg-white text-black font-semibold rounded-md flex items-center gap-2 hover:bg-white/90 transition-colors"
          >
            Start your journey <ArrowRight className="w-4 h-4" />
          </Link>
          <a
            href="#features"
            className="px-6 py-3 border border-white/20 rounded-md font-semibold hover:bg-white/5 transition-colors"
          >
            Learn more
          </a>
        </div>
      </main>

      {/* Features Grid */}
      <section id="features" className="container mx-auto px-6 py-24 border-t border-white/10">
        <div className="grid md:grid-cols-3 gap-8">
          <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02]">
            <Sparkles className="w-8 h-8 mb-4 text-white/80" />
            <h3 className="text-xl font-semibold mb-2">Dynamic Auto-Regulation</h3>
            <p className="text-white/50">
              HeliX monitors your Readiness Score and dynamically scales workout
              intensity to prevent fatigue and maximize gains.
            </p>
          </div>
          <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02]">
            <Database className="w-8 h-8 mb-4 text-white/80" />
            <h3 className="text-xl font-semibold mb-2">AlloyDB Persistence</h3>
            <p className="text-white/50">
              Long-term memory mapping of your entire fitness journey,
              securely stored and organized for tracking progress.
            </p>
          </div>
          <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02]">
            <Calendar className="w-8 h-8 mb-4 text-white/80" />
            <h3 className="text-xl font-semibold mb-2">Calendar Booking</h3>
            <p className="text-white/50">
              The AI automatically finds open slots in your Google Calendar and
              books your workouts effortlessly.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

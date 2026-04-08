"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import Sidebar from "../../components/Sidebar";
import ChatInterface from "../../components/ChatInterface";
import ReadinessGauge from "../../components/ReadinessGauge";
import WeeklyCalendar from "../../components/WeeklyCalendar";
import { Loader2 } from "lucide-react";

export default function DashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <Loader2 className="w-8 h-8 text-white/50 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-black text-white font-sans selection:bg-white/30">
      <Sidebar />
      
      <main className="flex-1 p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Main Chat */}
        <div className="lg:col-span-2 flex flex-col h-[calc(100vh-4rem)]">
          <div className="mb-6">
            <h1 className="text-2xl font-bold tracking-tight mb-2">
              Good afternoon, {user.displayName?.split(" ")[0] || "Athlete"}
            </h1>
            <p className="text-white/50">
              Your autonomous agents are actively managing your fitness plan.
            </p>
          </div>
          
          <div className="flex-1 min-h-0">
            <ChatInterface />
          </div>
        </div>

        {/* Right Column - Widgets */}
        <div className="flex flex-col gap-6 h-[calc(100vh-4rem)]">
          <ReadinessGauge score={85} />
          <WeeklyCalendar />
          
          <div className="flex-1 p-6 rounded-xl border border-white/10 bg-white/[0.02] flex flex-col items-center justify-center text-center">
            <h3 className="font-semibold mb-2">Today's Protocol</h3>
            <p className="text-sm text-white/50 mb-6">
              Legs / Anterior Chain Focus
            </p>
            <button className="px-4 py-2 bg-white text-black text-sm font-medium rounded-md hover:bg-white/90 transition-colors w-full">
              View Full Workout
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

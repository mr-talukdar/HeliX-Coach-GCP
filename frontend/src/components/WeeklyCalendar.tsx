"use client";

import { useState } from "react";
import { Calendar as CalendarIcon, CheckCircle2, Circle, ExternalLink } from "lucide-react";
import { useAuth } from "@/lib/hooks/useAuth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export default function WeeklyCalendar() {
  const { user } = useAuth();
  const [calendarConnected, setCalendarConnected] = useState(false);

  const days = [
    { day: "Mon", active: true, completed: true, type: "Push" },
    { day: "Tue", active: true, completed: true, type: "Pull" },
    { day: "Wed", active: true, completed: false, type: "Legs", isToday: true },
    { day: "Thu", active: false, completed: false, type: "Rest" },
    { day: "Fri", active: true, completed: false, type: "Upper" },
    { day: "Sat", active: true, completed: false, type: "Lower" },
    { day: "Sun", active: false, completed: false, type: "Rest" },
  ];

  const handleConnectCalendar = () => {
    if (!user) return;
    window.location.href = `${API_URL}/api/auth/calendar?user_id=${user.uid}`;
  };

  return (
    <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02]">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-medium text-white/50 flex items-center gap-2">
          <CalendarIcon className="w-4 h-4" /> This Week
        </h3>
        <button
          onClick={handleConnectCalendar}
          className="text-xs text-white/70 hover:text-white transition-colors flex items-center gap-1"
        >
          <ExternalLink className="w-3 h-3" />
          {calendarConnected ? "Reconnect Calendar" : "Connect Google Calendar"}
        </button>
      </div>

      <div className="flex justify-between gap-2">
        {days.map((d, i) => (
          <div
            key={i}
            className={`flex flex-col items-center p-2 rounded-lg flex-1 ${
              d.isToday ? "bg-white/10 border border-white/20" : "bg-white/[0.01]"
            }`}
          >
            <span className={`text-xs mb-2 ${d.isToday ? "font-bold text-white" : "text-white/50"}`}>
              {d.day}
            </span>
            
            {d.completed ? (
              <CheckCircle2 className="w-5 h-5 text-green-500 mb-2" />
            ) : d.active ? (
              <Circle className="w-5 h-5 text-white/20 mb-2" />
            ) : (
              <div className="w-5 h-5 mb-2 flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-white/20" />
              </div>
            )}
            
            <span className="text-[10px] uppercase font-medium text-white/40 tracking-wider">
              {d.type}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

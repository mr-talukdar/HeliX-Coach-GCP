"use client";

import { useState, useRef, useEffect } from "react";
import { Send, User as UserIcon, Sparkles, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/hooks/useAuth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

interface Message {
  role: "user" | "agent";
  content: string;
}

const QUICK_ACTIONS = [
  "What is my workout today?",
  "Log my workout",
  "Check my schedule",
  "Assess my readiness",
  "Show my PRs",
];

export default function ChatInterface() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "agent",
      content:
        "Welcome to HeliX! I'm your autonomous fitness orchestrator. Ask me to check your schedule, generate a routine, log a workout, or assess your readiness.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Generate a unique session ID on mount
  useEffect(() => {
    setSessionId(`session-${Date.now()}-${Math.random().toString(36).slice(2)}`);
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: messageText };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Send to ADK backend via the /run or /run_sse endpoint
      const userId = user?.uid || "anonymous";
      const response = await fetch(`${API_URL}/api/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          app_name: "helix_coach",
          user_id: userId,
          session_id: sessionId,
          new_message: {
            role: "user",
            parts: [{ text: messageText }],
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();

      // Extract agent responses from the ADK response format
      let agentText = "I couldn't process that. Please try again.";
      if (data && data.length > 0) {
        // ADK returns an array of events; pick the last agent text
        const agentEvents = data.filter(
          (e: any) => e.content?.role === "model" && e.content?.parts
        );
        if (agentEvents.length > 0) {
          const lastEvent = agentEvents[agentEvents.length - 1];
          agentText = lastEvent.content.parts
            .map((p: any) => p.text || "")
            .join("")
            .trim();
        }
      }

      setMessages((prev) => [
        ...prev,
        { role: "agent", content: agentText || "Done." },
      ]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content:
            "⚠️ Could not reach the HeliX backend. Make sure the server is running on " +
            API_URL,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="flex flex-col h-full bg-white/[0.02] border border-white/10 rounded-xl overflow-hidden">
      {/* Chat header */}
      <div className="px-6 py-4 border-b border-white/10 bg-white/[0.01]">
        <h2 className="font-semibold text-white">HeliX Coach Chat</h2>
        <p className="text-sm text-white/50">🟢 Online — Agents Ready</p>
      </div>

      {/* Quick actions */}
      <div className="px-6 py-3 flex gap-2 overflow-x-auto border-b border-white/5 scrollbar-hide">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action}
            onClick={() => sendMessage(action)}
            disabled={isLoading}
            className="px-3 py-1.5 text-xs font-medium rounded-full border border-white/10 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white whitespace-nowrap transition-colors disabled:opacity-40"
          >
            {action}
          </button>
        ))}
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
          >
            <div
              className={`w-8 h-8 rounded flex items-center justify-center shrink-0 ${
                msg.role === "agent" ? "bg-white" : "bg-white/10"
              }`}
            >
              {msg.role === "agent" ? (
                <Sparkles className="w-5 h-5 text-black" />
              ) : (
                <UserIcon className="w-5 h-5 text-white/80" />
              )}
            </div>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-white text-black rounded-tr-sm"
                  : "bg-white/10 text-white rounded-tl-sm"
              }`}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">
                {msg.content}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-4">
            <div className="w-8 h-8 rounded bg-white flex items-center justify-center shrink-0">
              <Sparkles className="w-5 h-5 text-black" />
            </div>
            <div className="bg-white/10 rounded-2xl rounded-tl-sm px-4 py-3">
              <Loader2 className="w-4 h-4 animate-spin text-white/50" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="p-4 bg-white/[0.01] border-t border-white/10">
        <form onSubmit={handleSend} className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Tell HeliX what you want to achieve..."
            disabled={isLoading}
            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 pr-12 focus:outline-none focus:border-white/30 text-white placeholder:text-white/40 transition-colors disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 top-2 p-1.5 bg-white text-black hover:bg-white/90 rounded-md disabled:opacity-50 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}

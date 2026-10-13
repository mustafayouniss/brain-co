"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { getStoredToken } from "@/lib/backend-auth";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatState {
  isOpen: boolean;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

export function AIChatWidget() {
  const [state, setState] = React.useState<ChatState>({
    isOpen: false,
    messages: [],
    isLoading: false,
    error: null,
  });
  const [input, setInput] = React.useState("");
  const [isMinimized, setIsMinimized] = React.useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const panelRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [state.messages]);

  const toggleChat = () => {
    setState((prev) => ({ ...prev, isOpen: !prev.isOpen }));
  };

  const toggleMinimize = () => {
    setIsMinimized((prev) => !prev);
  };

  const sendMessage = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || state.isLoading) return;

    const token = getStoredToken();
    if (!token) {
      setState((prev) => ({
        ...prev,
        error: "Please login to use the AI chat",
      }));
      return;
    }

    const userMessage: Message = {
      role: "user",
      content: trimmedInput,
      timestamp: new Date(),
    };

    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: null,
    }));
    setInput("");

    try {
      const response = await fetch("/api/ai/prompt", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: trimmedInput }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "AI request failed");
      }

      const data = await response.json();

      const assistantMessage: Message = {
        role: "assistant",
        content: data.content,
        timestamp: new Date(),
      };

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
        isLoading: false,
      }));
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to get AI response";
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearError = () => {
    setState((prev) => ({ ...prev, error: null }));
  };

  const unreadCount = state.messages.length > 0 ? state.messages.length : null;

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Chat Panel */}
      {state.isOpen && (
        <div
          ref={panelRef}
          className={`
            mb-4 w-[400px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-2xl
            border border-[#202a3e] bg-[#0b1425] shadow-2xl
            transition-all duration-300 ease-in-out
            ${isMinimized ? "h-16" : "h-[500px]"}
          `}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#202a3e] bg-gradient-to-r from-[#0b1425] to-[#151d2e] px-4 py-3">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-[#946eff] to-[#7c3aed]">
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-white"
                  >
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                </div>
                <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-green-500 border-2 border-[#0b1425]" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">AI Assistant</h3>
                <p className="text-xs text-[#8a94a8]">
                  {state.isLoading ? "Typing..." : "Powered by Groq"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={toggleMinimize}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-[#8a94a8] transition-colors hover:bg-[#202a3e] hover:text-white"
                aria-label={isMinimized ? "Expand" : "Minimize"}
              >
                {isMinimized ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 15l-6-6-6 6" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                )}
              </button>
              <button
                onClick={toggleChat}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-[#8a94a8] transition-colors hover:bg-[#202a3e] hover:text-white"
                aria-label="Close chat"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages */}
          {!isMinimized && (
            <div className="flex h-[calc(100%-4rem)] flex-col overflow-hidden">
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {state.messages.length === 0 && (
                  <div className="flex h-full flex-col items-center justify-center text-center">
                    <div className="mb-4 rounded-full bg-[#202a3e] p-4">
                      <svg
                        width="32"
                        height="32"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        className="text-[#946eff]"
                      >
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      </svg>
                    </div>
                    <p className="text-sm text-[#8a94a8]">
                      Start a conversation to test the AI integration
                    </p>
                    <p className="mt-2 text-xs text-[#5c6b7f]">
                      Messages are powered by Groq's fast inference
                    </p>
                  </div>
                )}

                {state.messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div className={`flex max-w-[85%] gap-2 ${message.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                      {message.role === "assistant" && (
                        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#946eff] to-[#7c3aed]">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                          </svg>
                        </div>
                      )}
                      <div>
                        <div
                          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                            message.role === "user"
                              ? "bg-gradient-to-br from-[#946eff] to-[#7c3aed] text-white shadow-lg"
                              : "bg-[#202a3e] text-[#e0e0e0] border border-[#2a3448]"
                          }`}
                        >
                          {message.content}
                        </div>
                        <p className={`mt-1 text-xs text-[#8a94a8] ${message.role === "user" ? "text-right" : "text-left"}`}>
                          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}

                {state.isLoading && (
                  <div className="flex justify-start">
                    <div className="flex gap-2">
                      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#946eff] to-[#7c3aed]">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white">
                          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                        </svg>
                      </div>
                      <div className="rounded-2xl bg-[#202a3e] border border-[#2a3448] px-4 py-3">
                        <div className="flex items-center gap-1">
                          <div className="h-2 w-2 animate-bounce rounded-full bg-[#946eff]" style={{ animationDelay: '0ms' }} />
                          <div className="h-2 w-2 animate-bounce rounded-full bg-[#946eff]" style={{ animationDelay: '150ms' }} />
                          <div className="h-2 w-2 animate-bounce rounded-full bg-[#946eff]" style={{ animationDelay: '300ms' }} />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {state.error && (
                  <div className="mx-auto max-w-sm rounded-xl border border-[#ef4444] bg-[#ef4444]/10 p-4">
                    <div className="flex items-start gap-3">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mt-0.5 text-[#ef4444] flex-shrink-0">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M12 8v4" />
                        <path d="M12 16h.01" />
                      </svg>
                      <div className="flex-1">
                        <p className="text-sm text-[#ef4444]">{state.error}</p>
                        <button
                          onClick={clearError}
                          className="mt-2 text-xs text-[#8a94a8] underline hover:text-white"
                        >
                          Dismiss
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="border-t border-[#202a3e] bg-gradient-to-r from-[#0b1425] to-[#151d2e] p-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type your message..."
                    disabled={state.isLoading}
                    className="flex-1 rounded-xl border border-[#34405a] bg-[#050b1a] px-4 py-3 text-sm text-white placeholder-[#8a94a8] focus:border-[#946eff] focus:outline-none focus:ring-2 focus:ring-[#946eff]/20 disabled:opacity-50 transition-all"
                  />
                  <Button
                    onClick={sendMessage}
                    disabled={!input.trim() || state.isLoading}
                    className="h-11 w-11 rounded-xl shadow-lg"
                    variant="primary"
                  >
                    {state.isLoading ? (
                      <svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                    ) : (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                      </svg>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Launcher Button */}
      <div className="relative">
        <Button
          onClick={toggleChat}
          className="h-16 w-16 rounded-full shadow-2xl transition-all duration-300 hover:scale-110 active:scale-95"
          variant="primary"
          aria-label={state.isOpen ? "Close chat" : "Open chat"}
        >
          {state.isOpen ? (
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          ) : (
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          )}
        </Button>
        {unreadCount && !state.isOpen && (
          <div className="absolute -top-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-[#ef4444] text-xs font-semibold text-white shadow-lg">
            {unreadCount}
          </div>
        )}
        <div className="absolute -bottom-1 -right-1 h-3 w-3 rounded-full bg-green-500 border-2 border-[#050b1a]" />
      </div>
    </div>
  );
}

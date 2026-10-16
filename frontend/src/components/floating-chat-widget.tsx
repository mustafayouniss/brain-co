"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/**
 * Floating AI Chat Widget - Integration Testing Feature
 * 
 * This widget provides a floating chat interface for testing the end-to-end
 * frontend-to-backend AI integration. It reuses the existing /api/ai/prompt
 * endpoint and backend LLM service.
 * 
 * Architecture:
 * Frontend Widget → /api/ai/prompt (Next.js) → /api/v1/ai/prompt (FastAPI) → LLMService → Configured Provider
 */
export function FloatingChatWidget() {
  const [isOpen, setIsOpen] = React.useState(false);
  const [input, setInput] = React.useState("");
  const [messages, setMessages] = React.useState<Array<{ role: "user" | "assistant"; content: string }>>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const messagesContainerRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    setMessages(prev => [...prev, { role: "user", content: trimmedInput }]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/ai/prompt", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: trimmedInput }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || "AI request failed");
      }

      const data = await response.json();
      setMessages(prev => [...prev, { role: "assistant", content: data.content }]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to get AI response";
      setError(errorMessage);
      // Restore the user's input so they can retry
      setInput(trimmedInput);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
      {/* Chat Panel */}
      {isOpen && (
        <div className="w-[calc(100vw-3rem)] max-w-md rounded-2xl border border-[#202a3e] bg-[#0b1425] shadow-2xl sm:w-96">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#202a3e] p-4">
            <h3 className="text-sm font-semibold text-white">AI Integration Test</h3>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-[#8a94a8] transition-colors hover:bg-[#202a3e] hover:text-white"
              aria-label="Close chat"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div
            ref={messagesContainerRef}
            className="h-[400px] overflow-y-auto p-4 space-y-3"
          >
            {messages.length === 0 ? (
              <div className="flex h-full items-center justify-center text-center">
                <p className="text-sm text-[#8a94a8]">
                  Test the AI integration by sending a message
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div className={`max-w-[80%] rounded-lg p-3 ${
                    msg.role === "user"
                      ? "bg-[#946eff] text-white"
                      : "bg-[#202a3e] text-[#a7b0c1]"
                  }`}>
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex justify-start">
                <div className="rounded-lg bg-[#202a3e] p-3 text-[#8a94a8]">
                  <p className="text-sm">Thinking...</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Error */}
          {error && (
            <div className="mx-4 mb-3 rounded-lg border border-[#4a1a1a] bg-[#1a0a0a] p-3">
              <p className="text-xs text-[#ff6b6b]">{error}</p>
            </div>
          )}

          {/* Input */}
          <div className="border-t border-[#202a3e] p-4">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message..."
                disabled={isLoading}
                className="h-10"
              />
              <Button
                onClick={sendMessage}
                disabled={isLoading || !input.trim()}
                size="md"
                className="h-10 px-4"
              >
                Send
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Launcher Button */}
      <Button
        onClick={() => setIsOpen(!isOpen)}
        size="lg"
        className="h-14 w-14 rounded-full p-0 shadow-lg"
        aria-label={isOpen ? "Close chat" : "Open chat"}
      >
        {isOpen ? (
          <svg
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        )}
      </Button>
    </div>
  );
}

"use client";

import * as React from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  AlertCircle,
  ArrowUp,
  Bot,
  Check,
  ChevronDown,
  Copy,
  MessageSquare,
  RotateCcw,
  Sparkles,
  X,
} from "lucide-react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

const STARTER_PROMPTS = [
  {
    icon: Sparkles,
    title: "What is Brain?",
    prompt: "What is Brain, and how can it help a business preserve organizational knowledge?",
  },
  {
    icon: Bot,
    title: "AI Employees",
    prompt: "What kinds of AI employees and business workflows is Brain designed to support?",
  },
  {
    icon: MessageSquare,
    title: "Getting Started",
    prompt: "How does Brain connect workflows, organizational knowledge, and business operations?",
  },
];

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/**
 * Enhanced Floating AI Assistant Widget
 *
 * Implements a modern, dynamic, responsive chat experience with:
 * - Animated launcher with presence indicators and contextual teaser
 * - Framer Motion transitions (respecting prefers-reduced-motion)
 * - Clickable starter prompts and new conversation reset
 * - Copy-to-clipboard on assistant responses
 * - Dynamic loading pulse and inline retry mechanisms
 * - Multiline composer with Enter to send and Shift+Enter for newlines
 * - Strict preservation of backend AI contracts & anonymous dev testing
 */
export function FloatingChatWidget() {
  const [isOpen, setIsOpen] = React.useState(false);
  const [input, setInput] = React.useState("");
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [lastFailedPrompt, setLastFailedPrompt] = React.useState<string | null>(null);
  const [copiedId, setCopiedId] = React.useState<string | null>(null);
  const [hasUnread, setHasUnread] = React.useState(false);
  const [showTeaser, setShowTeaser] = React.useState(true);

  const shouldReduceMotion = useReducedMotion();
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  React.useEffect(() => {
    if (isOpen) {
      setHasUnread(false);
      setShowTeaser(false);
      scrollToBottom("auto");
      setTimeout(() => textareaRef.current?.focus(), 150);
    }
  }, [isOpen]);

  React.useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom(shouldReduceMotion ? "auto" : "smooth");
    }
  }, [messages, isLoading, shouldReduceMotion]);

  const handleCopy = async (id: string, text: string) => {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
      }
    } catch {
      // Ignore clipboard write restrictions in headless browser environments
    }
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleResetChat = () => {
    if (isLoading) return;
    setMessages([]);
    setError(null);
    setLastFailedPrompt(null);
    setTimeout(() => textareaRef.current?.focus(), 50);
  };

  const sendPrompt = async (promptToSend: string) => {
    const trimmed = promptToSend.trim();
    if (!trimmed || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmed,
      timestamp: formatTime(new Date()),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);
    setLastFailedPrompt(null);

    // Auto-resize textarea back to default
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      const response = await fetch("/api/ai/prompt", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: trimmed, model: "" }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        let message = "AI request failed";
        if (response.status === 401) {
          message = "Authentication required: Please log in to your account first.";
        } else if (typeof errorData.error === "string") {
          message = errorData.error;
        } else if (errorData.error && typeof errorData.error.message === "string") {
          message = errorData.error.message;
        } else if (typeof errorData.detail === "string") {
          message = errorData.detail;
        } else if (response.status === 504 || response.status === 408) {
          message = "Request timed out. Please try again.";
        }
        throw new Error(message);
      }

      const data = await response.json();
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.content || "No response received.",
        timestamp: formatTime(new Date()),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (!isOpen) {
        setHasUnread(true);
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Failed to obtain AI response";
      setError(errMsg);
      setLastFailedPrompt(trimmed);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendPrompt(input);
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const target = e.target;
    target.style.height = "auto";
    target.style.height = `${Math.min(target.scrollHeight, 120)}px`;
  };

  const retryLast = () => {
    if (lastFailedPrompt) {
      void sendPrompt(lastFailedPrompt);
    }
  };

  return (
    <aside
      aria-label="Brain-Co AI Assistant"
      className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-50 flex flex-col items-end pointer-events-auto"
    >
      {/* Expanded Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            key="chat-window"
            initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95, y: 16 }}
            animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, scale: 1, y: 0 }}
            exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
            className="mb-3 flex flex-col overflow-hidden w-[calc(100vw-2rem)] sm:w-[410px] max-w-[420px] h-[580px] max-h-[calc(100vh-6.5rem)] rounded-2xl border border-border-strong/70 bg-[#070d1d]/95 backdrop-blur-xl shadow-2xl shadow-black/60"
            role="dialog"
            aria-modal="false"
            aria-labelledby="ai-chat-title"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border/80 bg-surface/80 px-4 py-3.5 backdrop-blur-md">
              <div className="flex items-center gap-3 min-w-0">
                <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#8052ff] to-[#4c2bc0] shadow-md shadow-[#8052ff]/20 text-white">
                  <Sparkles className="h-4 w-4" />
                  <span className="absolute -bottom-0.5 -right-0.5 flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500 border border-[#070d1d]" />
                  </span>
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <h3 id="ai-chat-title" className="text-sm font-semibold text-white truncate">
                      Brain-Co AI
                    </h3>
                    <span className="rounded-full bg-brand-soft px-1.5 py-0.2 text-[10px] font-medium text-[#c9c2ff]">
                      v1
                    </span>
                  </div>
                  <p className="text-[11px] text-[#8a94a8] truncate">
                    General Brain Assistant • Ready
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1">
                {messages.length > 0 && (
                  <button
                    type="button"
                    onClick={handleResetChat}
                    disabled={isLoading}
                    title="New conversation"
                    aria-label="New conversation"
                    className="flex h-8 w-8 items-center justify-center rounded-lg text-[#8a94a8] transition-colors hover:bg-surface-2 hover:text-white disabled:opacity-40"
                  >
                    <RotateCcw className="h-4 w-4" />
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  title="Close chat"
                  aria-label="Close chat"
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-[#8a94a8] transition-colors hover:bg-surface-2 hover:text-white"
                >
                  <ChevronDown className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Conversation Messages */}
            <div
              className="flex-1 overflow-y-auto p-4 space-y-3.5 scroll-smooth overscroll-contain"
              role="log"
              aria-live="polite"
              aria-relevant="additions text"
            >
              {messages.length === 0 ? (
                <div className="flex h-full flex-col justify-between py-2">
                  <div className="flex flex-col items-center text-center px-2 pt-4">
                    <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-soft text-[#c9c2ff] ring-1 ring-brand/30 shadow-inner">
                      <Bot className="h-6 w-6" />
                    </div>
                    <h4 className="text-base font-semibold text-white">
                      Brain Assistant
                    </h4>
                    <p className="mt-1.5 text-xs leading-relaxed text-[#8a94a8] max-w-[280px]">
                      Ask about the Brain platform, AI employees, organizational knowledge, and how Brain can help your business.
                    </p>
                  </div>

                  <div className="space-y-2 pt-4">
                    <p className="text-[11px] font-medium uppercase tracking-wider text-[#8a94a8] px-1">
                      Suggested Inquiries
                    </p>
                    <div className="space-y-1.5">
                      {STARTER_PROMPTS.map((item, idx) => {
                        const IconComponent = item.icon;
                        return (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => void sendPrompt(item.prompt)}
                            disabled={isLoading}
                            className="group flex w-full items-start gap-2.5 rounded-xl border border-border/60 bg-surface/60 p-2.5 text-left text-xs transition-all hover:border-brand/50 hover:bg-surface-2 focus-visible:outline-2 focus-visible:outline-brand"
                          >
                            <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-surface-2 text-[#9ba5b9] group-hover:text-brand">
                              <IconComponent className="h-3.5 w-3.5" />
                            </span>
                            <div className="min-w-0 flex-1">
                              <div className="font-medium text-white group-hover:text-violet">
                                {item.title}
                              </div>
                              <div className="truncate text-[11px] text-[#8a94a8]">
                                {item.prompt}
                              </div>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 8 }}
                    animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
                    transition={{ duration: 0.18 }}
                    className={`flex flex-col ${
                      msg.role === "user" ? "items-end" : "items-start"
                    }`}
                  >
                    <div
                      className={`group relative max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "bg-gradient-to-br from-brand to-[#6533f0] text-white rounded-tr-xs shadow-md shadow-brand/10"
                          : "bg-surface-2/90 border border-border/70 text-[#efeaff] rounded-tl-xs shadow-sm"
                      }`}
                    >
                      <p className="whitespace-pre-wrap break-words">{msg.content}</p>

                      {/* Assistant message copy action */}
                      {msg.role === "assistant" && (
                        <div className="mt-2 pt-1.5 border-t border-border/40 flex items-center justify-between text-[10px] text-[#8a94a8]">
                          <span className="opacity-75">{msg.timestamp}</span>
                          <button
                            type="button"
                            onClick={() => handleCopy(msg.id, msg.content)}
                            className="flex items-center gap-1 rounded px-1.5 py-0.5 transition-colors hover:bg-surface hover:text-white"
                            title="Copy response"
                          >
                            {copiedId === msg.id ? (
                              <>
                                <Check className="h-3 w-3 text-emerald-400" />
                                <span className="text-emerald-400">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="h-3 w-3" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                        </div>
                      )}
                    </div>

                    {msg.role === "user" && (
                      <span className="mt-1 px-1 text-[10px] text-[#8a94a8]">
                        {msg.timestamp}
                      </span>
                    )}
                  </motion.div>
                ))
              )}

              {/* Dynamic Loading State */}
              {isLoading && (
                <div className="flex items-start gap-2 pt-1">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-surface-2 text-brand">
                    <Bot className="h-3.5 w-3.5 animate-pulse" />
                  </div>
                  <div className="rounded-2xl rounded-tl-xs bg-surface-2/90 border border-border/70 px-4 py-3 text-sm text-[#8a94a8]">
                    <div className="flex items-center gap-1.5">
                      <span className="h-1.5 w-1.5 rounded-full bg-brand animate-bounce [animation-delay:-0.3s]" />
                      <span className="h-1.5 w-1.5 rounded-full bg-brand animate-bounce [animation-delay:-0.15s]" />
                      <span className="h-1.5 w-1.5 rounded-full bg-brand animate-bounce" />
                      <span className="ml-2 text-xs font-medium text-[#a7b0c1]">Thinking…</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Error Banner with Retry */}
            {error && (
              <div className="mx-4 mb-2 flex items-start justify-between gap-2.5 rounded-xl border border-red-500/30 bg-red-950/40 p-2.5 text-xs text-red-200 backdrop-blur-sm animate-in fade-in duration-200">
                <div className="flex items-start gap-2 min-w-0">
                  <AlertCircle className="h-4 w-4 shrink-0 text-red-400 mt-0.5" />
                  <p className="break-words leading-tight">{error}</p>
                </div>
                {lastFailedPrompt && (
                  <button
                    type="button"
                    onClick={retryLast}
                    disabled={isLoading}
                    className="shrink-0 font-semibold text-brand-hover hover:underline"
                  >
                    Retry
                  </button>
                )}
              </div>
            )}

            {/* Input Composer */}
            <div className="border-t border-border/80 bg-surface/90 p-3 backdrop-blur-md">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void sendPrompt(input);
                }}
                className="flex items-end gap-2 rounded-xl border border-border-strong/70 bg-[#050b1a] p-1.5 focus-within:border-brand focus-within:ring-1 focus-within:ring-brand/40 transition-all"
              >
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={handleInput}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about Brain, AI employees, or your organization…"
                  rows={1}
                  disabled={isLoading}
                  className="flex-1 max-h-28 resize-none bg-transparent px-2.5 py-1.5 text-sm text-white placeholder-[#8a94a8] focus:outline-none disabled:opacity-50"
                  aria-label="Ask AI prompt"
                />
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  aria-label="Send message"
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand text-white transition-all hover:bg-brand-hover active:scale-95 disabled:pointer-events-none disabled:opacity-40"
                >
                  <ArrowUp className="h-4 w-4 stroke-[2.5]" />
                </button>
              </form>
              <div className="mt-1.5 flex items-center justify-between px-1 text-[10px] text-[#8a94a8]">
                <span>Shift+Enter for newline</span>
                <span>Powered by Brain-Co</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Launcher Button with Teaser Pill */}
      <div className="flex items-center gap-3">
        {/* Contextual Teaser / Greeting Pill */}
        <AnimatePresence>
          {!isOpen && showTeaser && (
            <motion.div
              initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: 10, scale: 0.95 }}
              animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, x: 0, scale: 1 }}
              exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: 10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="hidden sm:flex items-center gap-2 rounded-full border border-border-strong/80 bg-surface/95 px-3 py-1.5 shadow-xl backdrop-blur-md"
            >
              <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-medium text-white">Ask Brain AI</span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowTeaser(false);
                }}
                className="ml-1 text-[#8a94a8] hover:text-white"
                aria-label="Dismiss greeting"
              >
                <X className="h-3 w-3" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Launcher Trigger Button */}
        <motion.button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          whileHover={shouldReduceMotion ? {} : { scale: 1.05 }}
          whileTap={shouldReduceMotion ? {} : { scale: 0.94 }}
          className="relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-[#8a5fff] via-brand to-[#5a2ad6] text-white shadow-xl shadow-[#8052ff]/30 ring-1 ring-white/20 transition-all hover:shadow-[#8052ff]/50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          aria-expanded={isOpen}
          aria-label={isOpen ? "Close AI chat" : "Open AI assistant chat"}
        >
          {isOpen ? (
            <X className="h-6 w-6 stroke-[2.2]" />
          ) : (
            <>
              <Sparkles className="h-6 w-6 stroke-[2.2]" />
              {hasUnread && (
                <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-hover opacity-75" />
                  <span className="relative inline-flex rounded-full h-4 w-4 bg-brand border-2 border-[#050b1a]" />
                </span>
              )}
            </>
          )}
        </motion.button>
      </div>
    </aside>
  );
}

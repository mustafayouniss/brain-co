"use client";

import * as React from "react";
import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import Script from "next/script";
import { site } from "@/content/site";
import { CookieConsent } from "@/components/cookie-consent";
import { AIChatWidget } from "@/components/ai-chat-widget";

type Consent = "granted" | "denied" | null;
const CONSENT_KEY = "brainco:cookie-consent";

/** Loads Google Analytics only after explicit consent (no tracking by default). */
function Analytics() {
  // External-system subscription (localStorage + cross-tab storage events)
  // without setState-in-effect.
  const consent = React.useSyncExternalStore(
    (onStoreChange) => {
      const onStorage = (event: StorageEvent) => {
        if (event.key === CONSENT_KEY) onStoreChange();
      };
      window.addEventListener("storage", onStorage);
      return () => window.removeEventListener("storage", onStorage);
    },
    () => window.localStorage.getItem(CONSENT_KEY) as Consent,
    () => null,
  );

  if (!site.gaId || consent !== "granted") return null;

  return (
    <>
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${site.gaId}`}
        strategy="afterInteractive"
      />
      <Script id="ga4" strategy="afterInteractive">
        {`window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', '${site.gaId}', { anonymize_ip: true });`}
      </Script>
    </>
  );
}

/** Registers the service worker so the site is installable (PWA). */
function ServiceWorkerRegistration() {
  React.useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    const register = () => {
      navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {
        /* offline support is progressive enhancement only */
      });
    };
    if (document.readyState === "complete") register();
    else window.addEventListener("load", register, { once: true });
    return () => window.removeEventListener("load", register);
  }, []);
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange>
      {children}
      <Analytics />
      <ServiceWorkerRegistration />
      <CookieConsent />
      <AIChatWidget />
      <Toaster
        position="bottom-right"
        offset={16}
        toastOptions={{
          style: {
            background: "var(--elevated)",
            border: "1px solid var(--border)",
            color: "var(--fg)",
          },
        }}
      />
    </ThemeProvider>
  );
}

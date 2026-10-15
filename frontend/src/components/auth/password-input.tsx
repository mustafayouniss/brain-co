"use client";

import * as React from "react";
import { Eye, EyeOff } from "lucide-react";
import { authCopy } from "@/content/marketing";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const copy = authCopy.login;

/** Password input with show/hide toggle (task B: password with show/hide).
 *  Shared by the login and registration screens. */
export const PasswordInput = React.forwardRef<
  HTMLInputElement,
  Omit<React.InputHTMLAttributes<HTMLInputElement>, "type">
>(function PasswordInput({ className, disabled, ...props }, ref) {
  const [show, setShow] = React.useState(false);
  return (
    <div className="relative">
      <Input
        ref={ref}
        type={show ? "text" : "password"}
        className={cn("pr-11", className)}
        disabled={disabled}
        {...props}
      />
      <button
        type="button"
        onClick={() => setShow((v) => !v)}
        aria-label={show ? copy.hidePassword : copy.showPassword}
        aria-pressed={show}
        disabled={disabled}
        className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded-lg p-2 text-subtle transition-colors hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
      >
        {show ? (
          <EyeOff className="size-4" aria-hidden="true" />
        ) : (
          <Eye className="size-4" aria-hidden="true" />
        )}
      </button>
    </div>
  );
});

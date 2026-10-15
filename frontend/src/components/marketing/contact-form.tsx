"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { contactSchema, type ContactInput } from "@/lib/validation";
import { contactCopy } from "@/content/marketing";
import { Field, Input, Textarea, Label } from "@/components/ui/input";
import { buttonClasses } from "@/components/ui/button";

const { form } = contactCopy;

/** Contact form: RHF + Zod client validation, Zod re-validation server-side. */
export function ContactForm() {
  const [sending, setSending] = React.useState(false);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ContactInput>({
    resolver: zodResolver(contactSchema),
    defaultValues: { name: "", email: "", company: "", topic: "Product demo", message: "", website: "" },
  });

  const onSubmit = async (values: ContactInput) => {
    if (sending) return;
    setSending(true);
    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => ({}))) as { error?: string };
        toast.error(data.error ?? form.errorBody);
        return;
      }
      toast.success(form.successTitle, { description: form.successBody });
      reset();
    } catch {
      toast.error(form.errorBody);
    } finally {
      setSending(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label={form.name} htmlFor="contact-name" error={errors.name?.message}>
          <Input
            id="contact-name"
            autoComplete="name"
            placeholder="Ada Lovelace"
            aria-invalid={!!errors.name}
            {...register("name")}
          />
        </Field>
        <Field label={form.email} htmlFor="contact-email" error={errors.email?.message}>
          <Input
            id="contact-email"
            type="email"
            autoComplete="email"
            placeholder="you@company.com"
            aria-invalid={!!errors.email}
            {...register("email")}
          />
        </Field>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label={form.company} htmlFor="contact-company" error={errors.company?.message}>
          <Input id="contact-company" autoComplete="organization" placeholder="Acme Inc." {...register("company")} />
        </Field>
        <Field label={form.topic} htmlFor="contact-topic" error={errors.topic?.message}>
          <select
            id="contact-topic"
            className="h-11 w-full rounded-xl border border-border-strong bg-surface px-3.5 text-sm text-foreground focus:border-gold focus:outline-none"
            {...register("topic")}
          >
            {form.topics.map((topic) => (
              <option key={topic} value={topic}>
                {topic}
              </option>
            ))}
          </select>
        </Field>
      </div>

      <Field label={form.message} htmlFor="contact-message" error={errors.message?.message}>
        <Textarea
          id="contact-message"
          placeholder={form.messagePlaceholder}
          aria-invalid={!!errors.message}
          {...register("message")}
        />
      </Field>

      {/* Honeypot: hidden from humans, bots fill it in. */}
      <div className="hidden">
        <Label htmlFor="contact-website">Website</Label>
        <input id="contact-website" tabIndex={-1} autoComplete="off" {...register("website")} />
      </div>

      <div className="mt-1">
        <button
          type="submit"
          disabled={sending}
          className={buttonClasses("primary", "lg", "w-full sm:w-auto")}
        >
          {sending ? form.sending : form.submit}
        </button>
      </div>
    </form>
  );
}

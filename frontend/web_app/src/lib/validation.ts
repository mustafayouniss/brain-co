import { z } from "zod";

/** Contact form — validated client-side (RHF) and server-side (API route). */
export const contactSchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, "Please enter your full name.")
    .max(120, "Name is too long."),
  email: z
    .string()
    .trim()
    .min(1, "We need your email to reply.")
    .email("Please enter a valid email address."),
  company: z.string().trim().max(120).optional(),
  topic: z.enum(["Product demo", "Security & privacy", "Partnerships", "Support", "Other"]),
  message: z
    .string()
    .trim()
    .min(10, "Tell us a little more (10 characters minimum).")
    .max(4000, "Message is too long (4000 characters maximum)."),
  /** Honeypot — must stay empty for humans. */
  website: z.string().max(0, "Bot detected.").optional().or(z.literal("")),
});

export type ContactInput = z.infer<typeof contactSchema>;

/** Login form — Backend JWT authentication (docs/backend/api/auth.md). */
export const loginSchema = z.object({
  email: z.string().trim().email("Enter a valid email address."),
  password: z.string().min(12, "Password must be at least 12 characters."),
  remember: z.boolean().optional(),
});

export type LoginInput = z.infer<typeof loginSchema>;

/** Registration form shown during onboarding (source: AccountScreen).
 *  "Company name" is required only when the Company account mode is chosen,
 *  exactly like the source app which conditionally renders the field. */
export const accountSchema = (requireCompany: boolean) =>
  z
    .object({
      companyName: z.string().optional(),
      fullName: z
        .string()
        .trim()
        .min(2, "Please enter your full name.")
        .max(120, "Name is too long."),
      email: z.string().trim().email("Please enter a valid email address."),
      password: z
        .string()
        .min(8, "Use at least 8 characters.")
        .regex(/[0-9]/, "Include at least one number."),
      confirmPassword: z.string(),
    })
    .refine((data) => data.password === data.confirmPassword, {
      message: "Passwords do not match.",
      path: ["confirmPassword"],
    })
    .refine(
      (data) => !requireCompany || (data.companyName ?? "").trim().length >= 2,
      {
        message: "Please enter your company name.",
        path: ["companyName"],
      },
    );

export type AccountInput = z.infer<ReturnType<typeof accountSchema>>;

/** Organization survey — 4 steps validated step by step. */
export const surveySchema = z.object({
  organizationName: z.string().trim().min(2, "Organization name is required.").optional(),
  industry: z.string().trim().optional(),
  size: z.string().optional(),
  employees: z.string().trim().optional(),
  leadershipName: z.string().trim().optional(),
  brainUsers: z.string().trim().optional(),
  departments: z.array(z.string()).optional(),
  yourRole: z.string().trim().optional(),
  team: z.string().trim().optional(),
});

export type SurveyInput = z.infer<typeof surveySchema>;

"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useForm, type Path } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { surveyCopy, prototypeNote } from "@/content/app";
import { surveySchema, type SurveyInput } from "@/lib/validation";
import {
  FlowBody,
  FlowShell,
  FlowTag,
  FlowTitle,
  StepDots,
} from "@/components/onboarding/flow";
import { PrototypeBadge } from "@/components/auth/prototype-badge";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { useOnboarding } from "@/hooks/use-onboarding";
import { cn } from "@/lib/utils";

const emptySurvey: SurveyInput = {
  organizationName: "",
  industry: "",
  size: "",
  employees: "",
  leadershipName: "",
  brainUsers: "",
  departments: [],
  yourRole: "",
  team: "",
};

/**
 * Organization onboarding survey (source views `survey*`): 4 short steps
 * (Organization, People, Structure, Your role) with per-step validation and
 * data preserved across steps, refresh and back navigation (existing
 * sessionStorage onboarding state). MOCK: no organization API exists — the
 * answers are stored locally only (docs/FLOW_AUDIT.md, stage 7 / D5).
 */
export default function SurveyScreen() {
  const router = useRouter();
  const { state, update, hydrated } = useOnboarding();

  // Deep-link/refresh guards: every prior stage must exist first.
  React.useEffect(() => {
    if (!hydrated) return;
    if (!state.domain) router.replace("/onboarding/domains");
    else if (!state.accountMode) router.replace("/onboarding/usage");
    else if (!state.account) router.replace("/onboarding/account");
  }, [hydrated, state.domain, state.accountMode, state.account, router]);

  if (!hydrated || !state.domain || !state.accountMode || !state.account) return null;

  return (
    <SurveyForm
      initial={state.survey}
      onDone={(survey) => {
        update({ survey });
        router.push("/onboarding/upload");
      }}
    />
  );
}

function SurveyForm({
  initial,
  onDone,
}: {
  initial: SurveyInput | null;
  onDone: (survey: SurveyInput) => void;
}) {
  const router = useRouter();
  const [step, setStep] = React.useState(0);
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    getValues,
    trigger,
    formState: { errors },
  } = useForm<SurveyInput>({
    resolver: zodResolver(surveySchema),
    defaultValues: initial ?? emptySurvey,
  });

  const stepDef = surveyCopy.steps[step];
  const isLast = step === surveyCopy.steps.length - 1;
  const size = watch("size");
  const departments = watch("departments") ?? [];

  async function next() {
    const fields = stepDef.fields.map((field) => field.name as Path<SurveyInput>);
    const valid = await trigger(fields);
    if (!valid) return;
    if (!isLast) {
      setStep((s) => s + 1);
      return;
    }
    handleSubmit(onDone)();
  }

  function back() {
    if (step > 0) setStep((s) => s - 1);
    else router.back();
  }

  const chipClass = (active: boolean) =>
    cn(
      "rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors",
      "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
      active
        ? "border-[#946eff] bg-[#946eff]/15 text-white"
        : "border-[#202a3e] text-[#a7b0c1] hover:border-[#34405a] hover:text-white",
    );

  return (
    <FlowShell as="section">
      <PrototypeBadge className="mt-8" />
      <FlowTag>{surveyCopy.sections[step]}</FlowTag>
      <FlowTitle id="survey-title" className="mt-4">
        {surveyCopy.title}
      </FlowTitle>
      <FlowBody>
        {surveyCopy.stepLabel(step + 1)} — {prototypeNote}
      </FlowBody>

      <StepDots
        total={surveyCopy.steps.length}
        active={step}
        ariaLabel={surveyCopy.stepLabel(step + 1)}
      />

      <div className="mt-8 w-full max-w-sm space-y-4 text-left">
        {stepDef.fields.map((field) => (
          <Field
            key={field.name}
            label={field.label}
            htmlFor={`survey-${field.name}`}
            error={errors[field.name as keyof SurveyInput]?.message}
          >
            <Input
              id={`survey-${field.name}`}
              aria-invalid={errors[field.name as keyof SurveyInput] ? true : undefined}
              aria-describedby={
                errors[field.name as keyof SurveyInput]
                  ? `survey-${field.name}-error`
                  : undefined
              }
              {...register(field.name as Path<SurveyInput>)}
            />
          </Field>
        ))}

        {stepDef.chips === "size" && (
          <fieldset>
            <legend className="text-[13px] font-semibold text-muted">
              {surveyCopy.sizeLabel}
            </legend>
            <div className="mt-2 flex flex-wrap gap-2" role="radiogroup" aria-label={surveyCopy.sizeLabel}>
              {surveyCopy.sizeOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  role="radio"
                  aria-checked={size === option}
                  onClick={() => setValue("size", option, { shouldValidate: true })}
                  className={chipClass(size === option)}
                >
                  {option}
                </button>
              ))}
            </div>
          </fieldset>
        )}

        {stepDef.chips === "departments" && (
          <fieldset>
            <legend className="text-[13px] font-semibold text-muted">
              {surveyCopy.departmentsLabel}
            </legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {surveyCopy.departmentOptions.map((option) => {
                const active = departments.includes(option);
                return (
                  <button
                    key={option}
                    type="button"
                    aria-pressed={active}
                    onClick={() => {
                      // Read the freshest store value so rapid successive
                      // toggles can't overwrite each other with a stale array.
                      const current = getValues("departments") ?? [];
                      setValue(
                        "departments",
                        current.includes(option)
                          ? current.filter((d) => d !== option)
                          : [...current, option],
                        { shouldValidate: true },
                      );
                    }}
                    className={chipClass(active)}
                  >
                    {option}
                  </button>
                );
              })}
            </div>
          </fieldset>
        )}
      </div>

      <div className="mt-8 flex w-full max-w-sm flex-col gap-2.5 sm:flex-row sm:justify-center">
        <Button variant="secondary" size="lg" onClick={back} className="w-full sm:w-auto">
          {surveyCopy.back}
        </Button>
        <Button size="lg" onClick={next} className="w-full sm:w-auto">
          {isLast ? surveyCopy.final : surveyCopy.next}
        </Button>
      </div>
    </FlowShell>
  );
}

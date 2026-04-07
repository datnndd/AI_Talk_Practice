import { SignOut } from "@phosphor-icons/react";

import BrandMark from "./BrandMark";

const FlowHeader = ({ currentStep, totalSteps, onExit }) => {
  const progress = `${currentStep}/${totalSteps}`;

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="mx-auto max-w-7xl px-4 pt-4 md:px-6">
        <div className="flex h-[72px] items-center justify-between rounded-[28px] border border-[var(--panel-border)] bg-[var(--nav-bg)] px-4 shadow-[0_24px_48px_-32px_rgba(15,23,42,0.25)] backdrop-blur-xl md:px-5">
          <BrandMark eyebrow="Onboarding Flow" />

          <div className="hidden items-center gap-4 md:flex">
            <div className="h-2 w-40 overflow-hidden rounded-full bg-[var(--chip-neutral-bg)]">
              <div
                className="h-full rounded-full bg-primary transition-[width] duration-300"
                style={{ width: `${(currentStep / totalSteps) * 100}%` }}
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="rounded-full border border-primary/15 bg-primary/8 px-4 py-2 text-[11px] font-black uppercase tracking-[0.22em] text-primary">
              Step {progress}
            </div>
            <button
              type="button"
              onClick={onExit}
              className="inline-flex items-center gap-2 rounded-2xl border border-[var(--panel-border)] px-4 py-3 text-xs font-black uppercase tracking-[0.18em] text-[var(--nav-text)] transition hover:-translate-y-0.5 hover:border-primary/20 hover:text-primary"
            >
              <SignOut size={16} weight="bold" />
              Exit
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default FlowHeader;

import { ArrowLeft } from "@phosphor-icons/react";

const SessionHeader = ({ onBack }) => {
  return (
    <header className="flex items-center">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-zinc-200 bg-white text-zinc-700 shadow-[0_14px_30px_-24px_rgba(15,23,42,0.5)] transition hover:-translate-y-0.5 hover:text-primary"
        aria-label="End session and return to topics"
      >
        <ArrowLeft size={18} weight="bold" />
      </button>
    </header>
  );
};

export default SessionHeader;

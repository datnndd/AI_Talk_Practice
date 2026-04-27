import { CheckCircle, LockSimple } from "@phosphor-icons/react";

const SectionCard = ({ section, isActive, isCompleted }) => {
  const IllustrationIcon = section.illustration?.Icon;

  return (
    <div className={`flex flex-col gap-4 py-8 px-4 ${isCompleted ? 'section-completed' : isActive ? 'section-active' : ''}`}>
      <div className="app-section-panel app-section-spacing">
        <div className="app-section-content">
          <button className="app-section-meta">
            <span>A1 • {section.details || "see details"}</span>
          </button>
          
          <h1 className="app-section-title">{section.title}</h1>
          
          <div className="app-section-status">
            {isCompleted ? (
              <>
                <CheckCircle className="app-section-icon text-brand-green" weight="fill" />
                <p className="app-section-success">Completed!</p>
              </>
            ) : isActive ? (
              <div className="app-progress-bar w-[200px] flex-1">
                <div 
                  className="app-progress-fill bg-white" 
                  style={{ width: `${section.progress || 0}%` }}
                />
                <div className="app-progress-shine opacity-30" />
                <div className="app-progress-label text-[#1cb0f6]">
                  {section.progress}%
                </div>
              </div>
            ) : (
              <>
                <LockSimple className="app-section-icon text-[#afafaf] opacity-70" weight="fill" />
                <p className="text-sm font-black text-[#afafaf] uppercase tracking-wide">
                  {section.units} units
                </p>
              </>
            )}
          </div>
        </div>

        <div className="app-section-action">
          <button className="app-section-button">
            <span className="app-section-button-label">
              {isCompleted ? "Review" : isActive ? "Continue" : "Jump to section"}
            </span>
          </button>
        </div>
      </div>

      {/* Illustration & Bubble (if provided) */}
      {section.illustration && (
        <div className="flex items-end justify-end gap-4 pr-32 mt-4">
          <div className="character-bubble max-w-[280px]">
            {section.illustration.text}
          </div>
          {IllustrationIcon ? (
            <IllustrationIcon
              size={64}
              weight="fill"
              color={section.illustration.color}
              aria-hidden="true"
              className="shrink-0"
            />
          ) : null}
        </div>
      )}
    </div>
  );
};

export default SectionCard;

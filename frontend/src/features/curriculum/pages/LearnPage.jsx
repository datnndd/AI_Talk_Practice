import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  CaretLeft,
  CheckCircle,
  ChatCircleText,
  FlagCheckered,
  GlobeHemisphereEast,
  LockKey,
  PlayCircle,
  Trophy,
} from "@phosphor-icons/react";
import { curriculumApi } from "@/features/curriculum/api/curriculumApi";

const sectionPrompts = [
  "사람들과 한국어로 조금 대화할 수 있어요.",
  "한국어로 일상 생활이 가능해요.",
  "상황에 따라 한국어로 그에 맞는 표현을 할 수 있어요.",
  "나의 희망, 목표, 계획과 같은 추상적 주제에 대해 말할 수 있어요.",
  "한국어를 편하게 할 수 있어요. 다양한 주제에 대해 자연스럽게 내 의견을 말할 수 있어요.",
];

const sectionColors = ["#1cb0f6", "#58cc02", "#7848f4", "#ff9600", "#ff4b4b"];

const getSectionState = (section, currentUnitId) => {
  const units = section.units || [];
  const completedUnits = units.filter((unit) => unit.progress_status === "completed").length;
  const firstOpenUnit = units.find((unit) => !unit.is_locked);
  const currentUnit = units.find((unit) => unit.id === currentUnitId) || firstOpenUnit;
  const isCompleted = units.length > 0 && completedUnits === units.length;
  const isLocked = units.length > 0 && units.every((unit) => unit.is_locked);
  const isActive = !isCompleted && !isLocked;
  const progress = units.length ? Math.round((completedUnits / units.length) * 100) : 0;

  return { completedUnits, currentUnit, isActive, isCompleted, isLocked, progress, units };
};

const LearningPathCard = ({ section, index, currentUnitId }) => {
  const { completedUnits, currentUnit, isActive, isCompleted, isLocked, progress, units } = getSectionState(
    section,
    currentUnitId,
  );
  const prompt = section.description || sectionPrompts[index % sectionPrompts.length];
  const accentColor = sectionColors[index % sectionColors.length];
  const IllustrationIcon = index % 2 === 0 ? ChatCircleText : GlobeHemisphereEast;
  const buttonLabel = isCompleted ? "Review" : isActive ? "Continue" : `Jump to ${section.title}`;
  const buttonTarget = isLocked ? "#" : currentUnit ? `/learn/units/${currentUnit.id}` : "#";

  return (
    <section className={`learn-section-card ${isCompleted ? "learn-section-completed" : ""} ${isActive ? "learn-section-active" : ""} ${isLocked ? "learn-section-locked" : ""}`}>
      <div className="learn-section-panel">
        <div className="min-w-0 flex-1">
          {!isLocked && (
            <button className="learn-section-level" type="button">
              {section.cefr_level || section.code || "A1"} • see details
            </button>
          )}
          <h2 className="learn-section-title">{section.title}</h2>
          <div className="learn-section-status">
            {isCompleted ? (
              <>
                <CheckCircle size={26} weight="fill" className="text-brand-green" />
                <span>Completed!</span>
              </>
            ) : isActive ? (
              <>
                <div className="learn-progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow={progress} role="progressbar">
                  <div className="learn-progress-fill" style={{ width: `${progress}%` }} />
                  <span>{progress}%</span>
                </div>
                <Trophy size={36} weight="fill" className="text-brand-green" />
              </>
            ) : (
              <>
                <LockKey size={24} weight="fill" className="text-[#afafaf]" />
                <span>{units.length} units</span>
              </>
            )}
          </div>
          {isLocked && section.subtitle && <p className="mt-2 text-sm font-bold text-[#afafaf]">{section.subtitle}</p>}
        </div>

        <Link to={buttonTarget} aria-disabled={isLocked} className={`learn-section-button ${isLocked ? "pointer-events-none" : ""}`}>
          {buttonLabel}
        </Link>
      </div>

      {(isActive || isLocked) && (
        <div className="learn-section-art">
          <div className="learn-speech-bubble">{prompt}</div>
          <div className="learn-mascot" style={{ color: accentColor }}>
            {isLocked ? <FlagCheckered size={82} weight="fill" /> : <IllustrationIcon size={82} weight="fill" />}
          </div>
          {isActive && currentUnit && (
            <div className="learn-current-unit">
              <PlayCircle size={20} weight="fill" />
              <span>{completedUnits}/{units.length} done • {currentUnit.title}</span>
            </div>
          )}
        </div>
      )}
    </section>
  );
};

const LearnPage = () => {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      const cachedCurriculum = curriculumApi.getCachedCurriculum();
      if (cachedCurriculum) {
        setData(cachedCurriculum);
      }
      setIsLoading(!cachedCurriculum);
      setError("");
      try {
        const response = await curriculumApi.getCurriculum();
        if (mounted) {
          setData(response);
          void curriculumApi.prefetchUnit(response?.current_unit_id);
        }
      } catch (err) {
        if (mounted) setError(err?.response?.data?.detail || "Không thể tải lộ trình học.");
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    if (curriculumApi.getCachedCurriculum()) {
      void curriculumApi.getCurriculum({ force: true }).then((response) => {
        if (mounted) {
          setData(response);
          void curriculumApi.prefetchUnit(response?.current_unit_id);
        }
      }).catch(() => null);
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  if (isLoading) {
    return <div className="py-8 text-sm font-semibold text-muted-foreground">Đang tải lộ trình...</div>;
  }

  return (
    <div className="learn-path-page">
      <header className="learn-path-header">
        <Link to="/dashboard" className="learn-back-link">
          <CaretLeft size={20} weight="bold" />
          <span>Back</span>
        </Link>
      </header>

      {error && <div className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-700">{error}</div>}

      <div className="learn-section-list">
        {(data?.sections || []).map((section) => (
          <LearningPathCard key={section.id} section={section} index={section.order_index ?? section.id ?? 0} currentUnitId={data?.current_unit_id} />
        ))}
      </div>
    </div>
  );
};

export default LearnPage;


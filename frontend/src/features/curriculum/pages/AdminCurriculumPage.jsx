import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowClockwise,
  FloppyDiskBack,
  PencilSimple,
  Plus,
  ProhibitInset,
  SpeakerHigh,
  X,
} from "@phosphor-icons/react";

import { adminApi } from "@/features/admin-scenarios/api/adminScenariosApi";
import AdminShell from "@/shared/components/admin/AdminShell";
import { adminCurriculumApi } from "@/features/curriculum/api/curriculumApi";
import { getApiBaseUrl } from "@/shared/api/httpClient";

const EMPTY_CONTENT = {
  shadowing: {
    reference_text: "Could you help me with my reservation?",
    meaning_vi: "B\u1ea1n c\u00f3 th\u1ec3 gi\u00fap t\u00f4i v\u1edbi \u0111\u1eb7t ch\u1ed7 c\u1ee7a t\u00f4i kh\u00f4ng?",
    sample_audio_url: "",
    slow_audio_url: "",
  },
  read_aloud: {
    text: "I would like to order breakfast, please.",
    meaning_vi: "T\u00f4i mu\u1ed1n g\u1ecdi b\u1eefa s\u00e1ng.",
    sample_audio_url: "",
  },
  definition_choice: {
    definition_text: "A booking made before you arrive.",
    definition_audio_url: "",
    options: [
      { word: "reservation", meaning_vi: "\u0111\u1eb7t ch\u1ed7", is_correct: true },
      { word: "reception", meaning_vi: "l\u1ec5 t\u00e2n", is_correct: false },
      { word: "recommendation", meaning_vi: "g\u1ee3i \u00fd", is_correct: false },
      { word: "restaurant", meaning_vi: "nh\u00e0 h\u00e0ng", is_correct: false },
    ],
  },
  quick_qa: {
    question_text: "What did you eat for breakfast?",
    question_audio_url: "",
    answer_hints: ["I ate bread.", "I had coffee.", "I ate noodles."],
    min_words: 2,
  },
};

const EXERCISE_TYPES = [
  { value: "shadowing", label: "Shadowing / Repeat" },
  { value: "read_aloud", label: "Read aloud" },
  { value: "definition_choice", label: "Definition choice" },
  { value: "quick_qa", label: "Quick Q&A" },
];

const CURRICULUM_STATUS_FILTERS = [
  { value: "", label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
];

const CEFR_FILTERS = ["", "A1", "A2", "B1", "B2", "C1", "C2"];

const pretty = (value) => JSON.stringify(value || {}, null, 2);

const sortedById = (items = []) => [...items].sort((a, b) => a.id - b.id);
const sortedByOrder = (items = []) => [...items].sort((a, b) => (a.order_index - b.order_index) || (a.id - b.id));

const parseNumber = (value, fallback = 0) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const getErrorMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || item.message || String(item)).join(" ");
  }
  return detail || error?.message || fallback;
};

const hasLessonContent = (lesson) => Boolean(lesson?.content && Object.keys(lesson.content).length > 0);
const normalizeExerciseNode = (lesson) => ({
  ...lesson,
  lesson_id: lesson.unit_id,
});

const normalizeSectionTree = (sections = []) =>
  sortedById(sections).map((section) => ({
    ...section,
    lessons: sortedById(section.units || []).map((unit) => ({
      ...unit,
      level_id: unit.section_id,
      exercises: sortedByOrder(unit.lessons || []).map(normalizeExerciseNode),
    })),
  }));

const statusTone = (isActive) =>
  isActive
    ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
    : "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300";

const FieldLabel = ({ children }) => (
  <label className="mb-2 block text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">
    {children}
  </label>
);

const StatusBadge = ({ children, isActive = true }) => (
  <span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] ${statusTone(isActive)}`}>
    {children}
  </span>
);

const EmptyState = ({ children }) => (
  <div className="rounded-[24px] border border-dashed border-zinc-200 bg-zinc-50 px-4 py-8 text-center text-sm font-medium text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-400">
    {children}
  </div>
);

const RowActions = ({ item, kind, items, onEdit, onToggle, onMove, disabled, canMove = false }) => (
  <div className="flex shrink-0 flex-wrap justify-end gap-1">
    <button type="button" onClick={(event) => { event.stopPropagation(); onEdit(); }} className="rounded-full border border-zinc-200 bg-white p-1.5 text-zinc-600 hover:text-primary dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-300" aria-label="Edit">
      <PencilSimple size={13} />
    </button>
    <button type="button" onClick={(event) => { event.stopPropagation(); onToggle(); }} className="rounded-full border border-zinc-200 bg-white p-1.5 text-zinc-600 hover:text-rose-600 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-300" aria-label={item.is_active ? "Deactivate" : "Restore"}>
      <ProhibitInset size={13} />
    </button>
    {canMove && (
      <button type="button" disabled={disabled || items.findIndex((entry) => entry.id === item.id) <= 0} onClick={(event) => { event.stopPropagation(); onMove(kind, items, item.id, -1); }} className="rounded-full border border-zinc-200 bg-white p-1.5 text-zinc-600 hover:text-primary disabled:opacity-30 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-300" aria-label="Move up">
        ↑
      </button>
    )}
    {canMove && (
      <button type="button" disabled={disabled || items.findIndex((entry) => entry.id === item.id) >= items.length - 1} onClick={(event) => { event.stopPropagation(); onMove(kind, items, item.id, 1); }} className="rounded-full border border-zinc-200 bg-white p-1.5 text-zinc-600 hover:text-primary disabled:opacity-30 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-300" aria-label="Move down">
        ↓
      </button>
    )}
  </div>
);

const CurriculumTreeSkeleton = () => (
  <div className="space-y-2">
    {[0, 1, 2].map((item) => (
      <div key={item} className="rounded-[18px] bg-white px-3 py-3 dark:bg-zinc-900">
        <div className="h-4 w-2/3 animate-pulse rounded-full bg-zinc-200 dark:bg-zinc-800" />
        <div className="mt-2 h-3 w-1/3 animate-pulse rounded-full bg-zinc-200 dark:bg-zinc-800" />
      </div>
    ))}
  </div>
);

const toLevelForm = (level) => ({
  code: level?.code || "",
  title: level?.title || "",
  cefr_level: level?.cefr_level || "",
  description: level?.description || "",
  is_active: level?.is_active ?? true,
});

const toLessonForm = (lesson, selectedLevelId, nextOrder) => ({
  level_id: lesson?.level_id ?? selectedLevelId ?? "",
  title: lesson?.title || "",
  description: lesson?.description || "",
  xp_reward: lesson?.xp_reward ?? 50,
  coin_reward: lesson?.coin_reward ?? 0,
  is_active: lesson?.is_active ?? true,
});

const toExerciseForm = (exercise, selectedLessonId, nextOrder) => {
  const type = exercise?.type || "shadowing";
  const content = exercise?.content || EMPTY_CONTENT[type];
  return {
    lesson_id: exercise?.lesson_id ?? selectedLessonId ?? "",
    type,
    title: exercise?.title || `Lesson ${nextOrder + 1}`,
    order_index: exercise?.order_index ?? nextOrder,
    pass_score: exercise?.pass_score ?? 80,
    is_active: exercise?.is_active ?? true,
    content,
    contentJson: pretty(content),
  };
};

const normalizeLevelPayload = (form) => ({
  code: form.code.trim(),
  title: form.title.trim(),
  cefr_level: form.cefr_level.trim() || null,
  description: form.description.trim() || null,
  is_active: Boolean(form.is_active),
});

const normalizeLessonPayload = (form) => ({
  section_id: parseNumber(form.level_id),
  title: form.title.trim(),
  description: form.description.trim() || null,
  xp_reward: parseNumber(form.xp_reward),
  coin_reward: parseNumber(form.coin_reward),
  is_active: Boolean(form.is_active),
});

const normalizeExercisePayload = (form) => ({
  unit_id: parseNumber(form.lesson_id),
  type: form.type,
  title: form.title.trim(),
  order_index: parseNumber(form.order_index),
  pass_score: parseNumber(form.pass_score, 80),
  is_active: Boolean(form.is_active),
  content: JSON.parse(form.contentJson || "{}"),
});

const absoluteApiUrl = (value) => {
  if (!value) return "";
  if (/^https?:\/\//i.test(value)) return value;
  const apiBase = getApiBaseUrl().replace(/\/$/, "");
  const origin = apiBase.endsWith("/api") ? apiBase.slice(0, -4) : apiBase;
  return `${origin}${value.startsWith("/") ? value : `/${value}`}`;
};

const AudioAssetControl = ({ value, onChange, text = "", language = "en", lessonId = "", compact = false }) => {
  const [state, setState] = useState({ loading: "", error: "" });
  const fileInputRef = useRef(null);

  const createTts = async () => {
    const defaultText = text?.trim() || window.prompt("Text for TTS", "")?.trim();
    if (!defaultText) {
      setState({ loading: "", error: "Nhập text để tạo TTS." });
      return;
    }
    const editableText = window.prompt("Text for TTS", defaultText);
    const finalText = editableText?.trim();
    if (!finalText) return;
    setState({ loading: "tts", error: "" });
    try {
      const result = await adminCurriculumApi.createLessonAudioTts({
        text: finalText,
        language: language || "en",
        ...(lessonId ? { lesson_id: parseNumber(lessonId) } : {}),
      });
      onChange(result.url || "");
    } catch (error) {
      setState({ loading: "", error: getErrorMessage(error, "Không thể tạo audio TTS.") });
      return;
    }
    setState({ loading: "", error: "" });
  };

  const uploadAudio = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setState({ loading: "upload", error: "" });
    try {
      const result = await adminCurriculumApi.uploadLessonAudio({
        file,
        lessonId: lessonId ? parseNumber(lessonId) : undefined,
        text,
        language,
      });
      onChange(result.url || "");
    } catch (error) {
      setState({ loading: "", error: getErrorMessage(error, "Không thể upload audio.") });
      return;
    } finally {
      event.target.value = "";
    }
    setState({ loading: "", error: "" });
  };

  return (
    <div className="space-y-2">
      <div className={`grid gap-2 ${compact ? "" : "sm:grid-cols-[minmax(0,1fr)_auto]"}`}>
        <div className="min-w-0 rounded-[16px] border border-zinc-200 bg-zinc-50 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-950">
          <p className="truncate text-xs font-semibold text-zinc-500 dark:text-zinc-400">
            {value || "Generate TTS hoặc upload file audio để lấy Supabase URL"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={createTts}
            disabled={Boolean(state.loading)}
            className="inline-flex items-center gap-1 rounded-full border border-zinc-200 px-2 py-1 text-[11px] font-black text-zinc-700 hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
          >
            <SpeakerHigh size={13} />
            {state.loading === "tts" ? "Generating" : "Generate TTS"}
          </button>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={Boolean(state.loading)}
            className="inline-flex items-center gap-1 rounded-full border border-zinc-200 px-2 py-1 text-[11px] font-black text-zinc-700 hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
          >
            Upload
          </button>
          <input ref={fileInputRef} type="file" accept="audio/*" onChange={uploadAudio} className="hidden" />
        </div>
      </div>
      {value ? <audio controls src={absoluteApiUrl(value)} className="h-9 w-full" /> : null}
      {state.error ? <p className="text-xs font-semibold text-rose-600 dark:text-rose-300">{state.error}</p> : null}
    </div>
  );
};

const curriculumKindLabel = (kind) => (kind === "level" ? "section" : kind === "lesson" ? "unit" : "lesson");

const EntityModal = ({
  kind,
  form,
  setForm,
  onClose,
  onSubmit,
  isSaving,
  levels,
  lessons,
  scenarios,
  onNeedScenarios,
  editingItem,
}) => {
  const [activeTab, setActiveTab] = useState("builder");

  const updateForm = (patch) => setForm((current) => ({ ...current, ...patch }));
  const updateExerciseContent = (content) => updateForm({ content, contentJson: pretty(content) });

  const kindLabel = curriculumKindLabel(kind);
  const title = `${editingItem ? "Edit" : "New"} ${kindLabel}`;

  const renderLevelFields = () => (
    <>
      <div className="grid gap-4 sm:grid-cols-[120px_120px_minmax(0,1fr)]">
        <div>
          <FieldLabel>Code</FieldLabel>
          <input
            data-testid="level-code-input"
            required
            value={form.code}
            onChange={(event) => updateForm({ code: event.target.value })}
            className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>
        <div>
          <FieldLabel>CEFR</FieldLabel>
          <input
            data-testid="section-cefr-input"
            value={form.cefr_level}
            onChange={(event) => updateForm({ cefr_level: event.target.value })}
            placeholder="A1"
            className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>
        <div>
          <FieldLabel>Title</FieldLabel>
          <input
            data-testid="level-title-input"
            required
            value={form.title}
            onChange={(event) => updateForm({ title: event.target.value })}
            className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>
      </div>
      <div>
        <FieldLabel>Description</FieldLabel>
        <textarea
          value={form.description}
          onChange={(event) => updateForm({ description: event.target.value })}
          className="min-h-[96px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
        />
      </div>
      <ToggleField label="Active" checked={form.is_active} onChange={(value) => updateForm({ is_active: value })} />
    </>
  );

  const renderLessonFields = () => (
    <>
      <div>
        <FieldLabel>Section</FieldLabel>
        <select
          value={form.level_id}
          onChange={(event) => updateForm({ level_id: event.target.value })}
          className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
        >
          {levels.map((level) => (
            <option key={level.id} value={level.id}>
              {level.cefr_level || level.code} - {level.title}
            </option>
          ))}
        </select>
      </div>
      <div>
        <FieldLabel>Title</FieldLabel>
        <input
          data-testid="lesson-title-input"
          required
          value={form.title}
          onChange={(event) => updateForm({ title: event.target.value })}
          className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
        />
      </div>
      <div>
        <FieldLabel>Description</FieldLabel>
        <textarea
          value={form.description}
          onChange={(event) => updateForm({ description: event.target.value })}
          className="min-h-[96px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <FieldLabel>XP</FieldLabel>
          <input
            type="number"
            min="0"
            value={form.xp_reward}
            onChange={(event) => updateForm({ xp_reward: event.target.value })}
            className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>
        <div>
          <FieldLabel>Coins</FieldLabel>
          <input
            type="number"
            min="0"
            value={form.coin_reward}
            onChange={(event) => updateForm({ coin_reward: event.target.value })}
            className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>
      </div>
      <ToggleField label="Active" checked={form.is_active} onChange={(value) => updateForm({ is_active: value })} />
    </>
  );

  const renderOptionsEditor = (content) => (
    <div>
      <FieldLabel>Options</FieldLabel>
      <textarea
        value={(content.options || []).map((option) => `${option.is_correct ? "*" : ""}${option.word || ""}${option.meaning_vi ? ` | ${option.meaning_vi}` : ""}`).join("\n")}
        onChange={(event) => {
          const options = event.target.value
            .split(/\n/)
            .map((line) => line.trim())
            .filter(Boolean)
            .map((line) => {
              const isCorrect = line.startsWith("*");
              const cleanLine = isCorrect ? line.slice(1).trim() : line;
              const [word, meaningVi] = cleanLine.split("|").map((item) => item.trim());
              return { word, meaning_vi: meaningVi || "", is_correct: isCorrect };
            });
          updateExerciseContent({ ...content, options });
        }}
        placeholder={"*reservation | \u0111\u1eb7t ch\u1ed7\nreception | l\u1ec5 t\u00e2n\nrecommendation | g\u1ee3i \u00fd\nrestaurant | nh\u00e0 h\u00e0ng"}
        className="min-h-[150px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 font-mono text-xs outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
      />
      <p className="mt-2 text-xs font-semibold text-zinc-500 dark:text-zinc-400">Prefix exactly one correct option with *. Use exactly four options.</p>
    </div>
  );

  const renderHintsEditor = (content) => (
    <div>
      <FieldLabel>Answer Hints</FieldLabel>
      <textarea
        value={(content.answer_hints || []).join("\n")}
        onChange={(event) => updateExerciseContent({
          ...content,
          answer_hints: event.target.value.split(/\n/).map((line) => line.trim()).filter(Boolean).slice(0, 3),
        })}
        placeholder={"I ate bread.\nI had coffee.\nI ate noodles."}
        className="min-h-[110px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
      />
    </div>
  );

  const renderExerciseBuilder = () => {
    const content = form.content || {};

    if (form.type === "shadowing") {
      return (
        <div className="space-y-4">
          <div>
            <FieldLabel>Reference Text</FieldLabel>
            <textarea value={content.reference_text || ""} onChange={(event) => updateExerciseContent({ ...content, reference_text: event.target.value })} className="min-h-[110px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950" />
          </div>
          <div>
            <FieldLabel>Meaning VI</FieldLabel>
            <textarea value={content.meaning_vi || ""} onChange={(event) => updateExerciseContent({ ...content, meaning_vi: event.target.value })} className="min-h-[90px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950" />
          </div>
          <div>
            <FieldLabel>Sample Audio</FieldLabel>
            <AudioAssetControl value={content.sample_audio_url || ""} text={content.reference_text || ""} language="en" lessonId={form.lesson_id} onChange={(audioUrl) => updateExerciseContent({ ...content, sample_audio_url: audioUrl })} />
          </div>
          <div>
            <FieldLabel>Slow Audio (optional)</FieldLabel>
            <AudioAssetControl value={content.slow_audio_url || ""} text={content.reference_text || ""} language="en" lessonId={form.lesson_id} onChange={(audioUrl) => updateExerciseContent({ ...content, slow_audio_url: audioUrl })} />
          </div>
        </div>
      );
    }

    if (form.type === "read_aloud") {
      return (
        <div className="space-y-4">
          <div>
            <FieldLabel>Text</FieldLabel>
            <textarea value={content.text || ""} onChange={(event) => updateExerciseContent({ ...content, text: event.target.value })} className="min-h-[150px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950" />
          </div>
          <div>
            <FieldLabel>Meaning VI</FieldLabel>
            <textarea value={content.meaning_vi || ""} onChange={(event) => updateExerciseContent({ ...content, meaning_vi: event.target.value })} className="min-h-[90px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950" />
          </div>
          <div>
            <FieldLabel>Sample Audio (optional)</FieldLabel>
            <AudioAssetControl value={content.sample_audio_url || ""} text={content.text || ""} language="en" lessonId={form.lesson_id} onChange={(audioUrl) => updateExerciseContent({ ...content, sample_audio_url: audioUrl })} />
          </div>
        </div>
      );
    }

    if (form.type === "definition_choice") {
      return (
        <div className="space-y-4">
          <div>
            <FieldLabel>Definition Text (admin only)</FieldLabel>
            <textarea value={content.definition_text || ""} onChange={(event) => updateExerciseContent({ ...content, definition_text: event.target.value })} className="min-h-[110px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950" />
          </div>
          <div>
            <FieldLabel>Definition Audio</FieldLabel>
            <AudioAssetControl value={content.definition_audio_url || ""} text={content.definition_text || ""} language="en" lessonId={form.lesson_id} onChange={(audioUrl) => updateExerciseContent({ ...content, definition_audio_url: audioUrl })} />
          </div>
          {renderOptionsEditor(content)}
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div>
          <FieldLabel>Question Text</FieldLabel>
          <textarea value={content.question_text || ""} onChange={(event) => updateExerciseContent({ ...content, question_text: event.target.value })} className="min-h-[110px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950" />
        </div>
        <div>
          <FieldLabel>Question Audio (optional)</FieldLabel>
          <AudioAssetControl value={content.question_audio_url || ""} text={content.question_text || ""} language="en" lessonId={form.lesson_id} onChange={(audioUrl) => updateExerciseContent({ ...content, question_audio_url: audioUrl })} />
        </div>
        {renderHintsEditor(content)}
        <div>
          <FieldLabel>Minimum Words</FieldLabel>
          <input type="number" min="1" value={content.min_words || 2} onChange={(event) => updateExerciseContent({ ...content, min_words: parseNumber(event.target.value, 2) })} className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950" />
        </div>
      </div>
    );
  };

  const renderExerciseFields = () => (
    <>
      <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_220px]">
        <div>
        <FieldLabel>Unit</FieldLabel>
          <select
            value={form.lesson_id}
            onChange={(event) => updateForm({ lesson_id: event.target.value })}
            className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
          >
            {lessons.map((lesson) => (
              <option key={lesson.id} value={lesson.id}>
                #{lesson.id} - {lesson.title}
              </option>
            ))}
          </select>
        </div>
        <div>
          <FieldLabel>Type</FieldLabel>
          <select
            data-testid="exercise-type-select"
            value={form.type}
            onChange={(event) => {
              const type = event.target.value;
              const content = EMPTY_CONTENT[type];
              updateForm({ type, content, contentJson: pretty(content) });
            }}
            className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
          >
            {EXERCISE_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div>
        <FieldLabel>Title</FieldLabel>
        <input
          data-testid="exercise-title-input"
          required
          value={form.title}
          onChange={(event) => updateForm({ title: event.target.value })}
          className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <FieldLabel>Order</FieldLabel>
          <input
            type="number"
            min="0"
            value={form.order_index}
            onChange={(event) => updateForm({ order_index: event.target.value })}
            className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>
        <div>
          <FieldLabel>Pass Score</FieldLabel>
          <input
            type="number"
            min="0"
            max="100"
            value={form.pass_score}
            onChange={(event) => updateForm({ pass_score: event.target.value })}
            className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
          />
        </div>
        <ToggleField label="Active" checked={form.is_active} onChange={(value) => updateForm({ is_active: value })} />
      </div>
      <div className="flex gap-2 rounded-[20px] bg-zinc-100 p-1 dark:bg-zinc-950">
        <button
          type="button"
          onClick={() => setActiveTab("builder")}
          className={`flex-1 rounded-2xl px-4 py-2 text-sm font-black ${activeTab === "builder" ? "bg-white text-primary shadow-sm dark:bg-zinc-900" : "text-zinc-500"}`}
        >
          Builder
        </button>
        <button
          type="button"
          data-testid="exercise-json-tab"
          onClick={() => setActiveTab("json")}
          className={`flex-1 rounded-2xl px-4 py-2 text-sm font-black ${activeTab === "json" ? "bg-white text-primary shadow-sm dark:bg-zinc-900" : "text-zinc-500"}`}
        >
          JSON
        </button>
      </div>
      {activeTab === "builder" ? (
        renderExerciseBuilder()
      ) : (
        <div>
          <FieldLabel>Content JSON</FieldLabel>
          <textarea
            data-testid="exercise-json-input"
            value={form.contentJson}
            onChange={(event) => updateForm({ contentJson: event.target.value })}
            className="min-h-[260px] w-full rounded-[20px] border border-zinc-200 bg-zinc-950 px-4 py-3 font-mono text-xs text-zinc-50 outline-none focus:border-primary"
          />
        </div>
      )}
    </>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/60 px-4 py-6">
      <div className="max-h-[92dvh] w-full max-w-3xl overflow-y-auto rounded-[30px] border border-zinc-200 bg-white p-5 shadow-2xl dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Curriculum Editor</p>
            <h2 className="mt-1 font-display text-2xl font-black tracking-tight">{title}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-zinc-200 text-zinc-500 hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
            aria-label="Close editor"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={onSubmit} className="mt-5 space-y-4">
          {kind === "level" && renderLevelFields()}
          {kind === "lesson" && renderLessonFields()}
          {kind === "exercise" && renderExerciseFields()}

          <div className="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center justify-center rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
            >
              Cancel
            </button>
            <button
              data-testid="save-curriculum-entity"
              type="submit"
              disabled={isSaving}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-black text-white shadow-lg shadow-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <FloppyDiskBack size={16} />
              {isSaving ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const ToggleField = ({ label, checked, onChange }) => (
  <label className="flex items-center justify-between gap-3 rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-black dark:border-zinc-700 dark:bg-zinc-950">
    <span>{label}</span>
    <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
  </label>
);

const AdminCurriculumPage = () => {
  const [levels, setLevels] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [hasLoadedScenarios, setHasLoadedScenarios] = useState(false);
  const [selectedLevelId, setSelectedLevelId] = useState(null);
  const [selectedLessonId, setSelectedLessonId] = useState(null);
  const [selectedExerciseId, setSelectedExerciseId] = useState(null);
  const [sectionDetailCache, setSectionDetailCache] = useState({});
  const [loadingSectionId, setLoadingSectionId] = useState(null);
  const [sectionDetailError, setSectionDetailError] = useState("");
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isReordering, setIsReordering] = useState(false);
  const [filters, setFilters] = useState({ search: "", status: "", cefr_level: "", page: 1, page_size: 30 });
  const [sectionTotal, setSectionTotal] = useState(0);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const selectedLevel = useMemo(
    () => sectionDetailCache[selectedLevelId] || levels.find((item) => item.id === selectedLevelId) || null,
    [levels, sectionDetailCache, selectedLevelId],
  );
  const selectedLessons = useMemo(() => sortedByOrder(selectedLevel?.lessons || []), [selectedLevel]);
  const selectedLesson = useMemo(
    () => selectedLessons.find((item) => item.id === selectedLessonId) || null,
    [selectedLessons, selectedLessonId],
  );
  const selectedExercises = useMemo(() => sortedByOrder(selectedLesson?.exercises || []), [selectedLesson]);
  const allLessons = useMemo(
    () => Object.values(sectionDetailCache).flatMap((level) => level.lessons || []),
    [sectionDetailCache],
  );

  const replaceExercise = useCallback((exerciseId, patch) => {
    setLevels((currentLevels) =>
      currentLevels.map((level) => ({
        ...level,
        lessons: (level.lessons || []).map((lesson) => ({
          ...lesson,
          exercises: (lesson.exercises || []).map((exercise) =>
            exercise.id === exerciseId ? { ...exercise, ...patch } : exercise
          ),
        })),
      })),
    );
    setSectionDetailCache((currentCache) =>
      Object.fromEntries(
        Object.entries(currentCache).map(([levelId, level]) => [
          levelId,
          {
            ...level,
            lessons: (level.lessons || []).map((lesson) => ({
              ...lesson,
              exercises: (lesson.exercises || []).map((exercise) =>
                exercise.id === exerciseId ? { ...exercise, ...patch } : exercise
              ),
            })),
          },
        ]),
      ),
    );
  }, []);

  const loadExerciseDetail = useCallback(
    async (exercise) => {
      if (!exercise || hasLessonContent(exercise)) {
        return exercise;
      }
      try {
        const detail = normalizeExerciseNode(await adminCurriculumApi.getLesson(exercise.id));
        replaceExercise(exercise.id, detail);
        return detail;
      } catch (detailError) {
        setError(getErrorMessage(detailError, "Failed to load lesson content."));
        return exercise;
      }
    },
    [replaceExercise],
  );

  const loadScenarios = useCallback(async () => {
    if (hasLoadedScenarios) {
      return;
    }
    try {
      const response = await adminApi.listScenarios({ page: 1, page_size: 100 });
      setScenarios(response.items || []);
    } catch {
      setScenarios([]);
    } finally {
      setHasLoadedScenarios(true);
    }
  }, [hasLoadedScenarios]);

  const loadLevels = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
      const response = await adminCurriculumApi.listSectionSummariesPaged(params);
      const ordered = normalizeSectionTree(response.items || []);
      setLevels(ordered);
      setSectionTotal(response.total || 0);
      setSelectedLevelId((current) => (current && ordered.some((item) => item.id === current) ? current : ordered[0]?.id || null));
      setSectionDetailCache({});
      setSectionDetailError("");
    } catch (loadError) {
      setError(getErrorMessage(loadError, "Failed to load curriculum."));
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const updateFilter = (key, value) => {
    setFilters((current) => ({ ...current, [key]: value, page: 1 }));
  };

  const resetFilters = () => {
    setFilters({ search: "", status: "", cefr_level: "", page: 1, page_size: 30 });
  };

  const totalSectionPages = Math.max(1, Math.ceil(sectionTotal / filters.page_size));

  const loadSectionDetail = useCallback(async (levelId, { force = false } = {}) => {
    if (!force && sectionDetailCache[levelId]) {
      return sectionDetailCache[levelId];
    }
    setLoadingSectionId(levelId);
    setSectionDetailError("");
    try {
      const detail = normalizeSectionTree([await adminCurriculumApi.getSection(levelId)])[0];
      setSectionDetailCache((current) => ({ ...current, [levelId]: detail }));
      return detail;
    } catch (loadError) {
      setSectionDetailError(getErrorMessage(loadError, "Failed to load section detail."));
      return null;
    } finally {
      setLoadingSectionId(null);
    }
  }, [sectionDetailCache]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadLevels();
    }, 350);
    return () => window.clearTimeout(timer);
  }, [loadLevels]);

  useEffect(() => {
    if (!selectedLevel) {
      setSelectedLessonId(null);
      return;
    }
    setSelectedLessonId((current) => (current && selectedLessons.some((item) => item.id === current) ? current : selectedLessons[0]?.id || null));
  }, [selectedLevel, selectedLessons]);

  useEffect(() => {
    if (!selectedLesson) {
      setSelectedExerciseId(null);
      return;
    }
    setSelectedExerciseId((current) => (current && selectedExercises.some((item) => item.id === current) ? current : selectedExercises[0]?.id || null));
  }, [selectedLesson, selectedExercises]);

  const openModal = async (kind, item = null) => {
    const nextExerciseOrder = selectedExercises.length;
    let modalItem = item;

    if (kind === "level") {
      setForm(toLevelForm(modalItem));
    } else if (kind === "lesson") {
      setForm(toLessonForm(modalItem, selectedLevelId));
    } else {
      modalItem = await loadExerciseDetail(modalItem);
      setForm(toExerciseForm(modalItem, selectedLessonId, nextExerciseOrder));
    }
    setModal({ kind, item: modalItem });
    setError("");
  };

  const closeModal = () => {
    setModal(null);
    setForm(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!modal || !form) return;

    setIsSaving(true);
    setError("");
    try {
      if (modal.kind === "level") {
        const payload = normalizeLevelPayload(form);
        const saved = modal.item
          ? await adminCurriculumApi.updateSection(modal.item.id, payload)
          : await adminCurriculumApi.createSection(payload);
        setSelectedLevelId(saved.id);
      } else if (modal.kind === "lesson") {
        const payload = normalizeLessonPayload(form);
        const saved = modal.item
          ? await adminCurriculumApi.updateUnit(modal.item.id, payload)
          : await adminCurriculumApi.createUnit(payload);
        setSelectedLevelId(saved.section_id);
        setSelectedLessonId(saved.id);
      } else {
        const payload = normalizeExercisePayload(form);
        const saved = modal.item
          ? await adminCurriculumApi.updateLesson(modal.item.id, payload)
          : await adminCurriculumApi.createLesson(payload);
        setSelectedLessonId(saved.unit_id);
        setSelectedExerciseId(saved.id);
      }
      setNotice(`${curriculumKindLabel(modal.kind)} saved.`);
      closeModal();
      await refreshCurrentData(modal.kind);
    } catch (submitError) {
      setError(getErrorMessage(submitError, `Failed to save ${curriculumKindLabel(modal.kind)}.`));
    } finally {
      setIsSaving(false);
    }
  };

  const toggleActive = async (kind, item) => {
    if (!item) return;
    const nextActive = !item.is_active;
    setError("");
    try {
      if (kind === "level") {
        if (nextActive) {
          await adminCurriculumApi.updateSection(item.id, { is_active: true });
        } else {
          await adminCurriculumApi.deleteSection(item.id);
        }
      } else if (kind === "lesson") {
        if (nextActive) {
          await adminCurriculumApi.updateUnit(item.id, { is_active: true });
        } else {
          await adminCurriculumApi.deleteUnit(item.id);
        }
      } else if (nextActive) {
        await adminCurriculumApi.updateLesson(item.id, { is_active: true });
      } else {
        await adminCurriculumApi.deleteLesson(item.id);
      }
      setNotice(nextActive ? `${curriculumKindLabel(kind)} restored.` : `${curriculumKindLabel(kind)} deactivated.`);
      await refreshCurrentData(kind);
    } catch (toggleError) {
      setError(getErrorMessage(toggleError, `Failed to update ${curriculumKindLabel(kind)}.`));
    }
  };

  const moveItem = async (kind, items, itemId, direction) => {
    if (kind !== "exercise") return;
    const currentIndex = items.findIndex((item) => item.id === itemId);
    const targetIndex = currentIndex + direction;
    if (currentIndex < 0 || targetIndex < 0 || targetIndex >= items.length) return;

    const reordered = [...items];
    const [item] = reordered.splice(currentIndex, 1);
    reordered.splice(targetIndex, 0, item);
    const payload = reordered.map((entry, index) => ({ id: entry.id, order_index: index }));

    setIsReordering(true);
    setError("");
    try {
      await adminCurriculumApi.reorderLessons(payload);
      setNotice(`${curriculumKindLabel(kind)} order updated.`);
      await refreshCurrentData(kind);
    } catch (reorderError) {
      setError(getErrorMessage(reorderError, `Failed to reorder ${curriculumKindLabel(kind)}.`));
    } finally {
      setIsReordering(false);
    }
  };

  const selectLevelNode = async (levelId) => {
    setSelectedLevelId(levelId);
    setSelectedLessonId(null);
    setSelectedExerciseId(null);
    void loadSectionDetail(levelId);
  };

  const selectLessonNode = async (levelId, lessonId) => {
    setSelectedLevelId(levelId);
    setSelectedLessonId(lessonId);
    setSelectedExerciseId(null);
  };

  const selectExerciseNode = async (levelId, lessonId, exerciseId) => {
    setSelectedLevelId(levelId);
    setSelectedLessonId(lessonId);
    setSelectedExerciseId(exerciseId);
  };

  const refreshCurrentData = async (kind = modal?.kind) => {
    if (kind === "level" || !selectedLevelId) {
      await loadLevels();
      return;
    }
    await loadSectionDetail(selectedLevelId, { force: true });
  };

  const summaryCards = [
    { label: "Sections", value: levels.length },
    { label: "Units", value: levels.reduce((sum, level) => sum + (level.lessons?.length || 0), 0) },
    { label: "Lessons", value: allLessons.reduce((sum, lesson) => sum + (lesson.exercises?.length || 0), 0) },
    { label: "Inactive", value: levels.filter((level) => !level.is_active).length + allLessons.filter((lesson) => !lesson.is_active).length },
  ];

  return (
    <AdminShell
      title="Curriculum Admin"
      subtitle="Manage sections, units, lessons, order, and runtime content."
    >
      <div className="space-y-6">
        {(notice || error) && (
          <div
            className={`rounded-[26px] px-5 py-4 text-sm font-semibold ${
              error
                ? "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300"
                : "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
            }`}
          >
            {error || notice}
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {summaryCards.map((card) => (
            <div key={card.label} className="rounded-[28px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <p className="text-[11px] font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">{card.label}</p>
              <p className="mt-3 font-display text-4xl font-black tracking-tight">{card.value}</p>
            </div>
          ))}
        </div>

        <section id="curriculum-library">
          <div className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <PanelHeader
              eyebrow="Curriculum Browser"
              title="Sections ? Units ? Lessons"
              actionLabel="New Section"
              actionTestId="new-section-button"
              onAction={() => openModal("level")}
              onRefresh={loadLevels}
            />

            <div className="mt-5 grid gap-3 rounded-[24px] border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-950 md:grid-cols-[1fr_180px_160px_auto]">
              <input
                type="search"
                value={filters.search}
                onChange={(event) => updateFilter("search", event.target.value)}
                placeholder="Search sections..."
                className="rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
              />
              <select
                value={filters.status}
                onChange={(event) => updateFilter("status", event.target.value)}
                className="rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
              >
                {CURRICULUM_STATUS_FILTERS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <select
                value={filters.cefr_level}
                onChange={(event) => updateFilter("cefr_level", event.target.value)}
                className="rounded-2xl border border-zinc-200 bg-white px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
              >
                {CEFR_FILTERS.map((level) => (
                  <option key={level || "all"} value={level}>{level || "All CEFR"}</option>
                ))}
              </select>
              <button
                type="button"
                onClick={resetFilters}
                className="rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-black text-zinc-700 transition hover:bg-white dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
              >
                Reset
              </button>
            </div>

            <div className="mt-5 grid gap-4 xl:grid-cols-3">
              <div className="rounded-[26px] border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950">
                <div className="mb-3 flex items-center justify-between gap-3 px-2">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Sections</p>
                    <p className="mt-1 text-xs font-semibold text-zinc-500">{levels.length} items</p>
                  </div>
                  <button type="button" onClick={() => openModal("level")} className="rounded-xl bg-primary px-3 py-2 text-xs font-black text-white">New</button>
                </div>
                <div className="space-y-2">
                  {isLoading && <EmptyState>Loading curriculum...</EmptyState>}
                  {!isLoading && levels.length === 0 && <EmptyState>No sections created yet.</EmptyState>}
                  {!isLoading && levels.map((level, levelIndex) => (
                    <div
                      key={level.id}
                      role="button"
                      tabIndex={0}
                      data-testid={`curriculum-level-row-${level.id}`}
                      onClick={() => selectLevelNode(level.id)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") selectLevelNode(level.id);
                      }}
                      className={`flex w-full items-start justify-between gap-3 rounded-[18px] px-3 py-3 text-left transition ${
                        selectedLevelId === level.id ? "bg-primary/10 text-primary dark:text-white" : "bg-white hover:bg-zinc-100 dark:bg-zinc-900 dark:hover:bg-zinc-800"
                      }`}
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-black">{levelIndex + 1}. {level.title}</p>
                        <p className="mt-1 truncate text-xs font-semibold text-zinc-500 dark:text-zinc-400">{level.cefr_level || level.code}</p>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-2">
                        <StatusBadge isActive={level.is_active}>{level.is_active ? "Active" : "Inactive"}</StatusBadge>
                        <RowActions item={level} kind="level" items={levels} onEdit={() => openModal("level", level)} onToggle={() => toggleActive("level", level)} onMove={moveItem} disabled={isReordering} />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 flex items-center justify-between gap-2 border-t border-zinc-200 px-2 pt-3 text-xs font-bold text-zinc-500 dark:border-zinc-800">
                  <button
                    type="button"
                    disabled={filters.page <= 1 || isLoading}
                    onClick={() => setFilters((current) => ({ ...current, page: Math.max(1, current.page - 1) }))}
                    className="rounded-xl border border-zinc-200 px-3 py-2 disabled:opacity-40 dark:border-zinc-700"
                  >
                    Prev
                  </button>
                  <span>Page {filters.page}/{totalSectionPages} · {sectionTotal} total</span>
                  <button
                    type="button"
                    disabled={filters.page >= totalSectionPages || isLoading}
                    onClick={() => setFilters((current) => ({ ...current, page: Math.min(totalSectionPages, current.page + 1) }))}
                    className="rounded-xl border border-zinc-200 px-3 py-2 disabled:opacity-40 dark:border-zinc-700"
                  >
                    Next
                  </button>
                </div>
              </div>

              <div className="rounded-[26px] border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950">
                <div className="mb-3 flex items-center justify-between gap-3 px-2">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Units</p>
                    <p className="mt-1 text-xs font-semibold text-zinc-500">{selectedLevel ? selectedLevel.title : "Select a section"}</p>
                  </div>
                  <button
                    type="button"
                    disabled={!selectedLevelId}
                    onClick={() => openModal("lesson")}
                    className="rounded-xl bg-primary px-3 py-2 text-xs font-black text-white disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Add Unit
                  </button>
                </div>
                <div className="space-y-2">
                  {!selectedLevelId && <EmptyState>Select a section first.</EmptyState>}
                  {sectionDetailError && <div className="rounded-[18px] bg-rose-50 px-3 py-3 text-xs font-bold text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{sectionDetailError}</div>}
                  {loadingSectionId === selectedLevelId && !sectionDetailCache[selectedLevelId] && <CurriculumTreeSkeleton />}
                  {selectedLevelId && sectionDetailCache[selectedLevelId] && selectedLessons.length === 0 && <EmptyState>No units in this section yet.</EmptyState>}
                  {selectedLessons.map((lesson, lessonIndex) => (
                    <div
                      key={lesson.id}
                      role="button"
                      tabIndex={0}
                      data-testid={`curriculum-lesson-row-${lesson.id}`}
                      onClick={() => selectLessonNode(selectedLevelId, lesson.id)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") selectLessonNode(selectedLevelId, lesson.id);
                      }}
                      className={`flex w-full items-start justify-between gap-3 rounded-[18px] px-3 py-3 text-left transition ${
                        selectedLessonId === lesson.id ? "bg-primary/10 text-primary dark:text-white" : "bg-white hover:bg-zinc-100 dark:bg-zinc-900 dark:hover:bg-zinc-800"
                      }`}
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-black">{lessonIndex + 1}. {lesson.title}</p>
                        <p className="mt-1 truncate text-xs font-semibold text-zinc-500 dark:text-zinc-400">{lesson.xp_reward || 0} XP ? {lesson.coin_reward || 0} coins ? {(lesson.exercises || []).length} lessons</p>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-2">
                        <StatusBadge isActive={lesson.is_active}>{lesson.is_active ? "Active" : "Inactive"}</StatusBadge>
                        <RowActions item={lesson} kind="lesson" items={selectedLessons} onEdit={() => openModal("lesson", lesson)} onToggle={() => toggleActive("lesson", lesson)} onMove={moveItem} disabled={isReordering} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[26px] border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950">
                <div className="mb-3 flex items-center justify-between gap-3 px-2">
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Lessons</p>
                    <p className="mt-1 text-xs font-semibold text-zinc-500">{selectedLesson ? selectedLesson.title : "Select a unit"}</p>
                  </div>
                  <button
                    type="button"
                    disabled={!selectedLessonId}
                    onClick={() => openModal("exercise")}
                    className="rounded-xl bg-primary px-3 py-2 text-xs font-black text-white disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Add Lesson
                  </button>
                </div>
                <div className="space-y-2">
                  {!selectedLessonId && <EmptyState>Select a unit first.</EmptyState>}
                  {selectedLessonId && selectedExercises.length === 0 && <EmptyState>No lessons in this unit yet.</EmptyState>}
                  {selectedExercises.map((exercise, exerciseIndex) => (
                    <div
                      key={exercise.id}
                      role="button"
                      tabIndex={0}
                      data-testid={`curriculum-exercise-row-${exercise.id}`}
                      onClick={() => selectExerciseNode(selectedLevelId, selectedLessonId, exercise.id)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") selectExerciseNode(selectedLevelId, selectedLessonId, exercise.id);
                      }}
                      className={`flex w-full items-start justify-between gap-3 rounded-[18px] px-3 py-3 text-left transition ${
                        selectedExerciseId === exercise.id ? "bg-primary/10 text-primary dark:text-white" : "bg-white hover:bg-zinc-100 dark:bg-zinc-900 dark:hover:bg-zinc-800"
                      }`}
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-black">{exerciseIndex + 1}. {exercise.title}</p>
                        <p className="mt-1 truncate text-xs font-semibold text-zinc-500 dark:text-zinc-400">{exercise.type} ? pass {exercise.pass_score}</p>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-2">
                        <StatusBadge isActive={exercise.is_active}>{exercise.is_active ? "Active" : "Inactive"}</StatusBadge>
                        <RowActions item={exercise} kind="exercise" items={selectedExercises} onEdit={() => openModal("exercise", exercise)} onToggle={() => toggleActive("exercise", exercise)} onMove={moveItem} disabled={isReordering} canMove />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <p className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">
          Lesson audio is generated by backend TTS or uploaded directly by admins.
        </p>
      </div>

      {modal && form && (
        <EntityModal
          kind={modal.kind}
          form={form}
          setForm={setForm}
          onClose={closeModal}
          onSubmit={handleSubmit}
          isSaving={isSaving}
          levels={levels}
          lessons={allLessons}
          scenarios={scenarios}
          onNeedScenarios={loadScenarios}
          editingItem={modal.item}
        />
      )}
    </AdminShell>
  );
};

const PanelHeader = ({ eyebrow, title, actionLabel, actionTestId, onAction, onRefresh, disabled = false }) => (
  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
    <div className="min-w-0">
      <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">{eyebrow}</p>
      <h2 className="mt-1 truncate font-display text-2xl font-black tracking-tight">{title}</h2>
    </div>
    <div className="flex gap-2">
      {onRefresh ? (
        <button
          type="button"
          onClick={() => {
            void onRefresh();
          }}
          className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-zinc-200 text-zinc-600 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          aria-label="Refresh"
        >
          <ArrowClockwise size={16} />
        </button>
      ) : null}
      <button
        type="button"
        data-testid={actionTestId}
        onClick={onAction}
        disabled={disabled}
        className="inline-flex items-center justify-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-black text-white shadow-lg shadow-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Plus size={16} />
        {actionLabel}
      </button>
    </div>
  </div>
);

export default AdminCurriculumPage;


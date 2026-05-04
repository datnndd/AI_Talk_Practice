import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowClockwise,
  ArrowDown,
  ArrowUp,
  CheckCircle,
  Code,
  FloppyDiskBack,
  Gift,
  GraduationCap,
  MagicWand,
  PencilSimple,
  Plus,
  ProhibitInset,
  Robot,
  SpeakerHigh,
  SquaresFour,
  UserList,
  X,
} from "@phosphor-icons/react";

import { adminApi } from "@/features/admin-scenarios/api/adminScenariosApi";
import AdminShell from "@/features/admin-scenarios/components/AdminShell";
import { adminCurriculumApi } from "@/features/curriculum/api/curriculumApi";
import { getApiBaseUrl } from "@/shared/api/httpClient";

const EMPTY_CONTENT = {
  vocab_pronunciation: {
    words: [{ word: "hello", meaning_vi: "xin chao" }],
  },
  cloze_dictation: {
    passage: "I would like a ___, please.",
    blanks: [
      {
        answer: "coffee",
        accepted_answers: ["coffee"],
        meaning_vi: "ca phe",
        explanation_vi: "A drink noun.",
      },
    ],
  },
  sentence_pronunciation: {
    reference_text: "Could you help me with my reservation?",
  },
  interactive_conversation: {
    scenario_id: 1,
  },
  word_audio_choice: {
    prompt_word: "reservation",
    language: "en",
    options: [
      { word: "reservation", is_correct: true },
      { word: "reception", is_correct: false },
      { word: "recommendation", is_correct: false },
    ],
  },
};

const EXERCISE_TYPES = [
  { value: "vocab_pronunciation", label: "Vocabulary pronunciation" },
  { value: "cloze_dictation", label: "Cloze dictation" },
  { value: "sentence_pronunciation", label: "Sentence pronunciation" },
  { value: "interactive_conversation", label: "Interactive conversation" },
  { value: "word_audio_choice", label: "Word audio choice" },
];

const pretty = (value) => JSON.stringify(value || {}, null, 2);

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
  sortedByOrder(sections).map((section) => ({
    ...section,
    lessons: sortedByOrder(section.units || []).map((unit) => ({
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

const toLevelForm = (level, nextOrder) => ({
  code: level?.code || "",
  title: level?.title || "",
  cefr_level: level?.cefr_level || "",
  description: level?.description || "",
  order_index: level?.order_index ?? nextOrder,
  is_active: level?.is_active ?? true,
});

const toLessonForm = (lesson, selectedLevelId, nextOrder) => ({
  level_id: lesson?.level_id ?? selectedLevelId ?? "",
  title: lesson?.title || "",
  description: lesson?.description || "",
  order_index: lesson?.order_index ?? nextOrder,
  xp_reward: lesson?.xp_reward ?? 50,
  coin_reward: lesson?.coin_reward ?? 0,
  is_active: lesson?.is_active ?? true,
});

const toExerciseForm = (exercise, selectedLessonId, nextOrder) => {
  const type = exercise?.type || "vocab_pronunciation";
  const content = exercise?.content || EMPTY_CONTENT[type];
  return {
    lesson_id: exercise?.lesson_id ?? selectedLessonId ?? "",
    type,
    title: exercise?.title || `Lesson ${nextOrder + 1}`,
    order_index: exercise?.order_index ?? nextOrder,
    pass_score: exercise?.pass_score ?? 80,
    is_required: exercise?.is_required ?? true,
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
  order_index: parseNumber(form.order_index),
  is_active: Boolean(form.is_active),
});

const normalizeLessonPayload = (form) => ({
  section_id: parseNumber(form.level_id),
  title: form.title.trim(),
  description: form.description.trim() || null,
  order_index: parseNumber(form.order_index),
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
  is_required: Boolean(form.is_required),
  is_active: Boolean(form.is_active),
  content: JSON.parse(form.contentJson || "{}"),
});

const audioOptionsToText = (content) =>
  (content.options || [])
    .map((option) => `${option.is_correct ? "*" : ""}${option.word || ""}${option.audio_url ? ` | ${option.audio_url}` : ""}`)
    .join("\n");

const textToAudioChoice = (promptWord, language, value) => ({
  prompt_word: promptWord,
  language: language || "en",
  options: value
    .split(/\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const isCorrect = line.startsWith("*");
      const cleanLine = isCorrect ? line.slice(1).trim() : line;
      const [word, audioUrl] = cleanLine.split("|").map((item) => item.trim());
      return { word, is_correct: isCorrect, ...(audioUrl ? { audio_url: audioUrl } : {}) };
    }),
});

const normalizeVocabRows = (content = {}) => {
  const rows = Array.isArray(content.words) ? content.words : [];
  const normalized = rows.map((item) => {
    if (typeof item === "string") {
      return { word: item, meaning_vi: "", ipa: "", audio_url: "" };
    }
    return {
      word: item?.word || "",
      meaning_vi: item?.meaning_vi || "",
      ipa: item?.ipa || "",
      audio_url: item?.audio_url || "",
    };
  });
  return normalized.length > 0 ? normalized : [{ word: "", meaning_vi: "", ipa: "", audio_url: "" }];
};

const rowsToVocabContent = (rows) => ({
  words: rows
    .map((row) => ({
      word: row.word.trim(),
      ...(row.meaning_vi?.trim() ? { meaning_vi: row.meaning_vi.trim() } : {}),
      ...(row.ipa?.trim() ? { ipa: row.ipa.trim() } : {}),
      ...(row.audio_url?.trim() ? { audio_url: row.audio_url.trim() } : {}),
    }))
    .filter((row) => row.word),
});

const normalizeClozeRows = (content = {}) => {
  const rows = Array.isArray(content.blanks) ? content.blanks : [];
  const normalized = rows.map((blank) => ({
    answer: blank?.answer || "",
    accepted_answers: Array.isArray(blank?.accepted_answers)
      ? blank.accepted_answers.join(", ")
      : blank?.accepted_answers || "",
    meaning_vi: blank?.meaning_vi || "",
    explanation_vi: blank?.explanation_vi || "",
  }));
  return normalized.length > 0
    ? normalized
    : [{ answer: "", accepted_answers: "", meaning_vi: "", explanation_vi: "" }];
};

const rowsToClozeContent = (content, rows) => ({
  ...content,
  blanks: rows
    .map((row) => {
      const answer = row.answer.trim();
      const accepted = row.accepted_answers
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
      return {
        answer,
        accepted_answers: accepted.length > 0 ? accepted : [answer],
        ...(row.meaning_vi?.trim() ? { meaning_vi: row.meaning_vi.trim() } : {}),
        ...(row.explanation_vi?.trim() ? { explanation_vi: row.explanation_vi.trim() } : {}),
      };
    })
    .filter((row) => row.answer),
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

const VocabWordsEditor = ({ content, onChange, lessonId = "" }) => {
  const rows = normalizeVocabRows(content);
  const [rowState, setRowState] = useState({});

  const updateRows = (nextRows) => onChange(rowsToVocabContent(nextRows));
  const updateRow = (index, patch) => {
    updateRows(rows.map((row, rowIndex) => (rowIndex === index ? { ...row, ...patch } : row)));
  };
  const setLookupState = (index, patch) => {
    setRowState((current) => ({ ...current, [index]: { ...(current[index] || {}), ...patch } }));
  };
  const lookupWord = async (index, field) => {
    const word = rows[index]?.word?.trim();
    if (!word) {
      setLookupState(index, { error: "Nhập từ tiếng Anh trước." });
      return;
    }

    setLookupState(index, { loading: field, error: "" });
    try {
      const result = await adminCurriculumApi.lookupDictionary({ word, lang: "en", defLang: "vi" });
      const patch = {
        ...(result.ipa ? { ipa: result.ipa } : {}),
      };
      if (field === "meaning") {
        patch.meaning_vi = result.meaning_vi || result.definitions?.[0] || "";
      }
      if (field === "audio") {
        patch.audio_url = result.audio_url || `/api/curriculum/dictionary/audio?word=${encodeURIComponent(word)}&lang=en`;
      }
      updateRow(index, patch);
    } catch (error) {
      setLookupState(index, { error: getErrorMessage(error, "Không thể lấy dữ liệu từ điển.") });
    } finally {
      setLookupState(index, { loading: "" });
    }
  };

  return (
    <div className="space-y-3">
      <div className="grid gap-2 rounded-[20px] border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-700 dark:bg-zinc-950">
        <div className="hidden grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_minmax(0,1.15fr)_40px] gap-2 px-1 text-[10px] font-black uppercase tracking-[0.18em] text-zinc-500 md:grid">
          <span>English word</span>
          <span>Vietnamese meaning</span>
          <span>Audio</span>
          <span />
        </div>
        {rows.map((row, index) => {
          const state = rowState[index] || {};
          return (
            <div
              key={index}
              className="grid gap-2 rounded-[18px] border border-zinc-200 bg-white p-2 dark:border-zinc-800 dark:bg-zinc-900 md:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_minmax(0,1.15fr)_40px]"
            >
              <div>
                <FieldLabel>English</FieldLabel>
                <input
                  data-testid={`vocab-word-input-${index}`}
                  value={row.word}
                  onChange={(event) => updateRow(index, { word: event.target.value })}
                  placeholder="reservation"
                  className="w-full rounded-[16px] border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                />
              </div>
              <div>
                <div className="mb-2 flex items-center justify-between gap-2">
                  <FieldLabel>Meaning VI</FieldLabel>
                  <button
                    type="button"
                    onClick={() => lookupWord(index, "meaning")}
                    disabled={state.loading === "meaning"}
                    className="inline-flex items-center gap-1 rounded-full border border-zinc-200 px-2 py-1 text-[11px] font-black text-zinc-700 hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                  >
                    <MagicWand size={13} />
                    {state.loading === "meaning" ? "Đang lấy" : "Lấy nghĩa"}
                  </button>
                </div>
                <input
                  data-testid={`vocab-meaning-input-${index}`}
                  value={row.meaning_vi}
                  onChange={(event) => updateRow(index, { meaning_vi: event.target.value })}
                  placeholder="sự đặt trước"
                  className="w-full rounded-[16px] border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                />
              </div>
              <div>
                <FieldLabel>Audio</FieldLabel>
                <AudioAssetControl
                  compact
                  value={row.audio_url}
                  text={row.word}
                  language="en"
                  lessonId={lessonId}
                  onChange={(audioUrl) => updateRow(index, { audio_url: audioUrl })}
                />
                {state.error ? <p className="mt-2 text-xs font-semibold text-rose-600 dark:text-rose-300">{state.error}</p> : null}
              </div>
              <button
                type="button"
                onClick={() => updateRows(rows.filter((_, rowIndex) => rowIndex !== index))}
                className="inline-flex h-10 w-10 items-center justify-center rounded-[14px] border border-zinc-200 text-zinc-500 hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800 md:self-end"
                aria-label="Remove word"
              >
                <X size={16} />
              </button>
            </div>
          );
        })}
      </div>
      <button
        type="button"
        onClick={() => updateRows([...rows, { word: "", meaning_vi: "", ipa: "", audio_url: "" }])}
        className="inline-flex items-center gap-2 rounded-2xl border border-zinc-200 px-4 py-2 text-sm font-black text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
      >
        <Plus size={16} />
        Add word
      </button>
    </div>
  );
};

const ClozeDictationEditor = ({ content, onChange, lessonId = "" }) => {
  const rows = normalizeClozeRows(content);
  const [rowState, setRowState] = useState({});

  const updateContent = (patch) => onChange({ ...content, ...patch });
  const updateRows = (nextRows) => onChange(rowsToClozeContent(content, nextRows));
  const updateRow = (index, patch) => {
    updateRows(rows.map((row, rowIndex) => (rowIndex === index ? { ...row, ...patch } : row)));
  };
  const setLookupState = (index, patch) => {
    setRowState((current) => ({ ...current, [index]: { ...(current[index] || {}), ...patch } }));
  };
  const lookupMeaning = async (index) => {
    const answer = rows[index]?.answer?.trim();
    if (!answer) {
      setLookupState(index, { error: "Nhập đáp án trước." });
      return;
    }

    setLookupState(index, { loading: true, error: "" });
    try {
      const result = await adminCurriculumApi.lookupDictionary({ word: answer, lang: "en", defLang: "vi" });
      updateRow(index, { meaning_vi: result.meaning_vi || result.definitions?.[0] || "" });
    } catch (error) {
      setLookupState(index, { error: getErrorMessage(error, "Không thể lấy nghĩa từ điển.") });
    } finally {
      setLookupState(index, { loading: false });
    }
  };
  const syncRowsToPassage = () => {
    const blankCount = (content.passage?.match(/_{3,}/g) || []).length;
    if (blankCount <= rows.length) return;
    updateRows([
      ...rows,
      ...Array.from({ length: blankCount - rows.length }, () => ({
        answer: "",
        accepted_answers: "",
        meaning_vi: "",
        explanation_vi: "",
      })),
    ]);
  };

  return (
    <div className="space-y-4">
      <div>
        <FieldLabel>Passage</FieldLabel>
        <textarea
          value={content.passage || ""}
          onChange={(event) => updateContent({ passage: event.target.value })}
          placeholder="I would like a ___, please."
          className="min-h-[110px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
        />
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={syncRowsToPassage}
            className="rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-black text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
          >
            Match ___ blanks
          </button>
          <p className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">
            Dùng <span className="font-mono">___</span> trong passage để đánh dấu chỗ trống.
          </p>
        </div>
      </div>

      <div>
        <FieldLabel>Prompt Audio</FieldLabel>
        <AudioAssetControl
          value={content.audio_url || ""}
          text={content.passage || ""}
          language={content.language || "en"}
          lessonId={lessonId}
          onChange={(audioUrl) => updateContent({ audio_url: audioUrl })}
        />
      </div>

      <div>
        <FieldLabel>Blank Answers</FieldLabel>
        <div className="grid gap-2 rounded-[20px] border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-700 dark:bg-zinc-950">
          <div className="hidden grid-cols-[minmax(0,0.85fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_40px] gap-2 px-1 text-[10px] font-black uppercase tracking-[0.18em] text-zinc-500 md:grid">
            <span>Answer</span>
            <span>Accepted answers</span>
            <span>Meaning VI</span>
            <span>Explanation</span>
            <span />
          </div>
          {rows.map((row, index) => {
            const state = rowState[index] || {};
            return (
              <div
                key={index}
                className="grid gap-2 rounded-[18px] border border-zinc-200 bg-white p-2 dark:border-zinc-800 dark:bg-zinc-900 md:grid-cols-[minmax(0,0.85fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_40px]"
              >
                <div>
                  <FieldLabel>Answer</FieldLabel>
                  <input
                    data-testid={`cloze-answer-input-${index}`}
                    value={row.answer}
                    onChange={(event) => updateRow(index, { answer: event.target.value })}
                    placeholder="coffee"
                    className="w-full rounded-[16px] border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                  />
                </div>
                <div>
                  <FieldLabel>Accepted</FieldLabel>
                  <input
                    value={row.accepted_answers}
                    onChange={(event) => updateRow(index, { accepted_answers: event.target.value })}
                    placeholder="coffee, cafe"
                    className="w-full rounded-[16px] border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                  />
                </div>
                <div>
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <FieldLabel>Meaning VI</FieldLabel>
                    <button
                      type="button"
                      onClick={() => lookupMeaning(index)}
                      disabled={state.loading}
                      className="inline-flex items-center gap-1 rounded-full border border-zinc-200 px-2 py-1 text-[11px] font-black text-zinc-700 hover:bg-zinc-100 disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                    >
                      <MagicWand size={13} />
                      {state.loading ? "Đang lấy" : "Lấy nghĩa"}
                    </button>
                  </div>
                  <input
                    data-testid={`cloze-meaning-input-${index}`}
                    value={row.meaning_vi}
                    onChange={(event) => updateRow(index, { meaning_vi: event.target.value })}
                    placeholder="cà phê"
                    className="w-full rounded-[16px] border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                  />
                  {state.error ? <p className="mt-2 text-xs font-semibold text-rose-600 dark:text-rose-300">{state.error}</p> : null}
                </div>
                <div>
                  <FieldLabel>Explanation</FieldLabel>
                  <input
                    value={row.explanation_vi}
                    onChange={(event) => updateRow(index, { explanation_vi: event.target.value })}
                    placeholder="Danh từ chỉ đồ uống."
                    className="w-full rounded-[16px] border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => updateRows(rows.filter((_, rowIndex) => rowIndex !== index))}
                  className="inline-flex h-10 w-10 items-center justify-center rounded-[14px] border border-zinc-200 text-zinc-500 hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800 md:self-end"
                  aria-label="Remove blank"
                >
                  <X size={16} />
                </button>
              </div>
            );
          })}
        </div>
        <button
          type="button"
          onClick={() => updateRows([...rows, { answer: "", accepted_answers: "", meaning_vi: "", explanation_vi: "" }])}
          className="mt-3 inline-flex items-center gap-2 rounded-2xl border border-zinc-200 px-4 py-2 text-sm font-black text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
        >
          <Plus size={16} />
          Add blank
        </button>
      </div>
    </div>
  );
};

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

  useEffect(() => {
    if (form.type === "interactive_conversation") {
      void onNeedScenarios?.();
    }
  }, [form.type, onNeedScenarios]);

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
      <BaseControls form={form} updateForm={updateForm} />
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
      <BaseControls form={form} updateForm={updateForm} />
    </>
  );

  const renderExerciseBuilder = () => {
    const content = form.content || {};

    if (form.type === "vocab_pronunciation") {
      return (
        <div>
          <FieldLabel>Words</FieldLabel>
          <VocabWordsEditor content={content} onChange={updateExerciseContent} lessonId={form.lesson_id} />
        </div>
      );
    }

    if (form.type === "cloze_dictation") {
      return (
        <ClozeDictationEditor content={content} onChange={updateExerciseContent} lessonId={form.lesson_id} />
      );
    }

    if (form.type === "sentence_pronunciation") {
      return (
        <div className="space-y-4">
          <div>
            <FieldLabel>Reference Text</FieldLabel>
            <textarea
              value={content.reference_text || ""}
              onChange={(event) => updateExerciseContent({ ...content, reference_text: event.target.value })}
              className="min-h-[130px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-medium outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
            />
          </div>
          <div>
            <FieldLabel>Sample Audio</FieldLabel>
            <AudioAssetControl
              value={content.sample_audio_url || ""}
              text={content.reference_text || ""}
              language={content.language || "en"}
              lessonId={form.lesson_id}
              onChange={(audioUrl) => updateExerciseContent({ ...content, sample_audio_url: audioUrl })}
            />
          </div>
        </div>
      );
    }

    if (form.type === "word_audio_choice") {
      return (
        <>
          <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_120px]">
            <div>
              <FieldLabel>Prompt Word</FieldLabel>
              <input
                value={content.prompt_word || ""}
                onChange={(event) => updateExerciseContent({ ...content, prompt_word: event.target.value })}
                className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
              />
            </div>
            <div>
              <FieldLabel>Language</FieldLabel>
              <input
                value={content.language || "en"}
                onChange={(event) => updateExerciseContent({ ...content, language: event.target.value })}
                className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
              />
            </div>
          </div>
          <div>
            <FieldLabel>Audio Options</FieldLabel>
            <textarea
              value={audioOptionsToText(content)}
              onChange={(event) => updateExerciseContent(textToAudioChoice(content.prompt_word || "", content.language || "en", event.target.value))}
              placeholder={"*reservation\nreception\nrecommendation"}
              className="min-h-[150px] w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 font-mono text-xs outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
            />
            <p className="mt-2 text-xs font-semibold text-zinc-500 dark:text-zinc-400">
              Prefix exactly one correct option with *. Generate or upload audio below to set Supabase URLs.
            </p>
            <div className="mt-3 space-y-3">
              {(content.options || []).map((option, index) => (
                <div key={`${option.word}-${index}`} className="rounded-[18px] border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-700 dark:bg-zinc-950">
                  <FieldLabel>{option.is_correct ? "Correct" : "Option"}: {option.word}</FieldLabel>
                  <AudioAssetControl
                    value={option.audio_url || ""}
                    text={option.word || content.prompt_word || ""}
                    language={content.language || "en"}
                    lessonId={form.lesson_id}
                    onChange={(audioUrl) => updateExerciseContent({
                      ...content,
                      options: (content.options || []).map((currentOption, optionIndex) => (
                        optionIndex === index ? { ...currentOption, audio_url: audioUrl } : currentOption
                      )),
                    })}
                  />
                </div>
              ))}
            </div>
          </div>
        </>
      );
    }

    return (
      <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_160px]">
        <div>
          <FieldLabel>Scenario</FieldLabel>
          <select
            value={String(content.scenario_id || "")}
            onChange={(event) => updateExerciseContent({ scenario_id: parseNumber(event.target.value) })}
            className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
          >
            <option value="">Manual ID</option>
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                #{scenario.id} - {scenario.title}
              </option>
            ))}
          </select>
        </div>
        <div>
          <FieldLabel>Scenario ID</FieldLabel>
          <input
            data-testid="scenario-id-input"
            type="number"
            min="1"
            value={content.scenario_id || ""}
            onChange={(event) => updateExerciseContent({ scenario_id: parseNumber(event.target.value) })}
            className="w-full rounded-[20px] border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm font-semibold outline-none focus:border-primary dark:border-zinc-700 dark:bg-zinc-950"
          />
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
              if (type === "interactive_conversation") {
                void onNeedScenarios?.();
              }
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
      <div className="grid gap-4 sm:grid-cols-4">
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
        <ToggleField label="Required" checked={form.is_required} onChange={(value) => updateForm({ is_required: value })} />
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

const BaseControls = ({ form, updateForm }) => (
  <div className="grid gap-4 sm:grid-cols-2">
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
    <ToggleField label="Active" checked={form.is_active} onChange={(value) => updateForm({ is_active: value })} />
  </div>
);

const AdminCurriculumPage = () => {
  const [levels, setLevels] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [hasLoadedScenarios, setHasLoadedScenarios] = useState(false);
  const [selectedLevelId, setSelectedLevelId] = useState(null);
  const [selectedLessonId, setSelectedLessonId] = useState(null);
  const [selectedExerciseId, setSelectedExerciseId] = useState(null);
  const [activeNode, setActiveNode] = useState(null);
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isReordering, setIsReordering] = useState(false);
  const [loadingExerciseId, setLoadingExerciseId] = useState(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const selectedLevel = useMemo(() => levels.find((item) => item.id === selectedLevelId) || null, [levels, selectedLevelId]);
  const selectedLessons = useMemo(() => sortedByOrder(selectedLevel?.lessons || []), [selectedLevel]);
  const selectedLesson = useMemo(
    () => selectedLessons.find((item) => item.id === selectedLessonId) || null,
    [selectedLessons, selectedLessonId],
  );
  const selectedExercises = useMemo(() => sortedByOrder(selectedLesson?.exercises || []), [selectedLesson]);
  const selectedExercise = useMemo(
    () => selectedExercises.find((item) => item.id === selectedExerciseId) || null,
    [selectedExercises, selectedExerciseId],
  );
  const allLessons = useMemo(() => levels.flatMap((level) => level.lessons || []), [levels]);

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
  }, []);

  const loadExerciseDetail = useCallback(
    async (exercise) => {
      if (!exercise || hasLessonContent(exercise)) {
        return exercise;
      }
      setLoadingExerciseId(exercise.id);
      try {
        const detail = normalizeExerciseNode(await adminCurriculumApi.getLesson(exercise.id));
        replaceExercise(exercise.id, detail);
        return detail;
      } catch (detailError) {
        setError(getErrorMessage(detailError, "Failed to load lesson content."));
        return exercise;
      } finally {
        setLoadingExerciseId(null);
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
      const response = await adminCurriculumApi.listSections();
      const ordered = normalizeSectionTree(response);
      setLevels(ordered);
      setSelectedLevelId((current) => (current && ordered.some((item) => item.id === current) ? current : ordered[0]?.id || null));
    } catch (loadError) {
      setError(getErrorMessage(loadError, "Failed to load curriculum."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadLevels();
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

  useEffect(() => {
    if (selectedExercise && !hasLessonContent(selectedExercise)) {
      void loadExerciseDetail(selectedExercise);
    }
  }, [loadExerciseDetail, selectedExercise]);

  const openModal = async (kind, item = null) => {
    const nextLevelOrder = levels.length;
    const nextLessonOrder = selectedLessons.length;
    const nextExerciseOrder = selectedExercises.length;
    let modalItem = item;

    if (kind === "level") {
      setForm(toLevelForm(modalItem, nextLevelOrder));
    } else if (kind === "lesson") {
      setForm(toLessonForm(modalItem, selectedLevelId, nextLessonOrder));
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
      await loadLevels();
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
      await loadLevels();
    } catch (toggleError) {
      setError(getErrorMessage(toggleError, `Failed to update ${curriculumKindLabel(kind)}.`));
    }
  };

  const moveItem = async (kind, items, itemId, direction) => {
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
      if (kind === "level") {
        await adminCurriculumApi.reorderSections(payload);
      } else if (kind === "lesson") {
        await adminCurriculumApi.reorderUnits(payload);
      } else {
        await adminCurriculumApi.reorderLessons(payload);
      }
      setNotice(`${curriculumKindLabel(kind)} order updated.`);
      await loadLevels();
    } catch (reorderError) {
      setError(getErrorMessage(reorderError, `Failed to reorder ${curriculumKindLabel(kind)}.`));
    } finally {
      setIsReordering(false);
    }
  };

  const selectLevelNode = (levelId) => {
    setSelectedLevelId(levelId);
    setActiveNode({ kind: "level", id: levelId });
  };

  const selectLessonNode = (levelId, lessonId) => {
    setSelectedLevelId(levelId);
    setSelectedLessonId(lessonId);
    setActiveNode({ kind: "lesson", id: lessonId });
  };

  const selectExerciseNode = (levelId, lessonId, exerciseId) => {
    setSelectedLevelId(levelId);
    setSelectedLessonId(lessonId);
    setSelectedExerciseId(exerciseId);
    setActiveNode({ kind: "exercise", id: exerciseId });
  };

  const activeItem =
    activeNode?.kind === "level"
      ? levels.find((level) => level.id === activeNode.id) || null
      : activeNode?.kind === "lesson"
        ? allLessons.find((lesson) => lesson.id === activeNode.id) || null
        : activeNode?.kind === "exercise"
          ? allLessons.flatMap((lesson) => lesson.exercises || []).find((exercise) => exercise.id === activeNode.id) || null
          : null;

  const activeParentLesson =
    activeNode?.kind === "exercise"
      ? allLessons.find((lesson) => (lesson.exercises || []).some((exercise) => exercise.id === activeNode.id)) || null
      : null;

  const activeKindLabel = activeNode ? curriculumKindLabel(activeNode.kind) : "item";

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
              eyebrow="Curriculum Tree"
              title="Sections, units, lessons"
              actionLabel="New Section"
              actionTestId="new-section-button"
              onAction={() => openModal("level")}
              onRefresh={loadLevels}
            />

            <div className="mt-5 space-y-3">
              {isLoading && <EmptyState>Loading curriculum...</EmptyState>}
              {!isLoading && levels.length === 0 && <EmptyState>No sections created yet.</EmptyState>}
              {!isLoading && levels.map((level, levelIndex) => (
                <div key={level.id} className="rounded-[24px] border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950">
                  <button
                    type="button"
                    data-testid={`curriculum-level-row-${level.id}`}
                    onClick={() => selectLevelNode(level.id)}
                    className={`flex w-full items-start justify-between gap-3 rounded-[18px] px-3 py-3 text-left transition ${
                      activeNode?.kind === "level" && activeNode.id === level.id
                        ? "bg-primary/10 text-primary dark:text-white"
                        : "hover:bg-white dark:hover:bg-zinc-900"
                    }`}
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-black">{levelIndex + 1}. {level.title}</p>
                      <p className="mt-1 truncate text-xs font-semibold text-zinc-500 dark:text-zinc-400">
                        {level.cefr_level || level.code} ? {(level.lessons || []).length} units
                      </p>
                    </div>
                    <StatusBadge isActive={level.is_active}>{level.is_active ? "Active" : "Inactive"}</StatusBadge>
                  </button>

                  <div className="mt-2 space-y-2 border-l border-zinc-200 pl-4 dark:border-zinc-800">
                    {sortedByOrder(level.lessons || []).map((lesson, lessonIndex) => (
                      <div key={lesson.id}>
                        <button
                          type="button"
                          data-testid={`curriculum-lesson-row-${lesson.id}`}
                          onClick={() => selectLessonNode(level.id, lesson.id)}
                          className={`flex w-full items-start justify-between gap-3 rounded-[18px] px-3 py-2 text-left transition ${
                            activeNode?.kind === "lesson" && activeNode.id === lesson.id
                              ? "bg-primary/10 text-primary dark:text-white"
                              : "hover:bg-white dark:hover:bg-zinc-900"
                          }`}
                        >
                          <div className="min-w-0">
                            <p className="truncate text-sm font-bold">{levelIndex + 1}.{lessonIndex + 1} {lesson.title}</p>
                            <p className="mt-1 truncate text-xs font-semibold text-zinc-500 dark:text-zinc-400">
                              {lesson.xp_reward || 0} XP ? {lesson.coin_reward || 0} coins ? {(lesson.exercises || []).length} lessons
                            </p>
                          </div>
                          <StatusBadge isActive={lesson.is_active}>{lesson.is_active ? "Active" : "Inactive"}</StatusBadge>
                        </button>

                        <div className="mt-1 space-y-1 border-l border-zinc-200 pl-4 dark:border-zinc-800">
                          {sortedByOrder(lesson.exercises || []).map((exercise, exerciseIndex) => (
                            <button
                              key={exercise.id}
                              type="button"
                              data-testid={`curriculum-exercise-row-${exercise.id}`}
                              onClick={() => selectExerciseNode(level.id, lesson.id, exercise.id)}
                              className={`flex w-full items-start justify-between gap-3 rounded-[16px] px-3 py-2 text-left transition ${
                                activeNode?.kind === "exercise" && activeNode.id === exercise.id
                                  ? "bg-primary/10 text-primary dark:text-white"
                                  : "hover:bg-white dark:hover:bg-zinc-900"
                              }`}
                            >
                              <div className="min-w-0">
                                <p className="truncate text-xs font-black">
                                  {levelIndex + 1}.{lessonIndex + 1}.{exerciseIndex + 1} {exercise.title}
                                </p>
                                <p className="mt-1 truncate text-[11px] font-semibold text-zinc-500 dark:text-zinc-400">
                                  {exercise.type} ? pass {exercise.pass_score}
                                </p>
                              </div>
                              <StatusBadge isActive={exercise.is_active}>{exercise.is_active ? "Active" : "Inactive"}</StatusBadge>
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className={`fixed inset-y-0 right-0 z-50 w-full max-w-3xl overflow-y-auto border-l border-zinc-200 bg-zinc-50 p-4 shadow-2xl transition-transform duration-300 dark:border-zinc-800 dark:bg-zinc-950 ${activeNode ? "translate-x-0" : "translate-x-full"}`}>
            <div className="mb-4 rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">{activeKindLabel} Detail</p>
                  <h2 className="mt-1 truncate text-2xl font-black">{activeItem?.title || "Select a curriculum item"}</h2>
                  <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
                    Tree stays visible while this drawer handles editing, ordering, and preview.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveNode(null)}
                  className="rounded-2xl border border-zinc-200 p-3 text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                  aria-label="Close curriculum detail"
                >
                  <X size={18} />
                </button>
              </div>
            </div>

            {!activeItem && <EmptyState>Select a section, unit, or lesson from the tree.</EmptyState>}

            {activeItem && (
              <div className="space-y-4">
                <div className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">Overview</p>
                      <h3 className="mt-2 text-xl font-black">{activeItem.title}</h3>
                      <p className="mt-2 text-sm leading-6 text-zinc-500 dark:text-zinc-400">
                        {activeItem.description || activeItem.type || activeItem.code || "No description."}
                      </p>
                    </div>
                    <StatusBadge isActive={activeItem.is_active}>{activeItem.is_active ? "Active" : "Inactive"}</StatusBadge>
                  </div>

                  <div className="mt-5 grid gap-3 sm:grid-cols-3">
                    <div className="rounded-[22px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Order</p>
                      <p className="mt-2 text-2xl font-black">{activeItem.order_index ?? 0}</p>
                    </div>
                    <div className="rounded-[22px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Type</p>
                      <p className="mt-2 text-sm font-black capitalize">{activeKindLabel}</p>
                    </div>
                    <div className="rounded-[22px] bg-zinc-50 p-4 dark:bg-zinc-950">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Children</p>
                      <p className="mt-2 text-2xl font-black">
                        {activeNode.kind === "level" ? (activeItem.lessons || []).length : activeNode.kind === "lesson" ? (activeItem.exercises || []).length : 0}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
                  <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Quick Actions</p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <button
                      type="button"
                      onClick={() => openModal(activeNode.kind, activeItem)}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl bg-primary px-4 py-3 text-sm font-black text-white transition hover:-translate-y-0.5"
                    >
                      <PencilSimple size={16} />
                      Edit {activeKindLabel}
                    </button>
                    <button
                      type="button"
                      onClick={() => toggleActive(activeNode.kind, activeItem)}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-black text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                    >
                      <ProhibitInset size={16} />
                      {activeItem.is_active ? "Deactivate" : "Restore"}
                    </button>
                    {activeNode.kind === "level" && (
                      <button
                        type="button"
                        onClick={() => openModal("lesson")}
                        className="inline-flex items-center justify-center gap-2 rounded-2xl border border-primary/20 bg-primary/10 px-4 py-3 text-sm font-black text-primary transition hover:-translate-y-0.5 dark:text-white"
                      >
                        <Plus size={16} />
                        Add Unit
                      </button>
                    )}
                    {activeNode.kind === "lesson" && (
                      <button
                        type="button"
                        onClick={() => openModal("exercise")}
                        className="inline-flex items-center justify-center gap-2 rounded-2xl border border-primary/20 bg-primary/10 px-4 py-3 text-sm font-black text-primary transition hover:-translate-y-0.5 dark:text-white"
                      >
                        <Plus size={16} />
                        Add Lesson
                      </button>
                    )}
                  </div>

                  <ItemActions
                    kind={activeNode.kind}
                    item={activeItem}
                    items={activeNode.kind === "level" ? levels : activeNode.kind === "lesson" ? selectedLessons : selectedExercises}
                    onEdit={() => openModal(activeNode.kind, activeItem)}
                    onToggle={() => toggleActive(activeNode.kind, activeItem)}
                    onMove={moveItem}
                    disabled={isReordering}
                  />
                </div>

                {activeNode.kind === "exercise" && (
                  <div className="rounded-[30px] border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500 dark:text-zinc-400">
                        <Code size={14} />
                        Content Preview
                      </div>
                      {activeParentLesson && <span className="text-xs font-semibold text-zinc-500">Unit: {activeParentLesson.title}</span>}
                    </div>
                    <pre className="mt-3 max-h-[420px] overflow-auto whitespace-pre-wrap break-words rounded-[18px] bg-zinc-950 p-4 font-mono text-xs text-zinc-50">
                      {loadingExerciseId === activeItem.id ? "Loading content..." : pretty(activeItem.content)}
                    </pre>
                  </div>
                )}
              </div>
            )}
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

const ItemActions = ({ kind, item, items, onEdit, onToggle, onMove, disabled }) => {
  if (!item) {
    return null;
  }
  const currentIndex = items.findIndex((entry) => entry.id === item.id);
  return (
    <div className="mt-5 grid gap-2 sm:grid-cols-2">
      <button
        type="button"
        data-testid={`edit-${kind}-button`}
        onClick={onEdit}
        className="inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
      >
        <PencilSimple size={16} />
        Edit
      </button>
      <button
        type="button"
        data-testid={`toggle-${kind}-button`}
        onClick={onToggle}
        className={`inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-black ${
          item.is_active
            ? "border border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-300"
            : "bg-emerald-600 text-white"
        }`}
      >
        {item.is_active ? <ProhibitInset size={16} /> : <CheckCircle size={16} />}
        {item.is_active ? "Deactivate" : "Restore"}
      </button>
      <button
        type="button"
        data-testid={`move-${kind}-up`}
        disabled={disabled || currentIndex <= 0}
        onClick={() => onMove(kind, items, item.id, -1)}
        className="inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
      >
        <ArrowUp size={16} />
        Move Up
      </button>
      <button
        type="button"
        data-testid={`move-${kind}-down`}
        disabled={disabled || currentIndex < 0 || currentIndex >= items.length - 1}
        onClick={() => onMove(kind, items, item.id, 1)}
        className="inline-flex items-center justify-center gap-2 rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
      >
        <ArrowDown size={16} />
        Move Down
      </button>
    </div>
  );
};

export default AdminCurriculumPage;

import { useMemo, useState } from "react";
import { X, Sparkle, ClockCounterClockwise, BracketsCurly, NotePencil } from "@phosphor-icons/react";
import JsonEditorField from "./JsonEditorField";
import ListEditorField from "./ListEditorField";
import PromptQualityBadge from "./PromptQualityBadge";

const prettyJson = (value, fallback) => JSON.stringify(value ?? fallback, null, 2);
const prettyList = (value) => (Array.isArray(value) ? value.join("\n") : "");
const parseListInput = (value = "") =>
  value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);

const STRUCTURED_METADATA_KEYS = [
  "topic",
  "conversation_topic",
  "assigned_task",
  "task",
  "user_goal",
  "goal",
  "persona",
  "partner_persona",
  "evaluation_focus",
  "success_criteria",
  "rubric",
  "suggested_responses",
  "stuck_help",
  "response_hints",
  "end_condition",
  "completion_signal",
  "wrap_up_cue",
  "target_turns",
];

const stripStructuredMetadata = (value) => {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return {};
  }

  return Object.fromEntries(
    Object.entries(value).filter(([key]) => !STRUCTURED_METADATA_KEYS.includes(key)),
  );
};

const metadataString = (metadata, keys) => {
  if (!metadata || typeof metadata !== "object") {
    return "";
  }

  for (const key of keys) {
    const value = metadata[key];
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return "";
};

const metadataList = (metadata, keys) => {
  if (!metadata || typeof metadata !== "object") {
    return [];
  }

  for (const key of keys) {
    const value = metadata[key];
    if (Array.isArray(value)) {
      const items = value
        .map((item) => (typeof item === "string" ? item.trim() : ""))
        .filter(Boolean);
      if (items.length > 0) {
        return items;
      }
    }
    if (typeof value === "string" && value.trim()) {
      return parseListInput(value);
    }
  }

  return [];
};

const PROMPT_STARTER = `You are the speaking partner for this practice scenario.

Stay in character throughout the interaction.
Keep your replies natural, concise, and appropriate to the learner's level.
Encourage the learner to clarify, ask follow-up questions, and complete the task goal.
Correct only important mistakes, and do so briefly without breaking the flow.
End the conversation once the learner reaches the scenario outcome.`;

const createInitialState = (scenario) => ({
  title: scenario?.title || "",
  description: scenario?.description || "",
  category: scenario?.category || "travel",
  difficulty: scenario?.difficulty || "medium",
  ai_system_prompt: scenario?.ai_system_prompt || "",
  estimated_duration_minutes: scenario?.estimated_duration_minutes || 10,
  is_pre_generated: scenario?.is_pre_generated ?? true,
  pre_gen_count: scenario?.pre_gen_count || 8,
  mode: scenario?.mode || "conversation",
  is_active: scenario?.is_active ?? true,
  opening_message: scenario?.opening_message || "",
  is_ai_start_first: scenario?.is_ai_start_first ?? true,
  change_note: "",
  learning_objectives: prettyList(scenario?.learning_objectives),
  target_skills: prettyList(scenario?.target_skills),
  tags: prettyList(scenario?.tags),
  topic: metadataString(scenario?.metadata, ["topic", "conversation_topic"]),
  assigned_task: metadataString(scenario?.metadata, ["assigned_task", "task", "user_goal", "goal"]),
  persona: metadataString(scenario?.metadata, ["persona", "partner_persona"]),
  evaluation_focus: prettyList(metadataList(scenario?.metadata, ["evaluation_focus", "success_criteria", "rubric"])),
  suggested_responses: prettyList(metadataList(scenario?.metadata, ["suggested_responses", "stuck_help", "response_hints"])),
  end_condition: metadataString(scenario?.metadata, ["end_condition", "completion_signal", "wrap_up_cue"]),
  target_turns: scenario?.metadata?.target_turns ? String(scenario.metadata.target_turns) : "",
  metadata: prettyJson(stripStructuredMetadata(scenario?.metadata), {}),
});

const ScenarioEditorModal = ({
  scenario,
  promptHistory = [],
  onClose,
  onSubmit,
  onSuggestSkills,
  isSaving,
}) => {
  const [form, setForm] = useState(() => createInitialState(scenario));
  const [jsonError, setJsonError] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(() => Boolean(scenario?.metadata && Object.keys(scenario.metadata).length));

  const updateField = (field, value) => setForm((current) => ({ ...current, [field]: value }));
  const objectiveCount = useMemo(() => parseListInput(form.learning_objectives).length, [form.learning_objectives]);
  const skillCount = useMemo(() => parseListInput(form.target_skills).length, [form.target_skills]);
  const tagCount = useMemo(() => parseListInput(form.tags).length, [form.tags]);
  const evaluationFocusCount = useMemo(() => parseListInput(form.evaluation_focus).length, [form.evaluation_focus]);
  const responseHintCount = useMemo(() => parseListInput(form.suggested_responses).length, [form.suggested_responses]);
  const promptLength = form.ai_system_prompt.trim().length;

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      const metadata = JSON.parse(form.metadata || "{}");
      const evaluationFocus = parseListInput(form.evaluation_focus);
      const suggestedResponses = parseListInput(form.suggested_responses);
      const payload = {
        ...form,
        estimated_duration_minutes: Number(form.estimated_duration_minutes),
        pre_gen_count: Number(form.pre_gen_count),
        learning_objectives: parseListInput(form.learning_objectives),
        target_skills: parseListInput(form.target_skills),
        tags: parseListInput(form.tags),
        is_ai_start_first: Boolean(form.is_ai_start_first),
        opening_message: form.opening_message.trim() || null,
        metadata: {
          ...metadata,
          ...(form.topic.trim() ? { topic: form.topic.trim() } : {}),
          ...(form.assigned_task.trim() ? { assigned_task: form.assigned_task.trim() } : {}),
          ...(form.persona.trim() ? { persona: form.persona.trim() } : {}),
          ...(evaluationFocus.length > 0 ? { evaluation_focus: evaluationFocus } : {}),
          ...(suggestedResponses.length > 0 ? { suggested_responses: suggestedResponses } : {}),
          ...(form.end_condition.trim() ? { end_condition: form.end_condition.trim() } : {}),
          ...(form.target_turns.trim() ? { target_turns: Number(form.target_turns) } : {}),
        },
      };
      delete payload.topic;
      delete payload.assigned_task;
      delete payload.persona;
      delete payload.evaluation_focus;
      delete payload.suggested_responses;
      delete payload.end_condition;
      delete payload.target_turns;
      setJsonError("");
      await onSubmit(payload);
    } catch (error) {
      setJsonError(error.message || "JSON fields must be valid before saving.");
    }
  };

  const handleSkillSuggestion = async () => {
    const suggested = await onSuggestSkills({
      description: form.description,
      category: form.category,
    });
    updateField("target_skills", prettyList(suggested));
  };

  return (
    <div className="fixed inset-0 z-[120] bg-zinc-950/60 p-3 backdrop-blur md:p-6">
      <div className="mx-auto flex h-full max-w-7xl flex-col overflow-hidden rounded-[32px] border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4 dark:border-zinc-800">
          <div>
            <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">
              {scenario ? "Edit Scenario" : "Create Scenario"}
            </p>
            <h2 className="mt-1 font-display text-2xl font-black tracking-tight">
              {scenario ? scenario.title : "New Scenario"}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-2xl border border-zinc-200 p-2 text-zinc-500 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="grid min-h-0 flex-1 gap-0 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="min-h-0 overflow-y-auto p-5 md:p-6">
            <div className="space-y-6">
              <section className="rounded-[28px] border border-zinc-200 bg-zinc-50/70 p-5 dark:border-zinc-800 dark:bg-zinc-900/60">
                <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
                  <div>
                    <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Overview</p>
                    <h3 className="mt-1 font-display text-2xl font-black tracking-tight">What is this scenario about?</h3>
                    <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
                      Start with the learner situation and the outcome they should reach. Keep it clear enough for another admin to understand in 10 seconds.
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2 text-[11px] font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                    <span className="rounded-full bg-white px-3 py-1.5 dark:bg-zinc-950">{form.mode}</span>
                    <span className="rounded-full bg-white px-3 py-1.5 dark:bg-zinc-950">{form.difficulty}</span>
                    <span className="rounded-full bg-white px-3 py-1.5 dark:bg-zinc-950">{form.estimated_duration_minutes} min</span>
                  </div>
                </div>

                <div className="mt-5 grid gap-5 xl:grid-cols-2">
                  <label className="block space-y-2 xl:col-span-2">
                    <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                      Title
                    </span>
                    <input
                      required
                      value={form.title}
                      onChange={(event) => updateField("title", event.target.value)}
                      className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                      placeholder="Example: Missing reservation at hotel check-in"
                    />
                  </label>

                  <label className="block space-y-2 xl:col-span-2">
                    <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                      Scenario Brief
                    </span>
                    <textarea
                      required
                      value={form.description}
                      onChange={(event) => updateField("description", event.target.value)}
                      rows={5}
                      className="w-full rounded-[24px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                      placeholder="Describe the learner context, who they are speaking with, the tension in the situation, and the outcome they should reach."
                    />
                  </label>

                  <label className="block space-y-2">
                    <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                      Category
                    </span>
                    <input
                      value={form.category}
                      onChange={(event) => updateField("category", event.target.value)}
                      className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                      placeholder="travel, work, daily-life..."
                    />
                  </label>

                  <label className="block space-y-2">
                    <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                      Difficulty
                    </span>
                    <select
                      value={form.difficulty}
                      onChange={(event) => updateField("difficulty", event.target.value)}
                      className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </label>
                </div>
              </section>

              <section className="rounded-[28px] border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
                <div>
                  <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Learning Setup</p>
                  <h3 className="mt-1 font-display text-2xl font-black tracking-tight">How should practice behave?</h3>
                  <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
                    These fields shape the lesson structure and make the scenario easier to find later. Enter each item on a new line or separate with commas.
                  </p>
                </div>

                <div className="mt-5 grid gap-5 xl:grid-cols-2">
                  <label className="block space-y-2">
                    <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                      Mode
                    </span>
                    <select
                      value={form.mode}
                      onChange={(event) => updateField("mode", event.target.value)}
                      className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                    >
                      {["conversation", "roleplay", "debate", "interview", "presentation"].map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="block space-y-2">
                    <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                      Max conversation time (minutes)
                    </span>
                    <input
                      type="number"
                      min="1"
                      max="180"
                      value={form.estimated_duration_minutes}
                      onChange={(event) => updateField("estimated_duration_minutes", event.target.value)}
                      className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                    />
                    <p className="text-xs leading-relaxed text-zinc-500 dark:text-zinc-400">
                      The live conversation ends automatically when this limit is reached.
                    </p>
                  </label>

                  <ListEditorField
                    label="Learning Objectives"
                    value={form.learning_objectives}
                    onChange={(value) => updateField("learning_objectives", value)}
                    helperText="Teacher-facing goals for this scenario."
                    placeholder={"Clarify a problem politely\nAsk follow-up questions\nConfirm key details"}
                  />

                  <ListEditorField
                    label="Target Skills"
                    value={form.target_skills}
                    onChange={(value) => updateField("target_skills", value)}
                    helperText="What should this practice improve?"
                    placeholder={"fluency\npronunciation\ngrammar"}
                  />

                  <div className="xl:col-span-2">
                    <ListEditorField
                      label="Tags"
                      value={form.tags}
                      onChange={(value) => updateField("tags", value)}
                      helperText="Used for filtering, search, and content discovery."
                      placeholder={"travel\nhotel\nproblem-solving"}
                      rows={3}
                    />
                  </div>

                  <div className="grid gap-4 xl:col-span-2 md:grid-cols-3">
                    <label className="flex items-center gap-3 rounded-[24px] border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
                      <input
                        type="checkbox"
                        checked={form.is_active}
                        onChange={(event) => updateField("is_active", event.target.checked)}
                      />
                      <span className="text-sm font-semibold">Active</span>
                    </label>
                    <label className="flex items-center gap-3 rounded-[24px] border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
                      <input
                        type="checkbox"
                        checked={form.is_pre_generated}
                        onChange={(event) => updateField("is_pre_generated", event.target.checked)}
                      />
                      <span className="text-sm font-semibold">Pre-generate variations</span>
                    </label>
                    <label className="block space-y-2 rounded-[24px] border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900">
                      <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                        Target pre-gen count
                      </span>
                      <input
                        type="number"
                        min="0"
                        max="30"
                        value={form.pre_gen_count}
                        onChange={(event) => updateField("pre_gen_count", event.target.value)}
                        className="w-full rounded-2xl border border-zinc-200 bg-white px-3 py-2 text-sm font-medium outline-none dark:border-zinc-700 dark:bg-zinc-950"
                      />
                    </label>
                  </div>
                </div>
              </section>

              <section className="rounded-[28px] border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
                <div>
                  <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Lesson Conversation</p>
                  <h3 className="mt-1 font-display text-2xl font-black tracking-tight">Guide the new lesson engine</h3>
                  <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
                    These fields shape the structured lesson flow used in the new guided conversation experience. They replace the need to hand-edit metadata JSON for common lesson behavior.
                  </p>
                </div>

                <div className="mt-5 grid gap-5 xl:grid-cols-2">
                  <label className="block space-y-2">
                    <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                      Lesson Topic
                    </span>
                    <input
                      value={form.topic}
                      onChange={(event) => updateField("topic", event.target.value)}
                      className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                      placeholder="Hotel check-in problem solving"
                    />
                  </label>

                  <label className="block space-y-2">
                    <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                      Conversation Partner
                    </span>
                    <input
                      value={form.persona}
                      onChange={(event) => updateField("persona", event.target.value)}
                      className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                      placeholder="Friendly hotel front desk agent"
                    />
                  </label>

                  <label className="block space-y-2 xl:col-span-2">
                    <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                      Assigned Task
                    </span>
                    <textarea
                      value={form.assigned_task}
                      onChange={(event) => updateField("assigned_task", event.target.value)}
                      rows={3}
                      className="w-full rounded-[24px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                      placeholder="Explain the reservation problem, confirm your booking details, and ask for a solution."
                    />
                  </label>

                  <ListEditorField
                    label="Evaluation Focus"
                    value={form.evaluation_focus}
                    onChange={(value) => updateField("evaluation_focus", value)}
                    helperText="What the lesson should check for across the conversation."
                    placeholder={"Explain the issue clearly\nConfirm key details\nAsk for a practical solution"}
                  />

                  <ListEditorField
                    label="Suggested Responses"
                    value={form.suggested_responses}
                    onChange={(value) => updateField("suggested_responses", value)}
                    helperText="Short starter lines shown when the learner is stuck."
                    placeholder={"I have a reservation under...\nThere seems to be a problem with...\nCould you help me solve this?"}
                  />

                  <label className="block space-y-2">
                    <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                      End Condition
                    </span>
                    <input
                      value={form.end_condition}
                      onChange={(event) => updateField("end_condition", event.target.value)}
                      className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                      placeholder="End once the learner explains the issue and confirms the next step."
                    />
                  </label>

                  <label className="block space-y-2">
                    <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                      Target User Turns
                    </span>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      value={form.target_turns}
                      onChange={(event) => updateField("target_turns", event.target.value)}
                      className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                      placeholder="6"
                    />
                  </label>

                  <label className="block space-y-2 xl:col-span-2">
                    <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                      Opening Message
                    </span>
                    <textarea
                      value={form.opening_message}
                      onChange={(event) => updateField("opening_message", event.target.value)}
                      rows={3}
                      className="w-full rounded-[24px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                      placeholder="The first line the AI will say, or the scene description for the user."
                    />
                  </label>

                  <label className="flex items-center gap-3 rounded-[24px] border border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-900 xl:col-span-2">
                    <input
                      type="checkbox"
                      checked={form.is_ai_start_first}
                      onChange={(event) => updateField("is_ai_start_first", event.target.checked)}
                    />
                    <div className="flex flex-col">
                      <span className="text-sm font-semibold">AI Start First</span>
                      <span className="text-xs text-zinc-500">If checked, AI will send the opening message first. Otherwise, it waits for the user.</span>
                    </div>
                  </label>
                </div>
              </section>

              <section className="rounded-[28px] border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">AI Prompt</p>
                    <h3 className="mt-1 font-display text-2xl font-black tracking-tight">Give the tutor clear operating rules</h3>
                    <p className="mt-2 max-w-3xl text-sm text-zinc-500 dark:text-zinc-400">
                      Focus on role, tone, correction style, and the condition for ending the conversation. Keep the brief above learner-facing and this prompt tutor-facing.
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={handleSkillSuggestion}
                      className="inline-flex items-center gap-2 rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-bold text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                    >
                      <Sparkle size={14} />
                      Suggest skills
                    </button>
                    <button
                      type="button"
                      onClick={() => updateField("ai_system_prompt", form.ai_system_prompt.trim() ? `${form.ai_system_prompt.trim()}\n\n${PROMPT_STARTER}` : PROMPT_STARTER)}
                      className="inline-flex items-center gap-2 rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-bold text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                    >
                      <NotePencil size={14} />
                      Insert starter
                    </button>
                  </div>
                </div>

                <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1.25fr)_280px]">
                  <div>
                    <textarea
                      required
                      value={form.ai_system_prompt}
                      onChange={(event) => updateField("ai_system_prompt", event.target.value)}
                      rows={14}
                      className="w-full rounded-[28px] border border-zinc-200 bg-zinc-950 px-4 py-4 font-mono text-sm text-emerald-200 outline-none transition focus:border-primary dark:border-zinc-700"
                      placeholder="You are a patient but realistic conversation partner..."
                    />
                  </div>

                  <div className="rounded-[24px] border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-900">
                    <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                      Prompt Checklist
                    </p>
                    <ul className="mt-3 space-y-2 text-sm text-zinc-600 dark:text-zinc-300">
                      <li>State who the AI is and what role it plays.</li>
                      <li>Explain how much correction the learner should receive.</li>
                      <li>Describe the desired tone and realism level.</li>
                      <li>Tell the AI when the scenario is considered complete.</li>
                    </ul>
                  </div>
                </div>
              </section>

              <section className="rounded-[28px] border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[11px] font-black uppercase tracking-[0.24em] text-primary">Advanced</p>
                    <h3 className="mt-1 font-display text-2xl font-black tracking-tight">Metadata and change tracking</h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowAdvanced((current) => !current)}
                    className="inline-flex items-center gap-2 rounded-full border border-zinc-200 px-3 py-1.5 text-xs font-bold text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                  >
                    <BracketsCurly size={14} />
                    {showAdvanced ? "Hide advanced" : "Show advanced"}
                  </button>
                </div>

                <label className="mt-5 block space-y-2">
                  <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
                    Change Note
                  </span>
                  <input
                    value={form.change_note}
                    onChange={(event) => updateField("change_note", event.target.value)}
                    className="w-full rounded-[22px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
                    placeholder="Why did this prompt or scenario change?"
                  />
                </label>

                {showAdvanced && (
                  <div className="mt-5">
                    <JsonEditorField
                      label="Advanced Metadata"
                      value={form.metadata}
                      onChange={(value) => updateField("metadata", value)}
                      placeholder='{"vocabulary_focus":"booking issues","lesson_flags":{"beta":true}}'
                      helperText="Optional extension bag for custom flags or niche scenario settings. Common lesson fields are edited above."
                    />
                  </div>
                )}
              </section>
            </div>
          </div>

          <aside className="min-h-0 overflow-y-auto border-t border-zinc-200 bg-zinc-50/80 p-5 dark:border-zinc-800 dark:bg-zinc-900/50 lg:border-l lg:border-t-0">
            <PromptQualityBadge quality={scenario?.latest_prompt_quality} />

            {jsonError && (
              <div className="mt-4 rounded-[24px] bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
                {jsonError}
              </div>
            )}

            <div className="mt-5 rounded-[24px] border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                Scenario Snapshot
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
                {[
                  ["Objectives", objectiveCount],
                  ["Skills", skillCount],
                  ["Tags", tagCount],
                  ["Eval focus", evaluationFocusCount],
                  ["Help lines", responseHintCount],
                  ["Prompt chars", promptLength],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-[20px] bg-zinc-50 px-4 py-3 dark:bg-zinc-900">
                    <p className="text-[11px] font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                      {label}
                    </p>
                    <p className="mt-1 text-lg font-black tracking-tight text-zinc-900 dark:text-zinc-100">{value}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-5 rounded-[24px] border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
              <div className="flex items-center gap-2">
                <ClockCounterClockwise size={16} className="text-zinc-500" />
                <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                  Prompt History
                </p>
              </div>
              <div className="mt-4 space-y-3">
                {promptHistory.length === 0 && (
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">No prompt revisions yet.</p>
                )}
                {promptHistory.map((entry) => (
                  <div key={entry.id} className="rounded-[22px] border border-zinc-200 p-3 dark:border-zinc-800">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold">{entry.change_note || "Prompt update"}</p>
                      <span className="rounded-full bg-zinc-100 px-2 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                        {entry.quality_score ?? "NA"}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                      {new Date(entry.created_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-5 rounded-[24px] border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
              <p className="text-xs font-black uppercase tracking-[0.18em] text-zinc-500 dark:text-zinc-400">
                Admin Notes
              </p>
              <ul className="mt-3 space-y-2 text-sm text-zinc-600 dark:text-zinc-300">
                <li>Keep scenarios reusable across many learners.</li>
                <li>Put skill-specific guidance in the prompt, not only the description.</li>
                <li>Use metadata for persona and vocabulary hints instead of prompt clutter.</li>
              </ul>
            </div>
          </aside>

          <div className="flex items-center justify-between gap-3 border-t border-zinc-200 px-5 py-4 dark:border-zinc-800 lg:col-span-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-2xl border border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-700 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="rounded-2xl bg-primary px-5 py-3 text-sm font-black text-white shadow-lg shadow-primary/20 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSaving ? "Saving..." : scenario ? "Save Scenario" : "Create Scenario"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ScenarioEditorModal;

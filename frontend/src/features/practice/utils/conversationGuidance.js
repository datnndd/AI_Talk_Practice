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

const normalizeList = (value) => {
  if (Array.isArray(value)) {
    return value
      .filter((item) => typeof item === "string")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  if (typeof value === "string" && value.trim()) {
    return [value.trim()];
  }

  return [];
};

const metadataList = (metadata, keys) => {
  if (!metadata || typeof metadata !== "object") {
    return [];
  }

  for (const key of keys) {
    const items = normalizeList(metadata[key]);
    if (items.length > 0) {
      return items;
    }
  }

  return [];
};

const uniqueStrings = (items) => {
  const seen = new Set();

  return items.filter((item) => {
    const normalized = item.trim().toLowerCase();
    if (!normalized || seen.has(normalized)) {
      return false;
    }

    seen.add(normalized);
    return true;
  });
};

const formatDurationGoal = (seconds) => {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return "";
  }

  if (seconds < 60) {
    return `about ${seconds} seconds`;
  }

  const minutes = Math.round(seconds / 60);
  return `about ${minutes} minute${minutes === 1 ? "" : "s"}`;
};

const buildModeSuggestions = (scenario, lastAssistantMessage) => {
  const mode = scenario?.mode || "conversation";
  const category = scenario?.category || "";

  const genericQuestionFallback = [
    "Could you say that one more time, please?",
    "Let me think for a second.",
    "From my point of view, ...",
    "Could you explain that in a simpler way?",
  ];

  if (/tell me about yourself/i.test(lastAssistantMessage)) {
    return [
      "Sure. My name is ..., and I currently ...",
      "One of my key strengths is ...",
      "I became interested in this field because ...",
      "A good example from my experience is ...",
    ];
  }

  if (mode === "interview") {
    return [
      "One example from my experience is ...",
      "My main strength is ...",
      "I am interested in this role because ...",
      "A challenge I handled well was ...",
    ];
  }

  if (mode === "debate") {
    return [
      "I agree to some extent, but ...",
      "The strongest reason is ...",
      "Another factor we should consider is ...",
      "The evidence seems to suggest that ...",
    ];
  }

  if (mode === "presentation") {
    return [
      "First, I would like to explain ...",
      "The key point here is ...",
      "To give a concrete example, ...",
      "In summary, ...",
    ];
  }

  if (category === "business") {
    return [
      "In my experience, ...",
      "The main reason is ...",
      "One example would be ...",
      ...genericQuestionFallback,
    ];
  }

  if (category === "travel") {
    return [
      "Could you tell me more about ...?",
      "I have a reservation under the name ...",
      "Is there anything else I should know?",
      ...genericQuestionFallback,
    ];
  }

  if (category === "academic") {
    return [
      "I think the main issue is ...",
      "Another possible solution is ...",
      "I agree with that point, but ...",
      ...genericQuestionFallback,
    ];
  }

  return [
    "I would like to ...",
    "Could you tell me more about ...?",
    "That makes sense. In my case, ...",
    ...genericQuestionFallback,
  ];
};

export const buildConversationGuidance = ({ scenario, messages, durationSeconds, turnCount }) => {
  const metadata = scenario?.metadata || {};
  const learningObjectives = normalizeList(scenario?.learning_objectives);
  const targetSkills = normalizeList(scenario?.target_skills);
  const evaluationFocus = uniqueStrings(
    metadataList(metadata, ["evaluation_focus", "success_criteria", "rubric"]).length > 0
      ? metadataList(metadata, ["evaluation_focus", "success_criteria", "rubric"])
      : [...learningObjectives, ...targetSkills]
  ).slice(0, 4);

  const topic = metadataString(metadata, ["topic", "conversation_topic"]) || scenario?.title || "Current scenario";
  const assignedTask =
    metadataString(metadata, ["assigned_task", "task", "user_goal", "goal"]) ||
    (learningObjectives.length > 0
      ? `Complete the scenario while demonstrating ${learningObjectives.slice(0, 3).join(", ")}.`
      : scenario?.description || "Stay on topic and respond naturally.");

  const completionRule =
    metadataString(metadata, ["end_condition", "completion_signal", "wrap_up_cue"]) || "";
  const explicitTurnTarget = Number(metadata.target_turns);
  const turnTarget = Number.isFinite(explicitTurnTarget) && explicitTurnTarget > 0
    ? explicitTurnTarget
    : Math.max(4, Math.min(8, (learningObjectives.length || 3) * 2));
  const durationTarget = Number(metadata.target_duration_seconds) || scenario?.estimated_duration || 0;
  const shouldWrapSoon =
    (durationTarget > 0 && durationSeconds >= durationTarget * 0.75) ||
    turnCount >= Math.max(3, turnTarget - 1);
  const shouldFinish =
    (durationTarget > 0 && durationSeconds >= durationTarget) ||
    turnCount >= turnTarget;

  const completionStatus = shouldFinish ? "ready" : shouldWrapSoon ? "soon" : "active";
  const completionTitle =
    completionStatus === "ready"
      ? "Good Time To End"
      : completionStatus === "soon"
        ? "Start Wrapping Up"
        : "Finish When";

  let completionDetail = completionRule;
  if (!completionDetail) {
    if (completionStatus === "ready") {
      completionDetail = "You have likely covered enough. Summarize your main point, confirm the outcome, and close the conversation naturally.";
    } else if (completionStatus === "soon") {
      completionDetail = "You are close to the target. Start moving toward a summary or closing exchange.";
    } else {
      const durationGoalText = formatDurationGoal(durationTarget);
      completionDetail = durationGoalText
        ? `Aim for ${durationGoalText} or roughly ${turnTarget} user turns before you close.`
        : `Aim to cover the task in roughly ${turnTarget} user turns, then close naturally.`;
    }
  }

  const lastAssistantMessage = [...(messages || [])]
    .reverse()
    .find((message) => message.role === "assistant")?.content || "";

  const suggestedResponses = uniqueStrings([
    ...metadataList(metadata, ["suggested_responses", "stuck_help", "response_hints"]),
    ...buildModeSuggestions(scenario, lastAssistantMessage),
  ]).slice(0, 4);

  return {
    topic,
    assignedTask,
    evaluationFocus,
    completion: {
      status: completionStatus,
      title: completionTitle,
      detail: completionDetail,
    },
    suggestedResponses,
  };
};

export const formatScenarioList = (value) => normalizeList(value);

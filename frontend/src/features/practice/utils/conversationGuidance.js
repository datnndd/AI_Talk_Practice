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

const buildSuggestions = (scenario, lastAssistantMessage) => {
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
  const tasks = normalizeList(scenario?.tasks);
  const evaluationFocus = uniqueStrings(tasks).slice(0, 4);

  const topic = scenario?.title || "Current scenario";
  const assignedTask = tasks.length > 0
    ? `Complete: ${tasks.slice(0, 3).join(", ")}.`
    : scenario?.description || "Stay on topic and respond naturally.";

  const turnTarget = Math.max(4, Math.min(8, (tasks.length || 3) * 2));
  const durationTarget = scenario?.estimated_duration || 0;
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

  let completionDetail;
  if (completionStatus === "ready") {
    completionDetail = "You have likely covered the required tasks. Summarize your main point and close naturally.";
  } else if (completionStatus === "soon") {
    completionDetail = "You are close to the target. Make sure each required task has been covered.";
  } else {
    const durationGoalText = formatDurationGoal(durationTarget);
    completionDetail = durationGoalText
      ? `Aim for ${durationGoalText} or roughly ${turnTarget} user turns while completing the tasks.`
      : `Aim to cover the tasks in roughly ${turnTarget} user turns, then close naturally.`;
  }

  const lastAssistantMessage = [...(messages || [])]
    .reverse()
    .find((message) => message.role === "assistant")?.content || "";

  const suggestedResponses = uniqueStrings([
    ...buildSuggestions(scenario, lastAssistantMessage),
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

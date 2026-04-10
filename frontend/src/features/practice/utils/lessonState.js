const normalizeText = (value) => (typeof value === "string" ? value.trim() : "");

export const appendUniqueMessage = (messages, nextMessage) => {
  if (!nextMessage?.content) {
    return messages;
  }

  const nextRole = normalizeText(nextMessage.role);
  const nextContent = normalizeText(nextMessage.content);
  const lastMessage = messages[messages.length - 1];

  if (
    lastMessage &&
    normalizeText(lastMessage.role) === nextRole &&
    normalizeText(lastMessage.content) === nextContent
  ) {
    return messages;
  }

  return [...messages, nextMessage];
};

export const getLessonStatusCopy = ({ lessonState, recordingState, connectionState }) => {
  if (!lessonState) {
    return "";
  }

  if (connectionState === "closed") {
    return "Reconnect to continue the guided lesson.";
  }

  if (lessonState.should_end) {
    return lessonState.completion_message || "The lesson goals are complete. You can close the conversation now.";
  }

  if (recordingState === "recording") {
    return "Answer the current lesson question naturally in your own words.";
  }

  if (recordingState === "processing") {
    return "Reviewing your answer and choosing the next guided question.";
  }

  if (recordingState === "assistant") {
    return "The coach is guiding you to the next step.";
  }

  return lessonState.current_question || "";
};

export const getLessonCompletionTone = (lessonState) => {
  if (!lessonState) {
    return "active";
  }

  if (lessonState.should_end || lessonState.status === "completed") {
    return "ready";
  }

  if ((lessonState.current_objective?.remaining_follow_ups || 0) <= 1) {
    return "soon";
  }

  return "active";
};

export const getLessonStatusLabel = (lessonState) => {
  if (!lessonState) {
    return "Waiting";
  }

  if (lessonState.should_end || lessonState.status === "completed") {
    return "Completed";
  }

  return lessonState.current_objective?.goal || "In progress";
};

export const formatLessonEndReason = (value) => {
  if (!value) {
    return "";
  }

  return value
    .split("_")
    .filter(Boolean)
    .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(" ");
};

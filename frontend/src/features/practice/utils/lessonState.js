const normalizeText = (value) => (typeof value === "string" ? value.trim() : "");

export const appendUniqueMessage = (messages, nextMessage) => {
  if (!nextMessage?.content) {
    return messages;
  }

  if (nextMessage.serverMessageId) {
    const existingIndex = messages.findIndex((message) => message.serverMessageId === nextMessage.serverMessageId);
    if (existingIndex >= 0) {
      return messages.map((message, index) => (index === existingIndex ? { ...message, ...nextMessage } : message));
    }
  }

  if (nextMessage.turnId) {
    const existingIndex = messages.findIndex((message) => message.turnId === nextMessage.turnId);
    if (existingIndex >= 0) {
      return messages.map((message, index) => (index === existingIndex ? { ...message, ...nextMessage } : message));
    }
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

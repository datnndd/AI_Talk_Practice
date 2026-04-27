const toHex = (buffer) =>
  Array.from(new Uint8Array(buffer))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");

const fallbackHash = (value) => {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(index);
    hash |= 0;
  }
  return `fallback-${Math.abs(hash).toString(16)}`;
};

export const createFutureVoiceFingerprint = async () => {
  const signals = [
    navigator.userAgent,
    navigator.language,
    navigator.languages?.join(",") || "",
    navigator.platform || "",
    String(navigator.hardwareConcurrency || ""),
    String(navigator.deviceMemory || ""),
    Intl.DateTimeFormat().resolvedOptions().timeZone || "",
    `${screen.width}x${screen.height}x${screen.colorDepth}`,
    String(window.devicePixelRatio || ""),
    String(navigator.maxTouchPoints || 0),
  ];

  const value = signals.join("|");
  if (!window.crypto?.subtle) {
    return fallbackHash(value);
  }

  const encoded = new TextEncoder().encode(value);
  const digest = await window.crypto.subtle.digest("SHA-256", encoded);
  return toHex(digest);
};


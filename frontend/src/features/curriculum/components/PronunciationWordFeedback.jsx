const normalizeToken = (value) => (value || "").toLowerCase().replace(/[^a-z']/g, "");

const getWordText = (word) => word?.Word || word?.word || word?.text || "";

const getAssessment = (word) => word?.PronunciationAssessment || word?.pronunciationAssessment || word?.pronunciation_assessment || {};

const getWordScore = (word) => {
  const assessment = getAssessment(word);
  const score = Number(assessment.AccuracyScore ?? assessment.accuracyScore ?? assessment.accuracy_score ?? word?.accuracy);
  return Number.isFinite(score) ? score : null;
};

const getErrorType = (word) => {
  const assessment = getAssessment(word);
  return String(assessment.ErrorType || assessment.errorType || assessment.error_type || "None");
};

const getToneFromScore = (score, fallbackTone = "good") => {
  if (score == null) return fallbackTone;
  if (score < 65) return "error";
  if (score < 85) return "warn";
  return "good";
};

const getWordTone = (word) => {
  if (!word) return "missing";
  const errorType = getErrorType(word).toLowerCase();
  const score = getWordScore(word);
  if (errorType && errorType !== "none") return "error";
  return getToneFromScore(score);
};

const wordToneClasses = {
  good: "text-emerald-700 bg-emerald-50 ring-emerald-200 dark:text-emerald-300 dark:bg-emerald-500/10 dark:ring-emerald-500/20",
  warn: "text-amber-700 bg-amber-50 ring-amber-200 dark:text-amber-300 dark:bg-amber-500/10 dark:ring-amber-500/20",
  error: "text-rose-700 bg-rose-50 ring-rose-200 dark:text-rose-300 dark:bg-rose-500/10 dark:ring-rose-500/20",
  missing: "text-rose-700 bg-rose-50 line-through decoration-2 ring-rose-200 dark:text-rose-300 dark:bg-rose-500/10 dark:ring-rose-500/20",
};

const buildWordFeedback = (referenceText, words) => {
  const azureWords = Array.isArray(words) ? words : [];
  let cursor = 0;

  return referenceText.split(/(\s+)/).map((token, index) => {
    if (/^\s+$/.test(token)) {
      return { key: `${index}-space`, text: token, whitespace: true };
    }

    const normalized = normalizeToken(token);
    let match = null;
    for (let wordIndex = cursor; wordIndex < azureWords.length; wordIndex += 1) {
      if (normalizeToken(getWordText(azureWords[wordIndex])) === normalized) {
        match = azureWords[wordIndex];
        cursor = wordIndex + 1;
        break;
      }
    }

    const score = getWordScore(match);
    return {
      key: `${index}-${token}`,
      text: token,
      score,
      tone: getWordTone(match),
      title: match ? `${getWordText(match) || token} · ${formatScore(score)}/100` : `${token} · omitted`,
    };
  });
};

const formatScore = (value) => {
  const score = Number(value);
  return Number.isFinite(score) ? Math.round(score) : "-";
};

const PronunciationWordFeedback = ({ assessment, referenceText }) => {
  const tokens = buildWordFeedback(referenceText || "", assessment?.words || []);

  return (
    <div className="space-y-3 rounded-xl border border-border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-black">Pronunciation result</p>
        <p className="rounded-full bg-muted px-3 py-1 text-xs font-black text-[var(--page-muted)]">
          Score: {formatScore(assessment?.score)} ({assessment?.source || "unknown"})
        </p>
      </div>
      <div className="rounded-xl bg-muted p-4 text-xl font-black leading-10">
        {tokens.map((token) =>
          token.whitespace ? (
            token.text
          ) : (
            <span
              key={token.key}
              title={token.title}
              className={`mx-1 rounded-lg px-2 py-1 ring-1 ${wordToneClasses[token.tone] || wordToneClasses.good}`}
            >
              {token.text}
            </span>
          ),
        )}
      </div>
      <div className="flex flex-wrap gap-2 text-xs font-black">
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">Đúng</span>
        <span className="rounded-full bg-amber-50 px-3 py-1 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">Chưa rõ</span>
        <span className="rounded-full bg-rose-50 px-3 py-1 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">Sai/thiếu</span>
      </div>
    </div>
  );
};

export default PronunciationWordFeedback;

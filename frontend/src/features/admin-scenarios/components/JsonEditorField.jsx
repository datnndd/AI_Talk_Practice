const formatJson = (value) => {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return "[]";
  }
};

const JsonEditorField = ({
  label,
  value,
  onChange,
  rows = 6,
  placeholder = "[]",
  helperText,
}) => {
  let parsedState = { valid: true, message: "Valid JSON" };

  try {
    if (value?.trim()) {
      JSON.parse(value);
    }
  } catch (error) {
    parsedState = { valid: false, message: error.message };
  }

  return (
    <label className="block space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
          {label}
        </span>
        <span
          className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${
            parsedState.valid
              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
              : "bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300"
          }`}
        >
          {parsedState.valid ? "Valid" : "Invalid"}
        </span>
      </div>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={rows}
        spellCheck="false"
        placeholder={placeholder}
        className="w-full rounded-[22px] border border-zinc-200 bg-zinc-950 px-4 py-3 font-mono text-sm text-emerald-200 outline-none transition focus:border-primary dark:border-zinc-700"
      />
      <div className="flex items-start justify-between gap-3 text-xs">
        <p className="text-zinc-500 dark:text-zinc-400">{helperText}</p>
        <button
          type="button"
          onClick={() => {
            try {
              onChange(formatJson(JSON.parse(value || placeholder)));
            } catch {
              onChange(value);
            }
          }}
          className="shrink-0 rounded-full border border-zinc-200 px-2.5 py-1 font-semibold text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
        >
          Format
        </button>
      </div>
      {!parsedState.valid && (
        <p className="text-xs text-rose-600 dark:text-rose-300">{parsedState.message}</p>
      )}
    </label>
  );
};

export default JsonEditorField;

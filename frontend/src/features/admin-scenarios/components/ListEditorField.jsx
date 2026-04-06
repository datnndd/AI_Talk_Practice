const parseItems = (value = "") =>
  value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);

const formatItems = (value = "") => parseItems(value).join("\n");

const ListEditorField = ({
  label,
  value,
  onChange,
  helperText,
  placeholder,
  rows = 4,
}) => {
  const items = parseItems(value);

  const removeItem = (itemToRemove) => {
    onChange(
      items
        .filter((item) => item !== itemToRemove)
        .join("\n")
    );
  };

  return (
    <label className="block space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <span className="text-xs font-black uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-400">
            {label}
          </span>
          {helperText && <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">{helperText}</p>}
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
            {items.length} items
          </span>
          <button
            type="button"
            onClick={() => onChange(formatItems(value))}
            className="rounded-full border border-zinc-200 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            Format
          </button>
        </div>
      </div>

      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        rows={rows}
        placeholder={placeholder}
        className="w-full rounded-[24px] border border-zinc-200 bg-white px-4 py-3 text-sm font-medium outline-none transition focus:border-primary dark:border-zinc-700 dark:bg-zinc-900"
      />

      {items.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {items.map((item) => (
            <button
              key={`${label}-${item}`}
              type="button"
              onClick={() => removeItem(item)}
              className="rounded-full bg-zinc-100 px-3 py-1.5 text-xs font-semibold text-zinc-700 transition hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700"
            >
              {item}
            </button>
          ))}
        </div>
      )}
    </label>
  );
};

export default ListEditorField;

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
          <span className="text-xs font-black uppercase tracking-[0.24em] text-[var(--page-muted)]">
            {label}
          </span>
          {helperText && <p className="mt-1 text-xs text-[var(--page-muted)]">{helperText}</p>}
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-muted px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.18em] text-[var(--page-muted)]">
            {items.length} items
          </span>
          <button
            type="button"
            onClick={() => onChange(formatItems(value))}
            className="rounded-full border border-border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[var(--page-muted)] transition hover:bg-muted hover:text-[var(--page-fg)]"
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
        className="w-full rounded-[24px] border border-border bg-card px-4 py-3 text-sm font-medium text-[var(--page-fg)] outline-none transition focus:border-primary focus:ring-4 focus:ring-[var(--focus-ring)]"
      />

      {items.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {items.map((item) => (
            <button
              key={`${label}-${item}`}
              type="button"
              onClick={() => removeItem(item)}
              className="rounded-full bg-muted px-3 py-1.5 text-xs font-semibold text-[var(--page-muted)] transition hover:bg-[var(--surface-strong)] hover:text-[var(--page-fg)]"
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

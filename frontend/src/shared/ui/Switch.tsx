interface Props {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}

export function Switch({ checked, onChange, label }: Props) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      className="switch"
      onClick={() => onChange(!checked)}
    >
      <span className={`switch-track${checked ? " on" : ""}`}>
        <span className="switch-thumb" />
      </span>
      <span>{label}</span>
    </button>
  );
}

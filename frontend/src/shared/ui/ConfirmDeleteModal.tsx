import { Modal } from "./Modal";

interface Props {
  open: boolean;
  label: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDeleteModal({ open, label, onConfirm, onCancel }: Props) {
  return (
    <Modal open={open} onClose={onCancel} danger>
      <p style={{ margin: "0 0 1em", fontSize: "0.9em" }}>{label}</p>
      <div style={{ display: "flex", gap: "0.8em", justifyContent: "flex-end" }}>
        <button
          type="button"
          onClick={onCancel}
          style={{ background: "transparent", border: "none", color: "var(--text)" }}
        >
          отмена
        </button>
        <button
          type="button"
          onClick={onConfirm}
          style={{ background: "transparent", border: "none", color: "var(--danger)" }}
        >
          удалить
        </button>
      </div>
    </Modal>
  );
}

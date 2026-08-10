import type { MouseEvent, ReactNode } from "react";

interface Props {
  open: boolean;
  onClose: () => void;
  danger?: boolean;
  children: ReactNode;
}

export function Modal({ open, onClose, danger, children }: Props) {
  if (!open) return null;

  function handleOverlayMouseDown(e: MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget) onClose();
  }

  return (
    <div className="modal-overlay" onMouseDown={handleOverlayMouseDown}>
      <div className={`modal-card${danger ? " danger" : ""}`}>{children}</div>
    </div>
  );
}

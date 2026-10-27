import type { ReactNode } from "react";

interface StatePanelProps {
  tone?: "muted" | "error" | "empty";
  title?: string;
  children?: ReactNode;
}

/** Shared visual for loading / empty / error states across every view. */
export default function StatePanel({ tone = "muted", title, children }: StatePanelProps) {
  return (
    <div className={`state-panel state-panel-${tone}`} role={tone === "error" ? "alert" : undefined}>
      {title && <p className="state-panel-title">{title}</p>}
      {children && <div className="state-panel-body">{children}</div>}
    </div>
  );
}

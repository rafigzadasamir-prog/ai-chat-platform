import type { Usage } from "../types";

interface UsagePanelProps {
  usage: Usage | null;
  isLoading: boolean;
  error: string | null;
}

export default function UsagePanel({ usage, isLoading, error }: UsagePanelProps) {
  return (
    <section className="usage-panel" aria-label="Usage statistics">
      <h3>Usage</h3>
      {isLoading && <p className="state-panel-muted">Loading…</p>}
      {error && <p className="state-panel-error">{error}</p>}
      {!isLoading && !error && usage && (
        <dl>
          <div className="usage-row">
            <dt>Messages sent</dt>
            <dd>{usage.message_count.toLocaleString()}</dd>
          </div>
          <div className="usage-row">
            <dt>Est. tokens used</dt>
            <dd>{usage.estimated_tokens.toLocaleString()}</dd>
          </div>
        </dl>
      )}
    </section>
  );
}

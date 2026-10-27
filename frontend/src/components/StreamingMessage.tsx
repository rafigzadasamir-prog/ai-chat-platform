import Markdown from "./Markdown";

interface StreamingMessageProps {
  content: string;
  isStreaming: boolean;
}

/**
 * Presentational-only: the parent owns the fetch/SSE plumbing and simply
 * hands this component an ever-growing `content` string as chunks arrive,
 * which keeps this component trivial to test (see tests/StreamingMessage.test.tsx).
 */
export default function StreamingMessage({ content, isStreaming }: StreamingMessageProps) {
  return (
    <div className="message message-assistant" data-testid="streaming-message">
      <div className="message-avatar" aria-hidden="true">
        AI
      </div>
      <div className="message-bubble">
        {content ? (
          <Markdown content={content} />
        ) : (
          isStreaming && <span className="state-panel-muted">Thinking…</span>
        )}
        {isStreaming && <span className="streaming-cursor" aria-hidden="true" />}
      </div>
    </div>
  );
}

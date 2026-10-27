import { useEffect, useRef } from "react";
import Markdown from "./Markdown";
import StatePanel from "./StatePanel";
import StreamingMessage from "./StreamingMessage";
import type { Message } from "../types";

interface MessageListProps {
  messages: Message[];
  streaming: { content: string; isStreaming: boolean } | null;
  isLoading: boolean;
  error: string | null;
}

export default function MessageList({ messages, streaming, isLoading, error }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Optional chaining on the call too: jsdom (used in tests) doesn't implement it.
    bottomRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages.length, streaming?.content]);

  if (isLoading) {
    return <StatePanel tone="muted" title="Loading conversation…" />;
  }

  if (error) {
    return (
      <StatePanel tone="error" title="Couldn't load this conversation">
        {error}
      </StatePanel>
    );
  }

  if (messages.length === 0 && !streaming) {
    return (
      <StatePanel tone="empty" title="No messages yet">
        Ask a question below, or attach a document first so the assistant can ground its answer
        in it.
      </StatePanel>
    );
  }

  return (
    <div className="message-list" aria-live="polite">
      {messages.map((message) => (
        <div key={message.id} className={`message message-${message.role}`}>
          <div className="message-avatar" aria-hidden="true">
            {message.role === "user" ? "You" : "AI"}
          </div>
          <div className="message-bubble">
            {message.role === "assistant" ? (
              <Markdown content={message.content} />
            ) : (
              <p>{message.content}</p>
            )}
          </div>
        </div>
      ))}
      {streaming && <StreamingMessage content={streaming.content} isStreaming={streaming.isStreaming} />}
      <div ref={bottomRef} />
    </div>
  );
}

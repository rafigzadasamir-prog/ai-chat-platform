/**
 * Minimal Server-Sent-Events parsing for a POST-based stream consumed via
 * fetch (the browser's native EventSource only supports GET, so the
 * backend's streaming chat endpoint is consumed manually here).
 */

export interface SSEEvent {
  event: string;
  data: string;
}

/**
 * Pure function: split a buffer into complete "event: ...\ndata: ...\n\n"
 * blocks plus the (possibly incomplete) remainder. Kept pure and exported so
 * it can be unit tested without touching fetch/streams at all.
 */
export function parseSSEBuffer(buffer: string): { events: SSEEvent[]; rest: string } {
  const events: SSEEvent[] = [];
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";

  for (const part of parts) {
    if (!part.trim()) continue;
    let eventName = "message";
    const dataLines: string[] = [];
    for (const line of part.split("\n")) {
      if (line.startsWith("event:")) {
        eventName = line.slice("event:".length).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice("data:".length).trim());
      }
    }
    events.push({ event: eventName, data: dataLines.join("\n") });
  }

  return { events, rest };
}

/** Consume a fetch Response body as a stream of parsed SSE events. */
export async function* streamSSE(response: Response): AsyncGenerator<SSEEvent> {
  if (!response.body) return;
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const { events, rest } = parseSSEBuffer(buffer);
    buffer = rest;
    for (const event of events) yield event;
  }

  if (buffer.trim()) {
    const { events } = parseSSEBuffer(`${buffer}\n\n`);
    for (const event of events) yield event;
  }
}

import { describe, expect, it } from "vitest";
import { parseSSEBuffer } from "../src/lib/sse";

describe("parseSSEBuffer", () => {
  it("parses a single complete event with an implicit 'message' event name", () => {
    const { events, rest } = parseSSEBuffer('data: {"chunk":"hi"}\n\n');
    expect(events).toEqual([{ event: "message", data: '{"chunk":"hi"}' }]);
    expect(rest).toBe("");
  });

  it("parses multiple complete events from one buffer", () => {
    const buffer = 'data: {"chunk":"a"}\n\ndata: {"chunk":"b"}\n\n';
    const { events, rest } = parseSSEBuffer(buffer);
    expect(events).toHaveLength(2);
    expect(events[0].data).toBe('{"chunk":"a"}');
    expect(events[1].data).toBe('{"chunk":"b"}');
    expect(rest).toBe("");
  });

  it("parses a named event (event: done)", () => {
    const { events } = parseSSEBuffer('event: done\ndata: {"message_id":7}\n\n');
    expect(events).toEqual([{ event: "done", data: '{"message_id":7}' }]);
  });

  it("holds back an incomplete trailing block as 'rest'", () => {
    const { events, rest } = parseSSEBuffer('data: {"chunk":"a"}\n\ndata: {"chunk":"inco');
    expect(events).toEqual([{ event: "message", data: '{"chunk":"a"}' }]);
    expect(rest).toBe('data: {"chunk":"inco');
  });

  it("ignores blank blocks", () => {
    const { events } = parseSSEBuffer("\n\n\n\n");
    expect(events).toEqual([]);
  });
});

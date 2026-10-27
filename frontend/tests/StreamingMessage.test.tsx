import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import StreamingMessage from "../src/components/StreamingMessage";

describe("StreamingMessage", () => {
  it("shows a thinking placeholder and cursor before any chunk arrives", () => {
    const { container } = render(<StreamingMessage content="" isStreaming={true} />);
    expect(screen.getByText("Thinking…")).toBeInTheDocument();
    expect(container.querySelector(".streaming-cursor")).not.toBeNull();
  });

  it("renders appended content as chunks accumulate, re-rendering with growing text", () => {
    const { rerender } = render(<StreamingMessage content="Hel" isStreaming={true} />);
    expect(screen.getByText("Hel")).toBeInTheDocument();

    rerender(<StreamingMessage content="Hello " isStreaming={true} />);
    expect(screen.getByText("Hello", { exact: false })).toBeInTheDocument();

    rerender(<StreamingMessage content="Hello world" isStreaming={true} />);
    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });

  it("hides the streaming cursor once streaming finishes", () => {
    const { container, rerender } = render(<StreamingMessage content="Hello" isStreaming={true} />);
    expect(container.querySelector(".streaming-cursor")).not.toBeNull();

    rerender(<StreamingMessage content="Hello world" isStreaming={false} />);
    expect(container.querySelector(".streaming-cursor")).toBeNull();
    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });

  it("renders markdown inside the streamed content (e.g. bold text)", () => {
    render(<StreamingMessage content="This is **bold**" isStreaming={true} />);
    const strong = screen.getByText("bold");
    expect(strong.tagName.toLowerCase()).toBe("strong");
  });
});

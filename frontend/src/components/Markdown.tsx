import { useMemo } from "react";
import { renderMarkdown } from "../lib/markdown";

export default function Markdown({ content }: { content: string }) {
  const html = useMemo(() => renderMarkdown(content), [content]);
  // Safe: renderMarkdown() sanitises with DOMPurify before this ever renders.
  return <div className="markdown" dangerouslySetInnerHTML={{ __html: html }} />;
}

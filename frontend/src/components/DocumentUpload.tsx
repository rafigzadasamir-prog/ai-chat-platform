import { useRef } from "react";
import type { ChangeEvent } from "react";
import type { DocumentInfo } from "../types";

interface DocumentUploadProps {
  documents: DocumentInfo[];
  onUpload: (file: File) => void;
  isUploading: boolean;
  errorMessage: string | null;
}

export default function DocumentUpload({
  documents,
  onUpload,
  isUploading,
  errorMessage,
}: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) onUpload(file);
    event.target.value = "";
  }

  return (
    <div className="document-upload">
      <button
        type="button"
        className="document-upload-trigger"
        onClick={() => inputRef.current?.click()}
        disabled={isUploading}
      >
        {isUploading ? "Indexing…" : "Attach document"}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".txt,.md,text/plain"
        hidden
        onChange={handleChange}
        aria-label="Attach a text document to ground answers in"
      />
      {documents.length > 0 && (
        <ul className="document-list">
          {documents.map((doc) => (
            <li key={doc.document_name}>
              <span className="document-list-name">{doc.document_name}</span>
              <span className="document-list-count">
                {doc.chunk_count} chunk{doc.chunk_count === 1 ? "" : "s"}
              </span>
            </li>
          ))}
        </ul>
      )}
      {errorMessage && <p className="document-upload-error">{errorMessage}</p>}
    </div>
  );
}

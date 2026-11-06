import { useRef, useState, type DragEvent, type ChangeEvent } from "react";
import { useUploadDocument } from "@/features/documents/hooks";
import { ErrorNotice } from "@/components/ErrorNotice";
import { ApiError } from "@/lib/api";

const MAX_SIZE = 5 * 1024 * 1024; // 5 MB
const ALLOWED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
];

interface UploadDropzoneProps {
  readonly?: boolean;
}

export function UploadDropzone({ readonly = false }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const upload = useUploadDocument();

  function handleFile(file: File) {
    setError(null);
    setSuccess(null);

    if (file.size > MAX_SIZE) {
      setError(`File exceeds ${String(MAX_SIZE / (1024 * 1024))} MB limit.`);
      return;
    }
    if (!ALLOWED_TYPES.includes(file.type)) {
      setError(`Unsupported file type: ${file.type || "unknown"}.`);
      return;
    }

    upload.mutate(
      { file },
      {
        onSuccess: (doc) => {
          setSuccess(`Uploaded ${doc.filename} (${String(doc.char_count)} chars).`);
        },
        onError: (err) => {
          if (err instanceof ApiError) {
            setError(err.message);
          } else {
            setError("Upload failed.");
          }
        },
      },
    );
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    if (readonly) return;
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function onDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    if (!readonly) setDragging(true);
  }

  function onDragLeave() {
    setDragging(false);
  }

  function onInputChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  }

  return (
    <section aria-label="Upload document" className="space-y-4">
      <div
        role="button"
        tabIndex={readonly ? -1 : 0}
        aria-disabled={readonly}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => !readonly && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (!readonly && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        className={`flex min-h-[120px] cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed p-6 text-center transition-colors ${
          readonly
            ? "cursor-not-allowed border-hairline bg-sunken text-ink-muted"
            : dragging
              ? "border-brand bg-brand-soft text-brand"
              : "border-hairline bg-sheet text-ink-secondary hover:border-brand hover:bg-brand-soft/50"
        }`}
      >
        <p className="text-body font-medium">
          {readonly ? "Upload disabled in read-only demo" : "Drop a file here or click to browse"}
        </p>
        <p className="mt-1 text-small text-ink-muted">
          PDF, DOCX, or TXT · max 5 MB · max 60 pages
        </p>
        <p className="mt-1 text-small text-ink-muted">
          Synthetic and anonymised data only (ADR-010).
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={onInputChange}
          className="sr-only"
          aria-label="Choose file to upload"
          disabled={readonly}
        />
      </div>

      {upload.isPending && (
        <p role="status" className="text-small text-ink-secondary">
          Uploading and extracting…
        </p>
      )}

      {error && <ErrorNotice code="server" message={error} />}

      {success && (
        <p role="status" className="text-small text-success">
          {success}
        </p>
      )}

      {readonly && (
        <p className="text-small text-ink-muted">
          This demo tenant is read-only. Upload is demonstrated by{" "}
          <code className="font-mono">make dev</code> and the recorded walkthrough.
        </p>
      )}
    </section>
  );
}

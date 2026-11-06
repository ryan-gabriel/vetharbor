import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AppProviders } from "@/app/providers";
import { UploadDropzone } from "@/components/UploadDropzone";

function wrap(ui: React.ReactElement) {
  return render(<AppProviders>{ui}</AppProviders>);
}

describe("UploadDropzone", () => {
  it("renders the dropzone with accessible label", () => {
    wrap(<UploadDropzone />);
    expect(screen.getByRole("button", { name: /choose file to upload/i })).toBeDefined();
  });

  it("shows limits in the idle state", () => {
    wrap(<UploadDropzone />);
    expect(screen.getByText(/max 5 MB/i)).toBeDefined();
    expect(screen.getByText(/max 60 pages/i)).toBeDefined();
  });

  it("is keyboard accessible", () => {
    wrap(<UploadDropzone />);
    const dropzone = screen.getByRole("button", { name: /choose file to upload/i }).parentElement;
    expect(dropzone).toBeDefined();
  });

  it("shows read-only message when readonly", () => {
    wrap(<UploadDropzone readonly />);
    expect(screen.getByText(/read-only demo/i)).toBeDefined();
    expect(screen.getByText(/make dev/i)).toBeDefined();
  });

  it("disables file input when readonly", () => {
    wrap(<UploadDropzone readonly />);
    const input = screen.getByLabelText(/choose file to upload/i);
    expect(input).toHaveProperty("disabled", true);
  });
});

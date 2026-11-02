import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { WakingUp } from "@/components/WakingUp";

describe("WakingUp", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("states what is true instead of faking progress (DESIGN.md §4)", () => {
    render(<WakingUp />);
    expect(screen.getByRole("status").textContent).toContain("This demo is asleep.");
  });

  it("counts down and auto-retries at the estimate", () => {
    const onRetry = vi.fn();
    render(<WakingUp estimatedSeconds={5} onRetry={onRetry} />);
    fireEvent.click(screen.getByRole("button", { name: /retry now/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);

    onRetry.mockClear();
    vi.advanceTimersByTime(5000);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});

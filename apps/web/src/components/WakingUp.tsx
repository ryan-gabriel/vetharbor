import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";

/**
 * DESIGN.md §4 `WakingUp`: Render free services sleep after 15 minutes and
 * take about a minute to wake (ARCHITECTURE.md §2). A skeleton would imply
 * progress that is not happening - this state says what is true instead.
 */
export interface WakingUpProps {
  estimatedSeconds?: number;
  onRetry?: () => void;
}

export function WakingUp({ estimatedSeconds = 60, onRetry }: WakingUpProps) {
  const [remaining, setRemaining] = useState(estimatedSeconds);

  useEffect(() => {
    const ticker = window.setInterval(() => {
      setRemaining((seconds) => (seconds > 0 ? seconds - 1 : 0));
    }, 1000);
    return () => {
      window.clearInterval(ticker);
    };
  }, []);

  useEffect(() => {
    if (!onRetry) return;
    const timer = window.setTimeout(onRetry, estimatedSeconds * 1000);
    return () => {
      window.clearTimeout(timer);
    };
  }, [onRetry, estimatedSeconds]);

  return (
    <section
      role="status"
      aria-label="Service starting"
      className="flex min-h-svh flex-col items-center justify-center gap-4 bg-sunken p-8 text-center"
    >
      <h2 className="font-display text-h2 text-ink">This demo is asleep.</h2>
      <p className="font-mono text-small text-ink-muted">retrying in {remaining}s</p>
      <Button
        variant="secondary"
        onClick={
          onRetry ??
          (() => {
            window.location.reload();
          })
        }
      >
        Retry now
      </Button>
      <p className="text-small text-ink-secondary">
        Prefer instant proof?{" "}
        <a className="text-brand underline underline-offset-4" href="/#recording">
          Watch the 3-minute recording
        </a>
      </p>
    </section>
  );
}

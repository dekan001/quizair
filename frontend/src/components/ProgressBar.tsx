interface ProgressBarProps {
  /** 0..1 */
  value: number;
  className?: string;
}

export function ProgressBar({ value, className = "" }: ProgressBarProps) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div
      className={`relative h-2.5 w-full overflow-hidden rounded-full bg-white/10 ${className}`}
    >
      <div
        className="relative h-full rounded-full bg-gradient-to-r from-brand-400 via-violet-500 to-fuchsia-500 shadow-[0_0_12px_-2px_rgba(139,92,246,0.7)] transition-all duration-500 ease-out"
        style={{ width: `${pct}%` }}
      >
        {pct > 0 && (
          <div className="absolute inset-0 overflow-hidden rounded-full">
            <div className="absolute inset-y-0 -left-1/2 w-1/2 animate-shimmer bg-gradient-to-r from-transparent via-white/40 to-transparent" />
          </div>
        )}
      </div>
    </div>
  );
}

// Лёгкие inline-иконки (stroke) для навигации и UI. Цвет наследуется (currentColor).

interface IconProps {
  className?: string;
}

const base = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function HomeIcon({ className = "h-6 w-6" }: IconProps) {
  return (
    <svg className={className} {...base}>
      <path d="M3 10.7 12 3l9 7.7" />
      <path d="M5.5 9.5V21h13V9.5" />
      <path d="M9.5 21v-6h5v6" />
    </svg>
  );
}

export function GiftIcon({ className = "h-6 w-6" }: IconProps) {
  return (
    <svg className={className} {...base}>
      <rect x="3" y="8" width="18" height="4" rx="1" />
      <path d="M5 12v8a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-8" />
      <path d="M12 8v13" />
      <path d="M12 8S10.5 3.5 8 4.2C6 4.8 6.4 8 9 8h3Z" />
      <path d="M12 8s1.5-4.5 4-3.8C18 4.8 17.6 8 15 8h-3Z" />
    </svg>
  );
}

export function TrophyIcon({ className = "h-6 w-6" }: IconProps) {
  return (
    <svg className={className} {...base}>
      <path d="M7 4h10v5a5 5 0 0 1-10 0V4Z" />
      <path d="M17 5h3v2a3 3 0 0 1-3 3" />
      <path d="M7 5H4v2a3 3 0 0 0 3 3" />
      <path d="M12 14v3" />
      <path d="M8.5 21h7l-.7-3.2a1 1 0 0 0-1-.8h-3.6a1 1 0 0 0-1 .8L8.5 21Z" />
    </svg>
  );
}

export function UserIcon({ className = "h-6 w-6" }: IconProps) {
  return (
    <svg className={className} {...base}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </svg>
  );
}

export function ChevronLeftIcon({ className = "h-5 w-5" }: IconProps) {
  return (
    <svg className={className} {...base}>
      <path d="m15 5-7 7 7 7" />
    </svg>
  );
}

export function ShareIcon({ className = "h-5 w-5" }: IconProps) {
  return (
    <svg className={className} {...base}>
      <path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7" />
      <path d="M12 16V3" />
      <path d="m8 7 4-4 4 4" />
    </svg>
  );
}

export function RefreshIcon({ className = "h-4 w-4" }: IconProps) {
  return (
    <svg className={className} {...base}>
      <path d="M21 12a9 9 0 1 1-2.6-6.4" />
      <path d="M21 4v5h-5" />
    </svg>
  );
}

export function BoltIcon({ className = "h-5 w-5" }: IconProps) {
  return (
    <svg className={className} {...base}>
      <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" />
    </svg>
  );
}

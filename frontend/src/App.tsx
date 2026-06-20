import { HashRouter, NavLink, Route, Routes } from "react-router-dom";
import type { ComponentType } from "react";
import { UserProvider } from "./context/UserContext";
import { Home } from "./screens/Home";
import { Quiz } from "./screens/Quiz";
import { Limit } from "./screens/Limit";
import { Profile } from "./screens/Profile";
import { Leaderboard } from "./screens/Leaderboard";
import { Tasks } from "./screens/Tasks";
import { Share } from "./screens/Share";
import {
  GiftIcon,
  HomeIcon,
  TrophyIcon,
  UserIcon,
} from "./components/icons";

interface NavItem {
  to: string;
  label: string;
  Icon: ComponentType<{ className?: string }>;
  end?: boolean;
}

const NAV: NavItem[] = [
  { to: "/", label: "Главная", Icon: HomeIcon, end: true },
  { to: "/tasks", label: "Задания", Icon: GiftIcon },
  { to: "/leaderboard", label: "Топ", Icon: TrophyIcon },
  { to: "/profile", label: "Профиль", Icon: UserIcon },
];

function BottomNav() {
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-0 z-40 flex justify-center pb-[calc(env(safe-area-inset-bottom)+0.75rem)]">
      <nav className="pointer-events-auto flex items-center gap-1 rounded-full border border-white/10 bg-ink-900/70 p-1.5 shadow-[0_12px_40px_-12px_rgba(0,0,0,0.8)] backdrop-blur-2xl">
        {NAV.map(({ to, label, Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `relative flex h-12 items-center gap-2 rounded-full px-4 text-sm font-medium transition-all duration-300 ${
                isActive
                  ? "bg-gradient-to-br from-brand-500 to-violet-600 text-white shadow-glow"
                  : "text-slate-400 hover:text-slate-200"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon className="h-5 w-5 shrink-0" />
                <span
                  className={`overflow-hidden whitespace-nowrap transition-all duration-300 ${
                    isActive ? "max-w-[6rem] opacity-100" : "max-w-0 opacity-0"
                  }`}
                >
                  {label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

export default function App() {
  return (
    <UserProvider>
      <HashRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/quiz/:topic" element={<Quiz />} />
          <Route path="/limit" element={<Limit />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/share" element={<Share />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
        </Routes>
        <BottomNav />
      </HashRouter>
    </UserProvider>
  );
}

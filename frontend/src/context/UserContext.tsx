import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import { api, type User } from "../lib/api";
import { getReferrerId, getTgUser, inTelegram } from "../lib/telegram";

const DEV_TG_KEY = "dev_tg_id";
const DEFAULT_DEV_TG = 1001;

interface UserContextValue {
  user: User | null;
  loading: boolean;
  error: string | null;
  tgId: number;
  isDev: boolean;
  refresh: () => Promise<void>;
  setDevTgId: (id: number) => void;
}

const UserContext = createContext<UserContextValue | null>(null);

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [devTgId, setDevTgIdState] = useState<number>(() => {
    const stored = Number(localStorage.getItem(DEV_TG_KEY));
    return Number.isFinite(stored) && stored > 0 ? stored : DEFAULT_DEV_TG;
  });

  const isDev = !inTelegram();
  const tgId = isDev ? devTgId : (getTgUser()?.id ?? devTgId);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setError(null);
      const tgUser = getTgUser();
      const u = await api.createUser({
        tg_id: tgId,
        username: tgUser?.username,
        first_name: tgUser?.first_name,
        photo_url: tgUser?.photo_url,
        referred_by: getReferrerId() ?? undefined,
      });
      setUser(u);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки профиля");
    } finally {
      setLoading(false);
    }
  }, [tgId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const setDevTgId = useCallback((id: number) => {
    localStorage.setItem(DEV_TG_KEY, String(id));
    setDevTgIdState(id);
  }, []);

  const value = useMemo<UserContextValue>(
    () => ({ user, loading, error, tgId, isDev, refresh, setDevTgId }),
    [user, loading, error, tgId, isDev, refresh, setDevTgId],
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useUser(): UserContextValue {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within UserProvider");
  return ctx;
}

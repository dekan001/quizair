// Минимальные типы Telegram Web App SDK (script telegram-web-app.js).
export {};

declare global {
  interface TgWebAppUser {
    id: number;
    username?: string;
    first_name?: string;
    last_name?: string;
    photo_url?: string;
    language_code?: string;
  }

  interface Window {
    Telegram?: {
      WebApp?: {
        initData: string;
        initDataUnsafe?: { user?: TgWebAppUser; [k: string]: unknown };
        version?: string;
        platform?: string;
        colorScheme?: "light" | "dark";
        themeParams?: Record<string, string>;
        viewportHeight?: number;
        viewportStableHeight?: number;
        ready: () => void;
        expand: () => void;
        close: () => void;
        setHeaderColor: (color: string) => void;
        setBackgroundColor: (color: string) => void;
        openTelegramLink: (url: string) => void;
        openLink: (url: string) => void;
        HapticFeedback?: {
          impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
          notificationOccurred: (type: "error" | "success" | "warning") => void;
          selectionChanged: () => void;
        };
      };
    };
  }
}

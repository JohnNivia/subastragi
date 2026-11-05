import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "../api/axios";

const ApiHealthContext = createContext<"checking" | "online" | "offline">("checking");

export function ApiHealthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");
  useEffect(() => {
    let active = true;
    const check = () => api.get("/health").then(
      () => { if (active) setStatus("online"); },
      () => { if (active) setStatus("offline"); },
    );
    void check();
    const interval = window.setInterval(() => { void check(); }, 60_000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);
  return <ApiHealthContext.Provider value={status}>{children}</ApiHealthContext.Provider>;
}

export function useApiHealth() {
  return useContext(ApiHealthContext);
}

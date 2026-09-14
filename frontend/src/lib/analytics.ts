import { useSyncExternalStore } from "react";

const STORAGE_KEY = "geoworkspace:analyses-completed";

function readCount(): number {
  try {
    return Number(window.localStorage.getItem(STORAGE_KEY)) || 0;
  } catch {
    return 0;
  }
}

function subscribe(onStoreChange: () => void): () => void {
  window.addEventListener("storage", onStoreChange);
  return () => window.removeEventListener("storage", onStoreChange);
}

function getServerSnapshot(): number {
  return 0;
}

/**
 * Tracks successful tool runs in this browser only -- there's no backend
 * persistence (see the README's Known Limitations), so this can't be a
 * real usage count. It's a per-browser convenience, not a metric.
 */
export function useAnalysesCompleted(): number {
  return useSyncExternalStore(subscribe, readCount, getServerSnapshot);
}

export function recordAnalysisCompleted(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, String(readCount() + 1));
    // The native "storage" event only fires in *other* tabs, not the one
    // that made the change, so dispatch one here to update this tab's own
    // useAnalysesCompleted() subscribers (e.g. the dashboard, reached via
    // client-side navigation without a full reload).
    window.dispatchEvent(new StorageEvent("storage", { key: STORAGE_KEY }));
  } catch {
    // localStorage can be unavailable (private browsing, disabled site
    // data) -- losing the count is fine, it's not load-bearing.
  }
}

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";

interface UsePollingResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  errorStatus: number | null;
  refetch: () => void;
}

export default function usePolling<T>(
  fetchFn: () => Promise<T>,
  intervalMs: number,
  enabled: boolean = true,
): UsePollingResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fetchFnRef = useRef(fetchFn);
  const hasFetchedRef = useRef(false);
  const requestCounterRef = useRef(0);

  // Keep fetchFn ref current so the interval always calls the latest version
  fetchFnRef.current = fetchFn;

  const stopPolling = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const doFetch = useCallback(async () => {
    const requestId = ++requestCounterRef.current;
    try {
      const result = await fetchFnRef.current();
      if (requestId !== requestCounterRef.current) return; // stale
      setData(result);
      setError(null);
      setErrorStatus(null);
    } catch (err) {
      if (requestId !== requestCounterRef.current) return; // stale
      const message =
        err instanceof Error ? err.message : "Something went wrong";
      const status = err instanceof ApiError ? err.status : null;
      setError(message);
      setErrorStatus(status);

      // Stop polling on 404 -- the game doesn't exist, retrying won't help
      if (status === 404) {
        stopPolling();
        setData(null);
      }
    } finally {
      if (requestId === requestCounterRef.current) {
        setLoading(false);
      }
    }
  }, [stopPolling]);

  // Immediate fetch on mount (or when enabled turns on)
  useEffect(() => {
    if (!enabled) {
      hasFetchedRef.current = false;
      return;
    }

    // Fetch immediately
    hasFetchedRef.current = true;
    setLoading(true);
    doFetch();

    // Set up polling interval
    intervalRef.current = setInterval(doFetch, intervalMs);

    return () => {
      stopPolling();
    };
  }, [enabled, intervalMs, doFetch, stopPolling]);

  const refetch = useCallback(() => {
    // Reset the interval so the next tick starts fresh after this manual fetch
    stopPolling();
    doFetch();
    if (enabled) {
      intervalRef.current = setInterval(doFetch, intervalMs);
    }
  }, [doFetch, enabled, intervalMs, stopPolling]);

  return { data, loading, error, errorStatus, refetch };
}

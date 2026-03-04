import { useState, useEffect } from 'react';

/**
 * Debounces a value by the given delay in milliseconds.
 * Returns the debounced value after the delay has elapsed without changes.
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

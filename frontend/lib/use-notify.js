"use client";

import { useCallback, useState } from "react";

export function useNotify() {
  const [items, setItems] = useState([]);

  const push = useCallback((type, text) => {
    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    setItems((prev) => [...prev, { id, type, text }]);
    window.setTimeout(() => {
      setItems((prev) => prev.filter((item) => item.id !== id));
    }, 3200);
  }, []);

  return { items, push };
}

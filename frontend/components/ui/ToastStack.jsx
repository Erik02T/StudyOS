"use client";

export default function ToastStack({ items }) {
  return (
    <div className="pointer-events-none fixed bottom-20 right-4 z-50 grid w-full max-w-xs gap-2 lg:bottom-6">
      {items.map((item) => (
        <div
          key={item.id}
          className={`pointer-events-auto rounded-xl border px-3 py-2 text-sm shadow-lg ${
            item.type === "ok"
              ? "border-success/60 bg-success/15 text-success"
              : "border-danger/60 bg-danger/15 text-danger"
          }`}
        >
          {item.text}
        </div>
      ))}
    </div>
  );
}

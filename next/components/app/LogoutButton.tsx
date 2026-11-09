"use client";

import { clearUserCaches } from "@/components/pwa/ServiceWorker";

export function LogoutButton() {
  return (
    <form
      method="post"
      action="/api/auth/logout"
      onSubmit={async (e) => {
        e.preventDefault();
        const form = e.currentTarget;
        await clearUserCaches().catch(() => {});
        form.submit();
      }}
    >
      <button type="submit" className="btn-ghost px-4 py-2 text-sm">Cerrar sesión</button>
    </form>
  );
}

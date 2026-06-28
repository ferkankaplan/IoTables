import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

type Tenant = {
  id: string;
  name: string;
  slug: string;
  status: "draft" | "active" | "suspended";
};

const tenants: Tenant[] = [];

function PlatformApp() {
  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">IoTables Platform</p>
          <h1>Tenant Yönetimi</h1>
        </div>
        <button type="button">Yeni Tenant</button>
      </header>

      <section className="panel">
        <div className="panelHeader">
          <h2>Müşteri İşletmeler</h2>
          <span>{tenants.length} kayıt</span>
        </div>
        {tenants.length === 0 ? (
          <p className="empty">Henüz tenant oluşturulmadı.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>İşletme</th>
                <th>Slug</th>
                <th>Durum</th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((tenant) => (
                <tr key={tenant.id}>
                  <td>{tenant.name}</td>
                  <td>{tenant.slug}</td>
                  <td>{tenant.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <PlatformApp />
  </StrictMode>,
);

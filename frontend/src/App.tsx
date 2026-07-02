import { FormEvent, useEffect, useMemo, useState } from "react";

type TenantHealthSummary = {
  tenantId: string;
  name: string;
  subdomain: string;
  status: string;
  dnsReady: boolean;
  sector: string | null;
  provisioningState: string;
  lastLifecycleEventAt: string | null;
  healthFlags: string[];
  createdAt: string;
  updatedAt: string;
};

type TenantProfile = TenantHealthSummary & {
  gsmNumber: string;
  capacity: number | null;
  address: string | null;
  starterTemplateState: string;
  tenantAdminBootstrapState: string;
};

type TenantListResponse = {
  items: TenantHealthSummary[];
  page: {
    nextCursor: string | null;
    limit: number;
  };
};

type TenantLifecycleEvent = {
  eventId: string;
  tenantId: string;
  previousStatus: string | null;
  nextStatus: string;
  actorUserId: string | null;
  reason: string;
  createdAt: string;
};

type TenantLifecycleEventListResponse = {
  items: TenantLifecycleEvent[];
  page: {
    nextCursor: string | null;
    limit: number;
  };
};

type AuditEvent = {
  auditEventId: string;
  tenantId: string | null;
  actor: {userId: string} | null;
  action: string;
  target: {type: string; id: string};
  reason: string | null;
  metadata: Record<string, unknown>;
  createdAt: string;
};

type AuditEventListResponse = {
  items: AuditEvent[];
  page: {
    nextCursor: string | null;
    limit: number;
  };
};

type ProvisioningResult = {
  tenantId: string;
  status: string;
  subdomain: string;
  starterTemplateApplied: boolean;
  failureSummary: string | null;
  dnsReady: boolean;
};

type ProvisioningState = {
  tenantId: string;
  tenantStatus: string;
  starterApplicationStatus: string;
  templateKey: string | null;
  templateVersion: number | null;
  failureSummary: string | null;
  dnsReady: boolean;
  createdAt: string;
  updatedAt: string;
};

type ProvisioningRecoverySummary = {
  tenantId: string;
  missingRequiredRecords: string[];
  completedPhases: string[];
  failedPhase: string | null;
  safeRetryAllowed: boolean;
  failureSummary: string | null;
};

type AuthenticatedActor = {
  userId: string | null;
  tenantId: string | null;
  appScope: string;
  roles: string[];
  stationIds: string[];
  hallIds: string[];
  displayName: string | null;
};

type SessionResponse = {
  actor: AuthenticatedActor;
};

type LoginResponse = {
  status: string;
  actor: AuthenticatedActor | null;
  setupToken: string | null;
  expiresAt: string | null;
  totpSetup: {
    secret: string;
    otpauthUrl: string;
  } | null;
};

type ApiErrorEnvelope = {
  error?: {
    code?: string;
    message?: string;
    fieldErrors?: { path: string; message: string }[];
  };
};

type CreateTenantForm = {
  name: string;
  subdomain: string;
  gsmNumber: string;
  sector: "cafe" | "";
  capacity: string;
  address: string;
};

type TenantProfileForm = {
  gsmNumber: string;
  sector: "cafe" | "";
  capacity: string;
  address: string;
};

const initialForm: CreateTenantForm = {
  name: "",
  subdomain: "",
  gsmNumber: "",
  sector: "cafe",
  capacity: "",
  address: ""
};

export function App() {
  const [authState, setAuthState] = useState<"checking" | "authenticated" | "anonymous">(
    "checking"
  );
  const [actor, setActor] = useState<AuthenticatedActor | null>(null);
  const [tenants, setTenants] = useState<TenantHealthSummary[]>([]);
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [selectedTenant, setSelectedTenant] = useState<TenantProfile | null>(null);
  const [listState, setListState] = useState<"loading" | "ready" | "error">("loading");
  const [detailState, setDetailState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [sectorFilter, setSectorFilter] = useState("");
  const [searchText, setSearchText] = useState("");
  const [nextCursor, setNextCursor] = useState<string | null>(null);

  async function loadTenants(nextSelectedTenantId?: string, cursor = "0", append = false) {
    setListState("loading");
    setErrorMessage(null);
    try {
      const params = new URLSearchParams();
      params.set("cursor", cursor);
      params.set("limit", "25");
      if (statusFilter) {
        params.set("status", statusFilter);
      }
      if (sectorFilter) {
        params.set("sector", sectorFilter);
      }
      if (searchText.trim()) {
        params.set("q", searchText.trim());
      }
      const payload = await apiRequest<TenantListResponse>(
        `/api/v1/platform/tenants?${params.toString()}`
      );
      const nextItems = append ? [...tenants, ...payload.items] : payload.items;
      setTenants(nextItems);
      setNextCursor(payload.page.nextCursor);
      const fallbackTenantId = nextItems[0]?.tenantId ?? null;
      const selectedCandidate = nextSelectedTenantId ?? selectedTenantId ?? fallbackTenantId;
      setSelectedTenantId(
        nextItems.some((tenant) => tenant.tenantId === selectedCandidate)
          ? selectedCandidate
          : fallbackTenantId
      );
      setListState("ready");
    } catch (error) {
      setListState("error");
      setErrorMessage(errorMessageFrom(error));
    }
  }

  useEffect(() => {
    let active = true;
    async function loadSession() {
      try {
        const payload = await apiRequest<SessionResponse>("/api/v1/auth/session");
        if (active) {
          setActor(payload.actor);
          setAuthState("authenticated");
        }
      } catch {
        if (active) {
          setActor(null);
          setAuthState("anonymous");
        }
      }
    }

    void loadSession();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (authState === "authenticated") {
      void loadTenants();
    }
  }, [authState]);

  useEffect(() => {
    if (!selectedTenantId) {
      setSelectedTenant(null);
      setDetailState("idle");
      return;
    }

    let active = true;
    async function loadDetail() {
      setDetailState("loading");
      try {
        const payload = await apiRequest<TenantProfile>(
          `/api/v1/platform/tenants/${selectedTenantId}`
        );
        if (active) {
          setSelectedTenant(payload);
          setDetailState("ready");
        }
      } catch {
        if (active) {
          setSelectedTenant(null);
          setDetailState("error");
        }
      }
    }

    void loadDetail();
    return () => {
      active = false;
    };
  }, [selectedTenantId]);

  const counters = useMemo(() => {
    return {
      active: tenants.filter((tenant) => tenant.status === "active").length,
      failed: tenants.filter((tenant) => tenant.status === "provisioning_failed").length,
      dnsNotReady: tenants.filter((tenant) => !tenant.dnsReady).length
    };
  }, [tenants]);

  async function logout() {
    await apiRequest("/api/v1/auth/logout", {
      headers: {"X-CSRF-Token": crypto.randomUUID()},
      method: "POST"
    });
    setActor(null);
    setAuthState("anonymous");
    setTenants([]);
    setSelectedTenantId(null);
    setSelectedTenant(null);
  }

  function applyTenantProfile(updated: TenantProfile) {
    setSelectedTenant(updated);
    setTenants((current) =>
      current.map((tenant) =>
        tenant.tenantId === updated.tenantId
          ? {
              tenantId: updated.tenantId,
              name: updated.name,
              subdomain: updated.subdomain,
              status: updated.status,
              dnsReady: updated.dnsReady,
              sector: updated.sector,
              provisioningState: updated.provisioningState,
              lastLifecycleEventAt: updated.lastLifecycleEventAt,
              healthFlags: updated.healthFlags,
              createdAt: updated.createdAt,
              updatedAt: updated.updatedAt
            }
          : tenant
      )
    );
  }

  if (authState === "checking") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-stone-100 text-zinc-950">
        <StateBlock title="Giriş durumu kontrol ediliyor" />
      </main>
    );
  }

  if (authState === "anonymous") {
    return (
      <LoginScreen
        onAuthenticated={(nextActor) => {
          setActor(nextActor);
          setAuthState("authenticated");
        }}
      />
    );
  }

  return (
    <main className="min-h-screen bg-stone-100 text-zinc-950">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 border-r border-zinc-200 bg-white px-5 py-6 lg:block">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
              IoTables
            </p>
            <h1 className="mt-2 text-2xl font-semibold">Platform</h1>
          </div>
          <nav className="mt-8 space-y-1 text-sm">
            <button className="w-full border-l-4 border-emerald-600 bg-emerald-50 px-3 py-2 text-left font-medium text-emerald-950">
              Tenantlar
            </button>
          </nav>
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          <header className="border-b border-zinc-200 bg-white px-4 py-4 sm:px-6">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                  PlatformApp
                </p>
                <h2 className="text-2xl font-semibold">Tenant sağlığı</h2>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-zinc-500">{actor?.displayName ?? "Platform"}</span>
                <button
                  className="h-10 border border-zinc-300 px-4 text-sm font-medium hover:bg-zinc-50"
                  onClick={() => void logout()}
                  type="button"
                >
                  Çıkış yap
                </button>
                <button
                  className="h-10 border border-zinc-950 bg-zinc-950 px-4 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:border-zinc-300 disabled:bg-zinc-300"
                  onClick={() => setDrawerOpen(true)}
                  type="button"
                >
                  Tenant oluştur
                </button>
              </div>
            </div>
          </header>

          <div className="grid flex-1 grid-cols-1 xl:grid-cols-[minmax(0,1fr)_420px]">
            <section className="min-w-0 px-4 py-5 sm:px-6">
              <div className="grid gap-3 md:grid-cols-3">
                <Metric label="Aktif" value={counters.active} />
                <Metric label="Provisioning hatası" value={counters.failed} />
                <Metric label="DNS hazır değil" value={counters.dnsNotReady} />
              </div>

              <div className="mt-5 overflow-hidden border border-zinc-200 bg-white">
                <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
                  <h3 className="text-sm font-semibold">Tenant listesi</h3>
                  <button
                    className="text-sm font-medium text-emerald-700 hover:text-emerald-900"
                    onClick={() => void loadTenants()}
                    type="button"
                  >
                    Yenile
                  </button>
                </div>
                <form
                  className="grid gap-3 border-b border-zinc-200 px-4 py-3 md:grid-cols-[140px_140px_minmax(0,1fr)_auto]"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void loadTenants(undefined, "0", false);
                  }}
                >
                  <select
                    className="h-10 border border-zinc-300 bg-white px-3 text-sm"
                    onChange={(event) => setStatusFilter(event.target.value)}
                    value={statusFilter}
                  >
                    <option value="">Tüm durumlar</option>
                    <option value="active">Aktif</option>
                    <option value="provisioning">Provisioning</option>
                    <option value="provisioning_failed">Hatalı</option>
                    <option value="suspended">Askıda</option>
                  </select>
                  <select
                    className="h-10 border border-zinc-300 bg-white px-3 text-sm"
                    onChange={(event) => setSectorFilter(event.target.value)}
                    value={sectorFilter}
                  >
                    <option value="">Tüm sektörler</option>
                    <option value="cafe">Kafe</option>
                  </select>
                  <input
                    className="h-10 border border-zinc-300 px-3 text-sm"
                    onChange={(event) => setSearchText(event.target.value)}
                    placeholder="Ara"
                    value={searchText}
                  />
                  <button
                    className="h-10 border border-zinc-950 px-4 text-sm font-medium hover:bg-zinc-50"
                    type="submit"
                  >
                    Uygula
                  </button>
                </form>

                {listState === "loading" ? (
                  <StateBlock title="Yükleniyor" />
                ) : listState === "error" ? (
                  <StateBlock title={errorMessage ?? "Tenant listesi alınamadı"} tone="error" />
                ) : tenants.length === 0 ? (
                  <StateBlock title="Henüz tenant yok" />
                ) : (
                  <div className="divide-y divide-zinc-200">
                    {tenants.map((tenant) => (
                      <button
                        className={`grid w-full gap-3 px-4 py-4 text-left hover:bg-zinc-50 md:grid-cols-[minmax(0,1.4fr)_120px_120px_140px] ${
                          selectedTenantId === tenant.tenantId ? "bg-emerald-50" : "bg-white"
                        }`}
                        key={tenant.tenantId}
                        onClick={() => setSelectedTenantId(tenant.tenantId)}
                        type="button"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold">{tenant.name}</p>
                          <p className="mt-1 truncate text-xs text-zinc-500">
                            {tenant.subdomain}.iotables.net
                          </p>
                        </div>
                        <StatusBadge value={tenant.status} />
                        <StatusBadge value={tenant.dnsReady ? "dns_ready" : "dns_not_ready"} />
                        <div className="min-w-0 text-xs text-zinc-600">
                          <p className="truncate">{tenant.provisioningState}</p>
                          <p className="mt-1 truncate">{tenant.sector ?? "Sektör yok"}</p>
                        </div>
                      </button>
                    ))}
                    {nextCursor ? (
                      <div className="px-4 py-3">
                        <button
                          className="h-10 w-full border border-zinc-300 text-sm font-medium hover:bg-zinc-50"
                          onClick={() => void loadTenants(undefined, nextCursor, true)}
                          type="button"
                        >
                          Daha fazla
                        </button>
                      </div>
                    ) : null}
                  </div>
                )}
              </div>
            </section>

            <TenantDetailPanel
              onTenantChanged={applyTenantProfile}
              state={detailState}
              tenant={selectedTenant}
            />
          </div>
        </section>
      </div>

      {drawerOpen ? (
        <CreateTenantDrawer
          onClose={() => setDrawerOpen(false)}
          onCreated={(result) => {
            setDrawerOpen(false);
            void loadTenants(result.tenantId);
          }}
        />
      ) : null}
    </main>
  );
}

function LoginScreen({ onAuthenticated }: { onAuthenticated: (actor: AuthenticatedActor) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [totpSetup, setTotpSetup] = useState<LoginResponse["totpSetup"]>(null);
  const [totpRequired, setTotpRequired] = useState(false);
  const [state, setState] = useState<"idle" | "submitting" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const canSubmit =
    username.trim() &&
    password &&
    (!totpSetup && !totpRequired ? true : totpCode.trim().length === 6);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit || state === "submitting") {
      return;
    }

    setState("submitting");
    setError(null);
    try {
      const result =
        totpSetup !== null
          ? await apiRequest<LoginResponse>("/api/v1/auth/totp/enroll", {
              body: JSON.stringify({
                username: username.trim(),
                password,
                secret: totpSetup.secret,
                totpCode
              }),
              headers: {"Content-Type": "application/json"},
              method: "POST"
            })
          : await apiRequest<LoginResponse>("/api/v1/auth/login", {
              body: JSON.stringify({
                appScope: "platform",
                username: username.trim(),
                password,
                totpCode: totpCode || undefined
              }),
              headers: {"Content-Type": "application/json"},
              method: "POST"
            });
      if (result.status === "totp_enrollment_required" && result.totpSetup !== null) {
        setTotpSetup(result.totpSetup);
        setTotpRequired(false);
        setState("idle");
        return;
      }
      if (result.status === "totp_required") {
        setTotpRequired(true);
        setState("idle");
        return;
      }
      if (result.status !== "authenticated" || result.actor === null) {
        throw new Error("Platform erişimi tamamlanamadı.");
      }
      onAuthenticated(result.actor);
    } catch (loginError) {
      setError(errorMessageFrom(loginError));
      setState("error");
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-stone-100 px-4 text-zinc-950">
      <section className="w-full max-w-sm border border-zinc-200 bg-white">
        <div className="border-b border-zinc-200 px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
            IoTables
          </p>
          <h1 className="mt-2 text-2xl font-semibold">Platform girişi</h1>
        </div>
        <form className="space-y-4 px-5 py-5" onSubmit={(event) => void submit(event)}>
          <FieldText label="Kullanıcı adı" onChange={setUsername} required value={username} />
          <FieldText
            label="Şifre"
            onChange={setPassword}
            required
            type="password"
            value={password}
          />
          {totpSetup ? (
            <div className="border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-950">
              <p className="font-semibold">TOTP kurulumu</p>
              <p className="mt-2 break-all font-mono text-xs">{totpSetup.secret}</p>
              <p className="mt-2 break-all text-xs">{totpSetup.otpauthUrl}</p>
            </div>
          ) : null}
          {totpSetup || totpRequired ? (
            <FieldText
              label="TOTP kodu"
              onChange={setTotpCode}
              required
              value={totpCode}
            />
          ) : null}
          {state === "error" ? <StateBlock title={error ?? "Giriş yapılamadı"} tone="error" /> : null}
          <button
            className="h-10 w-full bg-zinc-950 px-4 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-300"
            disabled={!canSubmit || state === "submitting"}
            type="submit"
          >
            {state === "submitting" ? "Giriş yapılıyor" : "Giriş yap"}
          </button>
        </form>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-zinc-200 bg-white px-4 py-3">
      <p className="text-xs font-medium text-zinc-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function TenantDetailPanel({
  onTenantChanged,
  state,
  tenant
}: {
  onTenantChanged: (tenant: TenantProfile) => void;
  state: "idle" | "loading" | "ready" | "error";
  tenant: TenantProfile | null;
}) {
  const [form, setForm] = useState<TenantProfileForm>({
    address: "",
    capacity: "",
    gsmNumber: "",
    sector: "cafe"
  });
  const [actionState, setActionState] = useState<"idle" | "submitting" | "error">("idle");
  const [actionError, setActionError] = useState<string | null>(null);
  const [lifecycleEvents, setLifecycleEvents] = useState<TenantLifecycleEvent[]>([]);
  const [lifecycleState, setLifecycleState] = useState<"idle" | "loading" | "ready" | "error">(
    "idle"
  );
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [auditState, setAuditState] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [provisioningState, setProvisioningState] = useState<ProvisioningState | null>(null);
  const [recoverySummary, setRecoverySummary] = useState<ProvisioningRecoverySummary | null>(null);
  const [provisioningPanelState, setProvisioningPanelState] = useState<
    "idle" | "loading" | "ready" | "error"
  >("idle");

  useEffect(() => {
    if (!tenant) {
      setLifecycleEvents([]);
      setLifecycleState("idle");
      setAuditEvents([]);
      setAuditState("idle");
      setProvisioningState(null);
      setRecoverySummary(null);
      setProvisioningPanelState("idle");
      return;
    }
    setForm({
      address: tenant.address ?? "",
      capacity: tenant.capacity?.toString() ?? "",
      gsmNumber: tenant.gsmNumber,
      sector: tenant.sector === "cafe" ? "cafe" : ""
    });
    setActionState("idle");
    setActionError(null);
  }, [tenant?.tenantId]);

  useEffect(() => {
    if (!tenant) {
      return;
    }
    void loadLifecycleEvents(tenant.tenantId);
    void loadAuditEvents(tenant.tenantId);
    void loadProvisioningRecovery(tenant.tenantId);
  }, [tenant?.tenantId]);

  async function loadLifecycleEvents(tenantId: string) {
    setLifecycleState("loading");
    try {
      const payload = await apiRequest<TenantLifecycleEventListResponse>(
        `/api/v1/platform/tenants/${tenantId}/lifecycle-events?limit=5`
      );
      setLifecycleEvents(payload.items);
      setLifecycleState("ready");
    } catch {
      setLifecycleEvents([]);
      setLifecycleState("error");
    }
  }

  async function loadAuditEvents(tenantId: string) {
    setAuditState("loading");
    try {
      const params = new URLSearchParams({tenantId, limit: "5"});
      const payload = await apiRequest<AuditEventListResponse>(
        `/api/v1/platform/audit-events?${params.toString()}`
      );
      setAuditEvents(payload.items);
      setAuditState("ready");
    } catch {
      setAuditEvents([]);
      setAuditState("error");
    }
  }

  function refreshTenantEvidence(tenantId: string) {
    void loadLifecycleEvents(tenantId);
    void loadAuditEvents(tenantId);
    void loadProvisioningRecovery(tenantId);
  }

  async function loadProvisioningRecovery(tenantId: string) {
    setProvisioningPanelState("loading");
    try {
      const [statePayload, summaryPayload] = await Promise.all([
        apiRequest<ProvisioningState>(`/api/v1/platform/tenants/${tenantId}/provisioning`),
        apiRequest<ProvisioningRecoverySummary>(
          `/api/v1/platform/tenants/${tenantId}/provisioning/recovery-summary`
        )
      ]);
      setProvisioningState(statePayload);
      setRecoverySummary(summaryPayload);
      setProvisioningPanelState("ready");
    } catch {
      setProvisioningState(null);
      setRecoverySummary(null);
      setProvisioningPanelState("error");
    }
  }

  async function retryProvisioning() {
    if (!tenant || actionState === "submitting") {
      return;
    }
    const recoveryNote = window.prompt("Provisioning retry notu");
    if (recoveryNote === null) {
      return;
    }

    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<ProvisioningState>(
        `/api/v1/platform/tenants/${tenant.tenantId}/provisioning/retry`,
        {
          body: JSON.stringify({recoveryNote: recoveryNote.trim() || null}),
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": crypto.randomUUID()
          },
          method: "POST"
        }
      );
      const updated = await apiRequest<TenantProfile>(
        `/api/v1/platform/tenants/${tenant.tenantId}`
      );
      onTenantChanged(updated);
      refreshTenantEvidence(updated.tenantId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!tenant || actionState === "submitting") {
      return;
    }

    setActionState("submitting");
    setActionError(null);
    try {
      const updated = await apiRequest<TenantProfile>(
        `/api/v1/platform/tenants/${tenant.tenantId}/profile`,
        {
          body: JSON.stringify({
            address: form.address.trim() || null,
            capacity: form.capacity ? Number(form.capacity) : null,
            gsmNumber: form.gsmNumber.trim(),
            sector: form.sector || null
          }),
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": crypto.randomUUID()
          },
          method: "PATCH"
        }
      );
      onTenantChanged(updated);
      refreshTenantEvidence(updated.tenantId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function setDnsReady(dnsReady: boolean) {
    if (!tenant || actionState === "submitting") {
      return;
    }

    setActionState("submitting");
    setActionError(null);
    try {
      const updated = await apiRequest<TenantProfile>(
        `/api/v1/platform/tenants/${tenant.tenantId}/dns-ready`,
        {
          body: JSON.stringify({dnsReady}),
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": crypto.randomUUID()
          },
          method: "POST"
        }
      );
      onTenantChanged(updated);
      refreshTenantEvidence(updated.tenantId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function changeStatus(nextStatus: "active" | "suspended") {
    if (!tenant || actionState === "submitting") {
      return;
    }

    const reason = window.prompt(
      nextStatus === "suspended" ? "Askıya alma nedeni" : "Yeniden aktifleştirme nedeni"
    );
    if (!reason?.trim()) {
      return;
    }

    setActionState("submitting");
    setActionError(null);
    try {
      const updated = await apiRequest<TenantProfile>(
        `/api/v1/platform/tenants/${tenant.tenantId}/status`,
        {
          body: JSON.stringify({nextStatus, reason: reason.trim()}),
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": crypto.randomUUID()
          },
          method: "POST"
        }
      );
      onTenantChanged(updated);
      refreshTenantEvidence(updated.tenantId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  const canSubmit = Boolean(tenant && form.gsmNumber.trim() && actionState !== "submitting");
  const nextLifecycleStatus = tenant?.status === "active" ? "suspended" : "active";

  return (
    <aside className="border-t border-zinc-200 bg-white px-5 py-5 xl:border-l xl:border-t-0">
      <h3 className="text-sm font-semibold">Tenant ayrıntısı</h3>
      {state === "idle" ? (
        <StateBlock title="Tenant seçilmedi" />
      ) : state === "loading" ? (
        <StateBlock title="Ayrıntı yükleniyor" />
      ) : state === "error" || tenant === null ? (
        <StateBlock title="Tenant ayrıntısı alınamadı" tone="error" />
      ) : (
        <div className="mt-4 space-y-5">
          <div>
            <p className="text-xl font-semibold">{tenant.name}</p>
            <p className="mt-1 break-all text-sm text-zinc-500">{tenant.subdomain}.iotables.net</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusBadge value={tenant.status} />
            <StatusBadge value={tenant.dnsReady ? "dns_ready" : "dns_not_ready"} />
            <StatusBadge value={tenant.starterTemplateState} />
          </div>
          <DetailRows
            rows={[
              ["GSM", tenant.gsmNumber],
              ["Sektör", tenant.sector ?? "-"],
              ["Kapasite", tenant.capacity?.toString() ?? "-"],
              ["Adres", tenant.address ?? "-"],
              ["Admin bootstrap", tenant.tenantAdminBootstrapState],
              ["Oluşturma", formatDate(tenant.createdAt)]
            ]}
          />
          <div className="border-t border-zinc-200 pt-4">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Provisioning
            </p>
            {provisioningPanelState === "loading" ? (
              <p className="mt-2 text-sm text-zinc-500">Provisioning durumu yükleniyor</p>
            ) : provisioningPanelState === "error" ? (
              <StateBlock title="Provisioning durumu alınamadı" tone="error" />
            ) : provisioningState ? (
              <div className="mt-3 space-y-3">
                <div className="flex flex-wrap gap-2">
                  <StatusBadge value={provisioningState.tenantStatus} />
                  <StatusBadge value={provisioningState.starterApplicationStatus} />
                  {recoverySummary?.safeRetryAllowed ? <StatusBadge value="safe_retry" /> : null}
                </div>
                {provisioningState.failureSummary ? (
                  <p className="text-sm text-zinc-600">{provisioningState.failureSummary}</p>
                ) : null}
                {recoverySummary ? (
                  <DetailRows
                    rows={[
                      ["Eksik", recoverySummary.missingRequiredRecords.join(", ") || "-"],
                      ["Tamamlanan", recoverySummary.completedPhases.join(", ") || "-"],
                      ["Hatalı faz", recoverySummary.failedPhase ?? "-"]
                    ]}
                  />
                ) : null}
                <button
                  className="h-10 w-full border border-zinc-300 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                  disabled={
                    actionState === "submitting" ||
                    tenant.status !== "provisioning_failed" ||
                    !recoverySummary?.safeRetryAllowed
                  }
                  onClick={() => void retryProvisioning()}
                  type="button"
                >
                  Provisioning retry
                </button>
              </div>
            ) : null}
          </div>
          <form className="space-y-3 border-t border-zinc-200 pt-4" onSubmit={saveProfile}>
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Profil ayarları
            </p>
            <FieldText
              label="GSM"
              onChange={(value) => setForm((current) => ({...current, gsmNumber: value}))}
              required
              value={form.gsmNumber}
            />
            <label className="block">
              <span className="text-sm font-medium">Sektör</span>
              <select
                className="mt-1 h-10 w-full border border-zinc-300 px-3 text-sm"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    sector: event.target.value === "cafe" ? "cafe" : ""
                  }))
                }
                value={form.sector}
              >
                <option value="">Seçilmedi</option>
                <option value="cafe">Kafe</option>
              </select>
            </label>
            <FieldText
              label="Kapasite"
              onChange={(value) => setForm((current) => ({...current, capacity: value}))}
              type="number"
              value={form.capacity}
            />
            <FieldText
              label="Adres"
              onChange={(value) => setForm((current) => ({...current, address: value}))}
              value={form.address}
            />
            <button
              className="h-10 w-full bg-zinc-950 px-4 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-300"
              disabled={!canSubmit}
              type="submit"
            >
              {actionState === "submitting" ? "Kaydediliyor" : "Profili kaydet"}
            </button>
          </form>
          <div className="space-y-3 border-t border-zinc-200 pt-4">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Operasyonlar
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              <button
                className="h-10 border border-zinc-300 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                disabled={actionState === "submitting"}
                onClick={() => void setDnsReady(!tenant.dnsReady)}
                type="button"
              >
                {tenant.dnsReady ? "DNS hazır değil yap" : "DNS hazır yap"}
              </button>
              <button
                className="h-10 border border-zinc-300 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                disabled={
                  actionState === "submitting" ||
                  !["active", "suspended", "provisioning_failed"].includes(tenant.status)
                }
                onClick={() => void changeStatus(nextLifecycleStatus)}
                type="button"
              >
                {nextLifecycleStatus === "suspended" ? "Askıya al" : "Aktifleştir"}
              </button>
            </div>
            {actionError ? <StateBlock title={actionError} tone="error" /> : null}
          </div>
          <div className="border-t border-zinc-200 pt-4">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Lifecycle geçmişi
            </p>
            {lifecycleState === "loading" ? (
              <p className="mt-2 text-sm text-zinc-500">Geçmiş yükleniyor</p>
            ) : lifecycleState === "error" ? (
              <StateBlock title="Lifecycle geçmişi alınamadı" tone="error" />
            ) : lifecycleEvents.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-500">Lifecycle kaydı yok</p>
            ) : (
              <ol className="mt-3 space-y-3">
                {lifecycleEvents.map((event) => (
                  <li className="border-l-2 border-zinc-200 pl-3 text-sm" key={event.eventId}>
                    <div className="font-medium">
                      {event.previousStatus ?? "başlangıç"}
                      {" -> "}
                      {event.nextStatus}
                    </div>
                    <div className="mt-1 text-zinc-500">{event.reason}</div>
                    <div className="mt-1 text-xs text-zinc-400">{formatDate(event.createdAt)}</div>
                  </li>
                ))}
              </ol>
            )}
          </div>
          <div className="border-t border-zinc-200 pt-4">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Audit kayıtları
            </p>
            {auditState === "loading" ? (
              <p className="mt-2 text-sm text-zinc-500">Audit kayıtları yükleniyor</p>
            ) : auditState === "error" ? (
              <StateBlock title="Audit kayıtları alınamadı" tone="error" />
            ) : auditEvents.length === 0 ? (
              <p className="mt-2 text-sm text-zinc-500">Audit kaydı yok</p>
            ) : (
              <ol className="mt-3 space-y-3">
                {auditEvents.map((event) => (
                  <li className="border-l-2 border-zinc-200 pl-3 text-sm" key={event.auditEventId}>
                    <div className="font-medium">{event.action}</div>
                    <div className="mt-1 text-zinc-500">
                      {event.reason ?? auditMetadataSummary(event.metadata)}
                    </div>
                    <div className="mt-1 text-xs text-zinc-400">{formatDate(event.createdAt)}</div>
                  </li>
                ))}
              </ol>
            )}
          </div>
          <div className="border-t border-zinc-200 pt-4">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Sağlık işaretleri
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {tenant.healthFlags.length > 0 ? (
                tenant.healthFlags.map((flag) => <StatusBadge key={flag} value={flag} />)
              ) : (
                <span className="text-sm text-zinc-500">Kritik işaret yok</span>
              )}
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}

function DetailRows({ rows }: { rows: [string, string][] }) {
  return (
    <dl className="divide-y divide-zinc-200 border-y border-zinc-200">
      {rows.map(([label, value]) => (
        <div className="grid grid-cols-[120px_minmax(0,1fr)] gap-3 py-3 text-sm" key={label}>
          <dt className="text-zinc-500">{label}</dt>
          <dd className="min-w-0 break-words font-medium">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function CreateTenantDrawer({
  onClose,
  onCreated
}: {
  onClose: () => void;
  onCreated: (result: ProvisioningResult) => void;
}) {
  const [form, setForm] = useState<CreateTenantForm>(initialForm);
  const [state, setState] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProvisioningResult | null>(null);

  const canSubmit = form.name.trim() && form.subdomain.trim() && form.gsmNumber.trim();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit || state === "submitting") {
      return;
    }

    setState("submitting");
    setError(null);
    try {
      const payload = await apiRequest<ProvisioningResult>("/api/v1/platform/tenants", {
        body: JSON.stringify({
          name: form.name.trim(),
          subdomain: form.subdomain.trim(),
          gsmNumber: form.gsmNumber.trim(),
          sector: form.sector || undefined,
          capacity: form.capacity ? Number(form.capacity) : undefined,
          address: form.address.trim() || undefined
        }),
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "POST"
      });
      setResult(payload);
      setState("success");
    } catch (submitError) {
      setError(errorMessageFrom(submitError));
      setState("error");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-zinc-950/35">
      <div className="flex h-full w-full max-w-xl flex-col bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4">
          <h3 className="text-lg font-semibold">Tenant oluştur</h3>
          <button
            className="h-9 border border-zinc-300 px-3 text-sm font-medium hover:bg-zinc-50"
            onClick={onClose}
            type="button"
          >
            Kapat
          </button>
        </div>

        <form className="flex min-h-0 flex-1 flex-col" onSubmit={(event) => void submit(event)}>
          <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-5">
            <FieldText
              label="Tenant adı"
              onChange={(value) => setForm((current) => ({ ...current, name: value }))}
              required
              value={form.name}
            />
            <FieldText
              label="Subdomain"
              onChange={(value) => setForm((current) => ({ ...current, subdomain: value }))}
              required
              value={form.subdomain}
            />
            <FieldText
              label="GSM"
              onChange={(value) => setForm((current) => ({ ...current, gsmNumber: value }))}
              required
              value={form.gsmNumber}
            />
            <label className="block">
              <span className="text-sm font-medium">Sektör</span>
              <select
                className="mt-1 h-10 w-full border border-zinc-300 bg-white px-3 text-sm"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    sector: event.target.value as CreateTenantForm["sector"]
                  }))
                }
                value={form.sector}
              >
                <option value="cafe">Kafe</option>
                <option value="">Seçilmeyecek</option>
              </select>
            </label>
            <FieldText
              label="Kapasite"
              onChange={(value) => setForm((current) => ({ ...current, capacity: value }))}
              type="number"
              value={form.capacity}
            />
            <label className="block">
              <span className="text-sm font-medium">Adres</span>
              <textarea
                className="mt-1 min-h-24 w-full resize-none border border-zinc-300 px-3 py-2 text-sm"
                onChange={(event) =>
                  setForm((current) => ({ ...current, address: event.target.value }))
                }
                value={form.address}
              />
            </label>

            {state === "error" ? <StateBlock title={error ?? "Tenant oluşturulamadı"} tone="error" /> : null}
            {state === "success" && result ? (
              <div className="border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-950">
                <p className="font-semibold">{result.subdomain}.iotables.net</p>
                <p className="mt-1">Durum: {result.status}</p>
                <p className="mt-1">Starter veri: {result.starterTemplateApplied ? "uygulandı" : "yok"}</p>
              </div>
            ) : null}
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-zinc-200 px-5 py-4">
            {state === "success" && result ? (
              <button
                className="h-10 bg-emerald-700 px-4 text-sm font-medium text-white hover:bg-emerald-800"
                onClick={() => onCreated(result)}
                type="button"
              >
                Listeye dön
              </button>
            ) : (
              <button
                className="h-10 bg-zinc-950 px-4 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-300"
                disabled={!canSubmit || state === "submitting"}
                type="submit"
              >
                {state === "submitting" ? "Oluşturuluyor" : "Tenant oluştur"}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}

function FieldText({
  label,
  onChange,
  required = false,
  type = "text",
  value
}: {
  label: string;
  onChange: (value: string) => void;
  required?: boolean;
  type?: "number" | "password" | "text";
  value: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium">
        {label}
        {required ? " *" : ""}
      </span>
      <input
        className="mt-1 h-10 w-full border border-zinc-300 px-3 text-sm"
        onChange={(event) => onChange(event.target.value)}
        type={type}
        value={value}
      />
    </label>
  );
}

function StatusBadge({ value }: { value: string }) {
  const label = value.replaceAll("_", " ");
  const tone = value.includes("failed") || value.includes("not_ready") ? "amber" : "emerald";
  const className =
    tone === "amber"
      ? "border-amber-200 bg-amber-50 text-amber-900"
      : "border-emerald-200 bg-emerald-50 text-emerald-900";

  return (
    <span
      className={`inline-flex min-h-7 max-w-full items-center border px-2 py-1 text-xs font-medium ${className}`}
    >
      <span className="truncate">{label}</span>
    </span>
  );
}

function StateBlock({ title, tone = "neutral" }: { title: string; tone?: "error" | "neutral" }) {
  return (
    <div
      className={`px-4 py-8 text-sm ${
        tone === "error" ? "bg-rose-50 text-rose-900" : "text-zinc-500"
      }`}
    >
      {title}
    </div>
  );
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: "include",
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    let payload: ApiErrorEnvelope = {};
    try {
      payload = (await response.json()) as ApiErrorEnvelope;
    } catch {
      payload = {};
    }
    throw new Error(payload.error?.message ?? "İstek tamamlanamadı.");
  }

  return (await response.json()) as T;
}

function errorMessageFrom(error: unknown): string {
  return error instanceof Error ? error.message : "İstek tamamlanamadı.";
}

function auditMetadataSummary(metadata: Record<string, unknown>): string {
  const changedFields = metadata.changedFields;
  if (Array.isArray(changedFields) && changedFields.length > 0) {
    return `Değişen alanlar: ${changedFields.join(", ")}`;
  }
  const keys = Object.keys(metadata);
  return keys.length > 0 ? keys.join(", ") : "Ek detay yok";
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

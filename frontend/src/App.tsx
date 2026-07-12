import { FormEvent, useEffect, useMemo, useState } from "react";
import QRCode from "qrcode";

type TenantHealthSummary = {
  tenantId: string;
  name: string;
  subdomain: string;
  status: string;
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

type TenantContext = {
  tenantId: string;
  name: string;
  subdomain: string;
  status: string;
  sector: string | null;
  capacity: number | null;
  address: string | null;
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
};

type ProvisioningState = {
  tenantId: string;
  tenantStatus: string;
  starterApplicationStatus: string;
  templateKey: string | null;
  templateVersion: number | null;
  failureSummary: string | null;
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
  actor: AuthenticatedActor | null;
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

type FirstPasswordSetupState = {
  status: string;
  setupToken: string;
  otpRequired: boolean;
  otpChallengeId: string | null;
  targetHint: string | null;
  expiresAt: string | null;
  remainingAttempts: number | null;
};

type VenueTable = {
  tableId: string;
  hallId: string;
  tableNumber: number;
  name: string;
  displayOrder: number;
  mode: "virtual_test" | "physical" | string;
  systemBoundarySlot: boolean;
  enabled: boolean;
};

type HallWithTables = {
  hallId: string;
  name: string;
  displayOrder: number;
  tableNumberBase: number;
  enabled: boolean;
  tables: VenueTable[];
};

type HallTableBoard = {
  halls: HallWithTables[];
  derivedAt: string;
};

type Station = {
  stationId: string;
  name: string;
  displayOrder: number;
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
};

type StationList = {
  items: Station[];
};

type StaffProfile = {
  userId: string;
  username: string;
  displayName: string;
  status: string;
  roles: string[];
  stationIds: string[];
  hallIds: string[];
  firstPasswordRequired: boolean;
  createdAt: string;
  updatedAt: string;
};

type StaffList = {
  items: StaffProfile[];
};

type ProductVariant = {
  variantId: string;
  productId: string;
  name: string;
  priceMinor: number;
  currencyCode: string;
  displayOrder: number;
  isDefault: boolean;
  enabled: boolean;
};

type ModifierOption = {
  optionId: string;
  groupId: string;
  name: string;
  priceDeltaMinor: number;
  currencyCode: string;
  available: boolean;
  displayOrder: number;
};

type ModifierGroup = {
  groupId: string;
  productId: string;
  name: string;
  required: boolean;
  minSelections: number;
  maxSelections: number;
  displayOrder: number;
  options: ModifierOption[];
};

type AvailabilityOverride = {
  overrideId: string;
  productId: string;
  variantId: string | null;
  state: "available" | "unavailable";
  reason: string | null;
  startsAt: string | null;
  endsAt: string | null;
  createdAt: string;
};

type ProductService = {
  productId: string;
  categoryId: string;
  stationId: string;
  name: string;
  description: string | null;
  enabled: boolean;
  variants: ProductVariant[];
  modifierGroups: ModifierGroup[];
  availability: AvailabilityOverride[];
  createdAt: string;
  updatedAt: string;
};

type MenuCategory = {
  categoryId: string;
  name: string;
  displayOrder: number;
  enabled: boolean;
  products: ProductService[];
  createdAt: string;
  updatedAt: string;
};

type MenuSetupCatalog = {
  categories: MenuCategory[];
  derivedAt: string;
};

type CustomerMenuVariant = {
  variantId: string;
  name: string;
  priceMinor: number;
  currencyCode: string;
  displayOrder: number;
  isDefault: boolean;
};

type CustomerMenuOption = {
  optionId: string;
  name: string;
  priceDeltaMinor: number;
  currencyCode: string;
  displayOrder: number;
};

type CustomerMenuModifierGroup = {
  groupId: string;
  name: string;
  required: boolean;
  minSelections: number;
  maxSelections: number;
  displayOrder: number;
  options: CustomerMenuOption[];
};

type CustomerMenuProduct = {
  productId: string;
  categoryId: string;
  name: string;
  description: string | null;
  variants: CustomerMenuVariant[];
  modifierGroups: CustomerMenuModifierGroup[];
};

type CustomerMenuCategory = {
  categoryId: string;
  name: string;
  displayOrder: number;
  products: CustomerMenuProduct[];
};

type CustomerMenu = {
  categories: CustomerMenuCategory[];
  derivedAt: string;
};

type PresenceRedeemResult = {
  customerOrderingSessionId: string;
  tableId: string;
  hallId: string;
  freshUntil: string;
  cartPreserved: boolean;
};

type PresenceState = {
  customerOrderingSessionId: string;
  tableId: string;
  hallId: string;
  freshUntil: string;
  fresh: boolean;
};

type CartItem = {
  clientCartItemId: string;
  productId: string;
  variantId: string;
  quantity: number;
  modifierOptionIds: string[];
  note: string | null;
  estimatedPriceMinor: number;
};

type CustomerCart = {
  cartId: string;
  version: string;
  items: CartItem[];
  displaySubtotalMinor: number;
  currency: string;
  updatedAt: string;
};

type ServiceReadyItem = {
  orderItemId: string;
  preparationItemId: string;
  tableId: string;
  hallId: string;
  tableLabel: string;
  itemLabel: string;
  quantity: number;
  preparationReadyAt: string;
  deliveryStatus: "picked_up" | "delivered" | null;
};

type ServiceReadyItemList = {
  items: ServiceReadyItem[];
};

type DeliveryState = {
  orderItemId: string;
  preparationItemId: string;
  status: "picked_up" | "delivered";
  pickedUpAt: string | null;
  deliveredAt: string | null;
  actorDisplayName: string | null;
};

type BulkDeliveryResult = {
  tableId: string;
  deliveredItems: DeliveryState[];
  alreadyDeliveredItems: string[];
  deliveredAt: string;
  actorDisplayName: string | null;
  duplicate: boolean;
};

type CashierTableState = {
  tableId: string;
  hallId: string;
  tableLabel: string;
  hallLabel: string;
  mode: "virtual_test" | "physical" | string;
  tableSessionId: string | null;
  checkId: string | null;
  status: "empty" | "occupied" | string;
  openedAt: string | null;
  totalMinor: number;
  paidMinor: number;
  remainingMinor: number;
};

type CashierVenueBoard = {
  tables: CashierTableState[];
  derivedAt: string;
};

type QrTokenPreview = {
  qrToken: string;
  expiresAt: string;
  refreshAfterSeconds: number;
};

type DisplayFirmwareCreated = {
  firmwareId: string;
  fileName: string;
  credentialId: string;
  tableId: string;
  expiresAt: string;
  firmwareContent: string;
};

type BillSummary = {
  checkId: string;
  tableSessionId: string;
  totalMinor: number;
  paidMinor: number;
  remainingMinor: number;
  currency: string;
  orderCount: number;
  paymentCount: number;
};

type CashierPayment = {
  paymentId: string;
  checkId: string;
  tableSessionId: string;
  amountMinor: number;
  currency: string;
  method: "cash" | "card" | "transfer" | string;
  status: string;
  recordedAt: string;
  voidedAt: string | null;
};

type PaymentList = {
  items: CashierPayment[];
};

type PaymentResult = {
  payment: CashierPayment;
  paidMinor: number;
  remainingMinor: number;
  duplicate: boolean;
};

type PaymentVoidResult = {
  payment: CashierPayment;
  paidMinor: number;
  remainingMinor: number;
  correctionId: string;
  duplicate: boolean;
};

type CashierOrderItem = {
  orderItemId: string;
  name: string;
  variantName: string;
  quantity: number;
  unitPriceMinor: number;
  currency: string;
  note: string | null;
  voided: boolean;
};

type CashierOrder = {
  orderId: string;
  tableSessionId: string;
  submittedAt: string;
  items: CashierOrderItem[];
};

type CashierOrderList = {
  items: CashierOrder[];
};

type ApiErrorEnvelope = {
  error?: {
    code?: string;
    message?: string;
    requestId?: string;
    fieldErrors?: { path: string; message: string }[];
  };
};

class ApiRequestError extends Error {
  code: string;
  requestId: string | null;
  fieldErrors: { path: string; message: string }[];

  constructor(envelope: ApiErrorEnvelope) {
    const error = envelope.error ?? {};
    const code = error.code ?? "request_failed";
    super(error.message ?? "Request failed.");
    this.name = "ApiRequestError";
    this.code = code;
    this.requestId = error.requestId ?? null;
    this.fieldErrors = error.fieldErrors ?? [];
  }
}

type CreateTenantForm = {
  name: string;
  subdomain: string;
  gsmNumber: string;
  sector: "cafe" | "";
  capacity: string;
  address: string;
};

type TenantCreationOtpState = {
  otpChallengeId: string;
  targetHint: string;
  expiresAt: string;
  remainingAttempts: number;
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
  const appSurface = detectAppSurface();

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
  const [tenantContextState, setTenantContextState] = useState<
    "idle" | "checking" | "ready" | "unavailable"
  >("idle");
  const [tenantContext, setTenantContext] = useState<TenantContext | null>(null);

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
        `/api/platform/tenants?${params.toString()}`
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
        const payload = await apiRequest<SessionResponse>("/api/auth/session");
        if (active) {
          setActor(payload.actor);
          setAuthState(payload.actor ? "authenticated" : "anonymous");
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
    if (!requiresTenantContext(appSurface)) {
      setTenantContextState("idle");
      setTenantContext(null);
      return;
    }

    let active = true;
    async function loadTenantContext() {
      setTenantContextState("checking");
      try {
        const payload = await apiRequest<TenantContext>("/api/tenant/context", {
          headers: tenantHeaders()
        });
        if (active) {
          setTenantContext(payload);
          setTenantContextState(payload.status === "active" ? "ready" : "unavailable");
        }
      } catch {
        if (active) {
          setTenantContext(null);
          setTenantContextState("unavailable");
        }
      }
    }

    void loadTenantContext();
    return () => {
      active = false;
    };
  }, [appSurface]);

  useEffect(() => {
    if (authState === "authenticated" && appSurface === "platform") {
      void loadTenants();
    }
  }, [authState, appSurface]);

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
          `/api/platform/tenants/${selectedTenantId}`
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
      suspended: tenants.filter((tenant) => tenant.status === "suspended").length
    };
  }, [tenants]);

  async function logout() {
    await apiRequest("/api/auth/logout", {
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

  if (tenantContextState === "checking") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-stone-100 text-zinc-950">
        <StateBlock title="İşletme durumu kontrol ediliyor" />
      </main>
    );
  }

  if (tenantContextState === "unavailable") {
    return <TenantUnavailableScreen />;
  }

  if (appSurface === "customer") {
    return <CustomerMenuApp />;
  }

  if (appSurface === "tenant-public") {
    return <TenantPublicScreen tenant={tenantContext} />;
  }

  if (authState === "anonymous") {
    const handleAuthenticated = (nextActor: AuthenticatedActor) => {
      setActor(nextActor);
      setAuthState("authenticated");
    };
    return isTenantLoginSurface(appSurface) ? (
      <TenantLoginScreen
        appScope={tenantLoginScopeForSurface(appSurface)}
        defaultUsername={tenantLoginDefaultUsername(appSurface)}
        heading={tenantLoginHeading(appSurface)}
        tenantName={tenantContext?.name ?? tenantSubdomainFromLocation()}
        onAuthenticated={handleAuthenticated}
      />
    ) : (
      <PlatformLoginScreen onAuthenticated={handleAuthenticated} />
    );
  }

  if (
    isTenantLoginSurface(appSurface) &&
    actor?.appScope !== tenantLoginScopeForSurface(appSurface)
  ) {
    return (
      <TenantLoginScreen
        appScope={tenantLoginScopeForSurface(appSurface)}
        defaultUsername={tenantLoginDefaultUsername(appSurface)}
        heading={tenantLoginHeading(appSurface)}
        tenantName={tenantContext?.name ?? tenantSubdomainFromLocation()}
        onAuthenticated={(nextActor) => {
          setActor(nextActor);
          setAuthState("authenticated");
        }}
      />
    );
  }

  if (appSurface === "service") {
    return <ServiceStaffSignedInScreen actor={actor} onLogout={() => void logout()} />;
  }

  if (appSurface === "station") {
    return <StationStaffSignedInScreen actor={actor} onLogout={() => void logout()} />;
  }

  if (appSurface === "cashier") {
    return <CashierSignedInScreen actor={actor} onLogout={() => void logout()} />;
  }

  if (appSurface === "tenant") {
    return <TenantSignedInScreen actor={actor} onLogout={() => void logout()} />;
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
                <Metric label="Askıda" value={counters.suspended} />
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
                        className={`grid w-full gap-3 px-4 py-4 text-left hover:bg-zinc-50 md:grid-cols-[minmax(0,1.4fr)_120px_140px] ${
                          selectedTenantId === tenant.tenantId ? "bg-emerald-50" : "bg-white"
                        }`}
                        key={tenant.tenantId}
                        onClick={() => setSelectedTenantId(tenant.tenantId)}
                        type="button"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold">{tenant.name}</p>
                          <p className="mt-1 truncate text-xs text-zinc-500">
                            {tenantHost(tenant.subdomain)}
                          </p>
                        </div>
                        <StatusBadge value={tenant.status} />
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

function PlatformLoginScreen({
  onAuthenticated
}: {
  onAuthenticated: (actor: AuthenticatedActor) => void;
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [state, setState] = useState<"idle" | "submitting" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const canSubmit = Boolean(username.trim() && password);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit || state === "submitting") {
      return;
    }

    setState("submitting");
    setError(null);
    try {
      const result = await apiRequest<LoginResponse>("/api/auth/login", {
        body: JSON.stringify({
          appScope: "platform",
          username: username.trim(),
          password
        }),
        headers: {"Content-Type": "application/json"},
        method: "POST"
      });
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

function TenantLoginScreen({
  appScope,
  defaultUsername,
  heading,
  tenantName,
  onAuthenticated
}: {
  appScope: "cashier" | "service" | "station" | "tenant";
  defaultUsername: string;
  heading: string;
  tenantName: string;
  onAuthenticated: (actor: AuthenticatedActor) => void;
}) {
  const [username, setUsername] = useState(defaultUsername);
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [setupState, setSetupState] = useState<FirstPasswordSetupState | null>(null);
  const [setupToken, setSetupToken] = useState<string | null>(null);
  const [state, setState] = useState<"idle" | "submitting" | "setup" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  const loginReady = Boolean(username.trim() && password && state !== "submitting");
  const setupReady = Boolean(
    setupToken &&
      newPassword.length >= 8 &&
      (!setupState?.otpRequired || (setupState.otpChallengeId && otpCode.trim().length === 6)) &&
      state !== "submitting"
  );

  async function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!loginReady) {
      return;
    }

    setState("submitting");
    setError(null);
    try {
      const result = await apiRequest<LoginResponse>("/api/auth/login", {
        body: JSON.stringify({
          appScope,
          username: username.trim(),
          password
        }),
        headers: {
          "Content-Type": "application/json",
          ...tenantHeaders()
        },
        method: "POST"
      });
      if (result.status === "first_password_required" && result.setupToken) {
        const beginResult = await apiRequest<FirstPasswordSetupState>(
          "/api/auth/first-password/begin",
          {
            body: JSON.stringify({setupToken: result.setupToken}),
            headers: {"Content-Type": "application/json"},
            method: "POST"
          }
        );
        setSetupToken(result.setupToken);
        setSetupState(beginResult);
        setState("setup");
        return;
      }
      if (result.status !== "authenticated" || result.actor === null) {
        throw new Error("Tenant erişimi tamamlanamadı.");
      }
      onAuthenticated(result.actor);
    } catch (loginError) {
      setError(errorMessageFrom(loginError));
      setState("error");
    }
  }

  async function completeSetup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!setupReady || setupToken === null) {
      return;
    }

    setState("submitting");
    setError(null);
    try {
      const result = await apiRequest<LoginResponse>("/api/auth/first-password/complete", {
        body: JSON.stringify(
          setupState?.otpRequired
            ? {
                setupToken,
                newPassword,
                otpChallengeId: setupState.otpChallengeId,
                otpCode
              }
            : {
                setupToken,
                newPassword
              }
        ),
        headers: {"Content-Type": "application/json"},
        method: "POST"
      });
      if (result.status !== "authenticated" || result.actor === null) {
        throw new Error("İlk şifre kurulumu tamamlanamadı.");
      }
      onAuthenticated(result.actor);
    } catch (setupError) {
      setError(errorMessageFrom(setupError));
      setState("setup");
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-stone-100 px-4 text-zinc-950">
      <section className="w-full max-w-sm border border-zinc-200 bg-white">
        <div className="border-b border-zinc-200 px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
            {tenantName}
          </p>
          <h1 className="mt-2 text-2xl font-semibold">{heading}</h1>
        </div>
        {setupState ? (
          <form className="space-y-4 px-5 py-5" onSubmit={(event) => void completeSetup(event)}>
            <div className="border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-950">
              <p className="font-semibold">
                {setupState.otpRequired ? "SMS doğrulaması gerekli" : "İlk şifre değişimi gerekli"}
              </p>
              {setupState.otpRequired ? (
                <>
                  <p className="mt-1">Kod gönderilen GSM: {setupState.targetHint ?? "gizli"}</p>
                  <p className="mt-1">Kalan deneme: {setupState.remainingAttempts ?? "-"}</p>
                </>
              ) : null}
            </div>
            <FieldText
              label="Yeni şifre"
              onChange={setNewPassword}
              required
              type="password"
              value={newPassword}
            />
            {setupState.otpRequired ? (
              <FieldText label="SMS kodu" onChange={setOtpCode} required value={otpCode} />
            ) : null}
            {error ? <StateBlock title={error} tone="error" /> : null}
            <button
              className="h-10 w-full bg-zinc-950 px-4 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-300"
              disabled={!setupReady}
              type="submit"
            >
              {state === "submitting" ? "Tamamlanıyor" : "Şifreyi değiştir ve gir"}
            </button>
          </form>
        ) : (
          <form className="space-y-4 px-5 py-5" onSubmit={(event) => void submitLogin(event)}>
            <FieldText label="Kullanıcı adı" onChange={setUsername} required value={username} />
            <FieldText
              label="Şifre"
              onChange={setPassword}
              required
              type="password"
              value={password}
            />
            {error ? <StateBlock title={error} tone="error" /> : null}
            <button
              className="h-10 w-full bg-zinc-950 px-4 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-300"
              disabled={!loginReady}
              type="submit"
            >
              {state === "submitting" ? "Giriş yapılıyor" : "Giriş yap"}
            </button>
          </form>
        )}
      </section>
    </main>
  );
}

function TenantUnavailableScreen() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-stone-100 px-4 text-zinc-950">
      <section className="w-full max-w-sm border border-zinc-200 bg-white px-5 py-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
          {tenantHost(tenantSubdomainFromLocation())}
        </p>
        <h1 className="mt-2 text-2xl font-semibold">İşletme bulunamadı</h1>
        <p className="mt-3 text-sm text-zinc-600">
          Bu tenant adresi aktif bir işletmeye bağlı değil veya şu anda kullanılamıyor.
        </p>
      </section>
    </main>
  );
}

function TenantPublicScreen({ tenant }: { tenant: TenantContext | null }) {
  return (
    <main className="min-h-screen bg-stone-100 text-zinc-950">
      <section className="mx-auto flex min-h-screen w-full max-w-3xl flex-col justify-center px-5 py-10">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
          {tenant?.subdomain
            ? tenantHost(tenant.subdomain)
            : tenantHost(tenantSubdomainFromLocation())}
        </p>
        <h1 className="mt-3 text-3xl font-semibold">{tenant?.name ?? "İşletme bilgileri"}</h1>
        <div className="mt-6 grid gap-3 text-sm sm:grid-cols-3">
          <div className="border border-zinc-200 bg-white px-4 py-3">
            <p className="text-zinc-500">Sektör</p>
            <p className="mt-1 font-medium">
              {tenant?.sector === "cafe" ? "Kafe" : "Belirtilmedi"}
            </p>
          </div>
          <div className="border border-zinc-200 bg-white px-4 py-3">
            <p className="text-zinc-500">Kapasite</p>
            <p className="mt-1 font-medium">{tenant?.capacity ?? "Belirtilmedi"}</p>
          </div>
          <div className="border border-zinc-200 bg-white px-4 py-3">
            <p className="text-zinc-500">Durum</p>
            <p className="mt-1 font-medium">Siparişe hazır</p>
          </div>
        </div>
        {tenant?.address ? (
          <div className="mt-3 border border-zinc-200 bg-white px-4 py-3 text-sm">
            <p className="text-zinc-500">Adres</p>
            <p className="mt-1 font-medium">{tenant.address}</p>
          </div>
        ) : null}
      </section>
    </main>
  );
}

function ForbiddenScreen({ appName, onLogout }: { appName: string; onLogout: () => void }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-stone-100 px-4 text-zinc-950">
      <section className="w-full max-w-sm border border-zinc-200 bg-white px-5 py-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">{appName}</p>
        <h1 className="mt-2 text-2xl font-semibold">Yetkisiz oturum</h1>
        <p className="mt-3 text-sm text-zinc-600">Bu oturum bu uygulama yüzeyine erişemez.</p>
        <button
          className="mt-5 h-10 border border-zinc-950 bg-zinc-950 px-4 text-sm font-medium text-white"
          onClick={onLogout}
          type="button"
        >
          Çıkış yap
        </button>
      </section>
    </main>
  );
}

function TenantSignedInScreen({
  actor,
  onLogout
}: {
  actor: AuthenticatedActor | null;
  onLogout: () => void;
}) {
  const [tenant, setTenant] = useState<TenantProfile | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error" | "forbidden">("loading");
  const [activeWorkspace, setActiveWorkspace] = useState<TenantWorkspaceKey>(
    tenantWorkspaceFromPath(window.location.pathname)
  );

  useEffect(() => {
    let active = true;
    async function loadTenantProfile() {
      if (actor?.appScope !== "tenant" || !actor.roles.includes("tenant_admin")) {
        setState("forbidden");
        return;
      }
      setState("loading");
      try {
        const payload = await apiRequest<TenantProfile>("/api/tenant/profile");
        if (active) {
          setTenant(payload);
          setState("ready");
        }
      } catch {
        if (active) {
          setTenant(null);
          setState("error");
        }
      }
    }

    void loadTenantProfile();
    return () => {
      active = false;
    };
  }, [actor?.appScope, actor?.tenantId, actor?.roles.join("|")]);

  function selectWorkspace(workspace: TenantWorkspaceKey) {
    setActiveWorkspace(workspace);
    window.history.replaceState(null, "", tenantWorkspacePath(workspace));
  }

  return (
    <main className="min-h-screen bg-stone-100 text-zinc-950">
      <section className="flex min-h-screen">
        <aside className="hidden w-64 border-r border-zinc-200 bg-white px-5 py-6 lg:block">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
              TenantApp
            </p>
            <h1 className="mt-2 text-2xl font-semibold">{tenant?.name ?? "Tenant"}</h1>
            <p className="mt-1 break-all text-xs text-zinc-500">
              {tenantHost(tenant?.subdomain ?? tenantSubdomainFromLocation())}
            </p>
          </div>
          <nav className="mt-8 space-y-1 text-sm">
            {tenantWorkspaces.map((workspace) => (
              <button
                className={`w-full border-l-4 px-3 py-2 text-left font-medium ${
                  activeWorkspace === workspace.key
                    ? "border-emerald-600 bg-emerald-50 text-emerald-950"
                    : "border-transparent hover:bg-zinc-50"
                }`}
                key={workspace.key}
                onClick={() => selectWorkspace(workspace.key)}
                type="button"
              >
                {workspace.label}
              </button>
            ))}
          </nav>
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          <header className="border-b border-zinc-200 bg-white px-4 py-4 sm:px-6">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                  {tenantWorkspaceLabel(activeWorkspace)}
                </p>
                <h2 className="text-2xl font-semibold">{tenant?.name ?? "Tenant yönetimi"}</h2>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge value={tenant?.status ?? "loading"} />
                <button
                  className="h-10 border border-zinc-300 px-4 text-sm font-medium hover:bg-zinc-50"
                  onClick={onLogout}
                  type="button"
                >
                  Çıkış yap
                </button>
              </div>
            </div>
            <div className="mt-4 flex gap-2 overflow-x-auto lg:hidden">
              {tenantWorkspaces.map((workspace) => (
                <button
                  className={`h-9 shrink-0 border px-3 text-sm font-medium ${
                    activeWorkspace === workspace.key
                      ? "border-emerald-600 bg-emerald-50 text-emerald-950"
                      : "border-zinc-300 bg-white"
                  }`}
                  key={workspace.key}
                  onClick={() => selectWorkspace(workspace.key)}
                  type="button"
                >
                  {workspace.label}
                </button>
              ))}
            </div>
          </header>

          <div className="flex-1 px-4 py-5 sm:px-6">
            {state === "loading" ? (
              <StateBlock title="Tenant bilgileri yükleniyor" />
            ) : state === "forbidden" ? (
              <StateBlock title="Bu oturum Tenant Admin yetkisine sahip değil" tone="error" />
            ) : state === "error" || tenant === null ? (
              <StateBlock title="Tenant profili alınamadı" tone="error" />
            ) : (
              <TenantWorkspace workspace={activeWorkspace} tenant={tenant} actor={actor} />
            )}
          </div>
        </section>
      </section>
    </main>
  );
}

function StationStaffSignedInScreen({
  actor,
  onLogout
}: {
  actor: AuthenticatedActor | null;
  onLogout: () => void;
}) {
  if (actor?.appScope !== "station" || !actor.roles.includes("station_staff")) {
    return <ForbiddenScreen appName="StationStaffApp" onLogout={onLogout} />;
  }

  return (
    <main className="min-h-screen bg-stone-100 text-zinc-950">
      <header className="border-b border-zinc-200 bg-white px-5 py-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              StationStaffApp
            </p>
            <h1 className="text-2xl font-semibold">İstasyon kuyruğu</h1>
          </div>
          <button
            className="h-10 border border-zinc-300 px-4 text-sm font-medium hover:bg-zinc-50"
            onClick={onLogout}
            type="button"
          >
            Çıkış yap
          </button>
        </div>
      </header>
      <section className="px-5 py-5">
        <StateBlock title="Yetkili istasyon seçimi ve kuyruk verisi yüklenmeyi bekliyor." />
      </section>
    </main>
  );
}

function ServiceStaffSignedInScreen({
  actor,
  onLogout
}: {
  actor: AuthenticatedActor | null;
  onLogout: () => void;
}) {
  const [items, setItems] = useState<ServiceReadyItem[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error" | "forbidden">("loading");
  const [actionState, setActionState] = useState<"idle" | "submitting" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [selectedItemIds, setSelectedItemIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    let active = true;
    async function load() {
      if (actor?.appScope !== "service" || !actor.roles.includes("service_staff")) {
        setState("forbidden");
        return;
      }
      setState("loading");
      try {
        const payload = await apiRequest<ServiceReadyItemList>("/api/service-staff/ready-items", {
          headers: tenantHeaders()
        });
        if (active) {
          setItems(payload.items);
          setSelectedItemIds(new Set());
          setState("ready");
        }
      } catch (requestError) {
        if (active) {
          setError(errorMessageFrom(requestError));
          setState("error");
        }
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [actor?.appScope, actor?.roles.join("|")]);

  async function loadItems() {
    setError(null);
    try {
      const payload = await apiRequest<ServiceReadyItemList>("/api/service-staff/ready-items", {
        headers: tenantHeaders()
      });
      setItems(payload.items);
      setSelectedItemIds(new Set());
      setState("ready");
    } catch (requestError) {
      setError(errorMessageFrom(requestError));
      setState("error");
    }
  }

  async function transitionItem(orderItemId: string, action: "deliver" | "pick-up") {
    if (actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setError(null);
    try {
      await apiRequest<DeliveryState>(`/api/service-staff/items/${orderItemId}/${action}`, {
        headers: {
          "X-CSRF-Token": crypto.randomUUID(),
          ...tenantHeaders()
        },
        method: "POST"
      });
      await loadItems();
      setActionState("idle");
    } catch (requestError) {
      setError(errorMessageFrom(requestError));
      setActionState("error");
    }
  }

  async function bulkDeliver() {
    const selectedItems = items.filter((item) => selectedItemIds.has(item.orderItemId));
    const tableId = selectedItems[0]?.tableId;
    if (!tableId || selectedItems.some((item) => item.tableId !== tableId)) {
      setError("Toplu teslim için aynı masadan ürün seçin.");
      return;
    }
    if (actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setError(null);
    try {
      await apiRequest<BulkDeliveryResult>("/api/service-staff/items/bulk-deliver", {
        body: JSON.stringify({
          tableId,
          orderItemIds: selectedItems.map((item) => item.orderItemId)
        }),
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
          "X-CSRF-Token": crypto.randomUUID(),
          ...tenantHeaders()
        },
        method: "POST"
      });
      await loadItems();
      setActionState("idle");
    } catch (requestError) {
      setError(errorMessageFrom(requestError));
      setActionState("error");
    }
  }

  function toggleSelected(item: ServiceReadyItem) {
    setSelectedItemIds((current) => {
      const next = new Set(current);
      if (next.has(item.orderItemId)) {
        next.delete(item.orderItemId);
      } else {
        next.add(item.orderItemId);
      }
      return next;
    });
  }

  const groupedItems = useMemo(() => {
    const groups = new Map<string, ServiceReadyItem[]>();
    for (const item of items) {
      groups.set(item.tableId, [...(groups.get(item.tableId) ?? []), item]);
    }
    return Array.from(groups.entries()).map(([tableId, groupItems]) => ({
      tableId,
      tableLabel: groupItems[0]?.tableLabel ?? "Masa",
      items: groupItems
    }));
  }, [items]);

  const selectedItems = items.filter((item) => selectedItemIds.has(item.orderItemId));
  const selectedTableIds = new Set(selectedItems.map((item) => item.tableId));
  const canBulkDeliver =
    selectedItems.length > 0 && selectedTableIds.size === 1 && actionState !== "submitting";

  return (
    <main className="min-h-screen bg-stone-100 text-zinc-950">
      <header className="border-b border-zinc-200 bg-white px-4 py-4 sm:px-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              ServiceStaffApp
            </p>
            <h1 className="text-2xl font-semibold">Servis kuyruğu</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-zinc-500">{actor?.displayName ?? "Servis"}</span>
            <button
              className="h-10 border border-zinc-300 px-4 text-sm font-medium hover:bg-zinc-50"
              onClick={() => void loadItems()}
              type="button"
            >
              Yenile
            </button>
            <button
              className="h-10 border border-zinc-300 px-4 text-sm font-medium hover:bg-zinc-50"
              onClick={onLogout}
              type="button"
            >
              Çıkış yap
            </button>
          </div>
        </div>
      </header>

      <section className="px-4 py-5 sm:px-6">
        <div className="mb-4 grid gap-3 md:grid-cols-3">
          <Metric label="Hazır" value={items.filter((item) => item.deliveryStatus === null).length} />
          <Metric
            label="Alındı"
            value={items.filter((item) => item.deliveryStatus === "picked_up").length}
          />
          <Metric label="Seçili" value={selectedItemIds.size} />
        </div>

        <div className="mb-4 flex flex-wrap items-center gap-2 border border-zinc-200 bg-white px-4 py-3">
          <button
            className="h-10 border border-zinc-950 bg-zinc-950 px-4 text-sm font-medium text-white disabled:cursor-not-allowed disabled:border-zinc-300 disabled:bg-zinc-300"
            disabled={!canBulkDeliver}
            onClick={() => void bulkDeliver()}
            type="button"
          >
            {actionState === "submitting" ? "İşleniyor" : "Seçilileri teslim et"}
          </button>
          {selectedItems.length > 0 && selectedTableIds.size !== 1 ? (
            <span className="text-sm text-amber-700">Seçimler aynı masadan olmalı.</span>
          ) : null}
        </div>

        {state === "loading" ? (
          <StateBlock title="Servis kuyruğu yükleniyor" />
        ) : state === "forbidden" ? (
          <StateBlock title="Bu oturum servis yetkisine sahip değil" tone="error" />
        ) : state === "error" ? (
          <StateBlock title={error ?? "Servis kuyruğu alınamadı"} tone="error" />
        ) : groupedItems.length === 0 ? (
          <StateBlock title="Teslim bekleyen ürün yok" />
        ) : (
          <div className="space-y-4">
            {groupedItems.map((group) => (
              <section className="border border-zinc-200 bg-white" key={group.tableId}>
                <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
                  <h2 className="text-base font-semibold">{group.tableLabel}</h2>
                  <span className="text-sm text-zinc-500">{group.items.length} ürün</span>
                </div>
                <div className="divide-y divide-zinc-200">
                  {group.items.map((item) => (
                    <div
                      className="grid gap-3 px-4 py-4 md:grid-cols-[44px_minmax(0,1fr)_140px_240px]"
                      key={item.orderItemId}
                    >
                      <input
                        aria-label={`${item.itemLabel} seç`}
                        checked={selectedItemIds.has(item.orderItemId)}
                        className="h-6 w-6 self-center"
                        onChange={() => toggleSelected(item)}
                        type="checkbox"
                      />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold">{item.itemLabel}</p>
                        <p className="mt-1 text-xs text-zinc-500">
                          {item.quantity} adet · hazır {formatDate(item.preparationReadyAt)}
                        </p>
                      </div>
                      <StatusBadge
                        value={item.deliveryStatus === "picked_up" ? "picked_up" : "ready"}
                      />
                      <div className="flex flex-wrap gap-2 md:justify-end">
                        <button
                          className="h-10 border border-zinc-300 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                          disabled={
                            item.deliveryStatus === "picked_up" || actionState === "submitting"
                          }
                          onClick={() => void transitionItem(item.orderItemId, "pick-up")}
                          type="button"
                        >
                          Alındı
                        </button>
                        <button
                          className="h-10 border border-zinc-950 bg-zinc-950 px-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:border-zinc-300 disabled:bg-zinc-300"
                          disabled={actionState === "submitting"}
                          onClick={() => void transitionItem(item.orderItemId, "deliver")}
                          type="button"
                        >
                          Teslim edildi
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
        {actionState === "error" && error ? <StateBlock title={error} tone="error" /> : null}
      </section>
    </main>
  );
}

function CashierSignedInScreen({
  actor,
  onLogout
}: {
  actor: AuthenticatedActor | null;
  onLogout: () => void;
}) {
  const [board, setBoard] = useState<CashierVenueBoard | null>(null);
  const [selectedTableId, setSelectedTableId] = useState<string | null>(null);
  const [billSummary, setBillSummary] = useState<BillSummary | null>(null);
  const [payments, setPayments] = useState<CashierPayment[]>([]);
  const [orders, setOrders] = useState<CashierOrder[]>([]);
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<"card" | "cash" | "transfer">("cash");
  const [showVirtualTables, setShowVirtualTables] = useState(false);
  const [qrPreview, setQrPreview] = useState<{
    tableId: string;
    dataUrl: string;
    expiresAt: string;
  } | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error" | "forbidden">("loading");
  const [actionState, setActionState] = useState<"idle" | "submitting" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (actor?.appScope !== "cashier" || !actor.roles.includes("cashier")) {
      setState("forbidden");
      return;
    }
    void loadBoard(showVirtualTables);
  }, [actor?.appScope, actor?.roles.join("|"), showVirtualTables]);

  useEffect(() => {
    const selected = board?.tables.find((table) => table.tableId === selectedTableId) ?? null;
    if (!selected?.tableSessionId || !selected.checkId) {
      setBillSummary(null);
      setPayments([]);
      setOrders([]);
      return;
    }
    void loadTableDetail(selected);
  }, [selectedTableId, board?.derivedAt]);

  async function loadBoard(includeVirtualTables = showVirtualTables) {
    setState("loading");
    setError(null);
    try {
      const query = includeVirtualTables ? "?includeVirtualTestTables=true" : "";
      const payload = await apiRequest<CashierVenueBoard>(`/api/cashier/venue/board${query}`, {
        headers: tenantHeaders()
      });
      setBoard(payload);
      setSelectedTableId((current) => current ?? payload.tables[0]?.tableId ?? null);
      setState("ready");
    } catch (requestError) {
      setError(errorMessageFrom(requestError));
      setState("error");
    }
  }

  async function createVirtualQrPreview(table: CashierTableState) {
    if (table.mode !== "virtual_test" || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setError(null);
    try {
      const payload = await apiRequest<QrTokenPreview>(
        `/api/cashier/virtual-tables/${table.tableId}/qr-preview`,
        {
          headers: {
            "X-CSRF-Token": crypto.randomUUID(),
            ...tenantHeaders()
          },
          method: "POST"
        }
      );
      const dataUrl = await QRCode.toDataURL(payload.qrToken, {
        errorCorrectionLevel: "M",
        margin: 1,
        scale: 8
      });
      setQrPreview({tableId: table.tableId, dataUrl, expiresAt: payload.expiresAt});
      setActionState("idle");
    } catch (requestError) {
      setError(errorMessageFrom(requestError));
      setActionState("error");
    }
  }

  async function loadTableDetail(table: CashierTableState) {
    if (!table.tableSessionId || !table.checkId) {
      return;
    }
    try {
      const [summaryPayload, paymentPayload, orderPayload] = await Promise.all([
        apiRequest<BillSummary>(`/api/cashier/table-sessions/${table.tableSessionId}/bill-summary`, {
          headers: tenantHeaders()
        }),
        apiRequest<PaymentList>(`/api/cashier/checks/${table.checkId}/payments`, {
          headers: tenantHeaders()
        }),
        apiRequest<CashierOrderList>(`/api/cashier/table-sessions/${table.tableSessionId}/orders`, {
          headers: tenantHeaders()
        })
      ]);
      setBillSummary(summaryPayload);
      setPayments(paymentPayload.items);
      setOrders(orderPayload.items);
    } catch (requestError) {
      setError(errorMessageFrom(requestError));
      setActionState("error");
    }
  }

  async function recordPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const selected = board?.tables.find((table) => table.tableId === selectedTableId) ?? null;
    const amountMinor = Number(paymentAmount);
    if (!selected?.checkId || !amountMinor || amountMinor <= 0 || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setError(null);
    try {
      const result = await apiRequest<PaymentResult>(
        `/api/cashier/checks/${selected.checkId}/payments`,
        {
          body: JSON.stringify({
            amountMinor,
            currency: billSummary?.currency ?? "TRY",
            method: paymentMethod
          }),
          headers: {
            "Content-Type": "application/json",
            "Idempotency-Key": crypto.randomUUID(),
            "X-CSRF-Token": crypto.randomUUID(),
            ...tenantHeaders()
          },
          method: "POST"
        }
      );
      setPaymentAmount("");
      setBillSummary((current) =>
        current
          ? {
              ...current,
              paidMinor: result.paidMinor,
              paymentCount: current.paymentCount + (result.duplicate ? 0 : 1),
              remainingMinor: result.remainingMinor
            }
          : current
      );
      await loadBoard();
      setActionState("idle");
    } catch (requestError) {
      setError(errorMessageFrom(requestError));
      setActionState("error");
    }
  }

  async function closeSession() {
    const selected = board?.tables.find((table) => table.tableId === selectedTableId) ?? null;
    if (!selected?.tableSessionId || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setError(null);
    try {
      await apiRequest(`/api/cashier/table-sessions/${selected.tableSessionId}/close`, {
        body: JSON.stringify({reason: null}),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID(),
          ...tenantHeaders()
        },
        method: "POST"
      });
      setBillSummary(null);
      setPayments([]);
      setOrders([]);
      await loadBoard();
      setActionState("idle");
    } catch (requestError) {
      setError(errorMessageFrom(requestError));
      setActionState("error");
    }
  }

  async function voidPayment(payment: CashierPayment) {
    const reason = window.prompt("Ödeme iptal nedeni");
    if (!reason?.trim() || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setError(null);
    try {
      const result = await apiRequest<PaymentVoidResult>(
        `/api/cashier/payments/${payment.paymentId}/void`,
        {
          body: JSON.stringify({reason: reason.trim()}),
          headers: {
            "Content-Type": "application/json",
            "Idempotency-Key": crypto.randomUUID(),
            "X-CSRF-Token": crypto.randomUUID(),
            ...tenantHeaders()
          },
          method: "POST"
        }
      );
      setBillSummary((current) =>
        current
          ? {
              ...current,
              paidMinor: result.paidMinor,
              paymentCount: Math.max(current.paymentCount - (result.duplicate ? 0 : 1), 0),
              remainingMinor: result.remainingMinor
            }
          : current
      );
      setPayments((current) =>
        current.map((item) =>
          item.paymentId === result.payment.paymentId ? result.payment : item
        )
      );
      await loadBoard();
      setActionState("idle");
    } catch (requestError) {
      setError(errorMessageFrom(requestError));
      setActionState("error");
    }
  }

  const selectedTable = board?.tables.find((table) => table.tableId === selectedTableId) ?? null;
  const occupiedTables = board?.tables.filter((table) => table.status === "occupied").length ?? 0;

  return (
    <main className="min-h-screen bg-stone-100 text-zinc-950">
      <header className="border-b border-zinc-200 bg-white px-4 py-4 sm:px-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">CashierApp</p>
            <h1 className="text-2xl font-semibold">Kasa</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-zinc-500">{actor?.displayName ?? "Kasiyer"}</span>
            <button
              className="h-10 border border-zinc-300 px-4 text-sm font-medium hover:bg-zinc-50"
              onClick={() => void loadBoard()}
              type="button"
            >
              Yenile
            </button>
            <label className="flex h-10 items-center gap-2 border border-zinc-300 px-3 text-sm font-medium">
              <input
                checked={showVirtualTables}
                onChange={(event) => {
                  setShowVirtualTables(event.target.checked);
                  setSelectedTableId(null);
                  setQrPreview(null);
                }}
                type="checkbox"
              />
              Sanal masalar
            </label>
            <button
              className="h-10 border border-zinc-300 px-4 text-sm font-medium hover:bg-zinc-50"
              onClick={onLogout}
              type="button"
            >
              Çıkış yap
            </button>
          </div>
        </div>
      </header>

      <section className="grid gap-5 px-4 py-5 sm:px-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <div className="min-w-0">
          <div className="mb-4 grid gap-3 md:grid-cols-3">
            <Metric label="Dolu masa" value={occupiedTables} />
            <Metric label="Toplam masa" value={board?.tables.length ?? 0} />
            <Metric label="Seçili bakiye" value={selectedTable?.remainingMinor ?? 0} />
          </div>

          {state === "loading" ? (
            <StateBlock title="Kasa board yükleniyor" />
          ) : state === "forbidden" ? (
            <StateBlock title="Bu oturum kasa yetkisine sahip değil" tone="error" />
          ) : state === "error" ? (
            <StateBlock title={error ?? "Kasa board alınamadı"} tone="error" />
          ) : board === null || board.tables.length === 0 ? (
            <StateBlock title="Masa yok" />
          ) : (
            <div className="grid gap-3 md:grid-cols-2 2xl:grid-cols-3">
              {board.tables.map((table) => (
                <button
                  className={`min-h-36 border px-4 py-4 text-left hover:bg-zinc-50 ${
                    table.mode === "virtual_test" ? "bg-slate-50" : "bg-white"
                  } ${
                    selectedTableId === table.tableId ? "border-emerald-600" : "border-zinc-200"
                  }`}
                  key={table.tableId}
                  onClick={() => setSelectedTableId(table.tableId)}
                  type="button"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h2 className="truncate text-base font-semibold">{table.tableLabel}</h2>
                      <p className="mt-1 truncate text-xs text-zinc-500">{table.hallLabel}</p>
                      {table.mode === "virtual_test" ? (
                        <p className="mt-2 text-xs font-medium text-slate-600">Sanal test masası</p>
                      ) : null}
                    </div>
                    <StatusBadge value={table.status} />
                  </div>
                  <div className="mt-5 grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <p className="text-zinc-500">Toplam</p>
                      <p className="mt-1 font-semibold">{table.totalMinor}</p>
                    </div>
                    <div>
                      <p className="text-zinc-500">Ödenen</p>
                      <p className="mt-1 font-semibold">{table.paidMinor}</p>
                    </div>
                    <div>
                      <p className="text-zinc-500">Kalan</p>
                      <p className="mt-1 font-semibold">{table.remainingMinor}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <aside className="border border-zinc-200 bg-white">
          <div className="border-b border-zinc-200 px-4 py-3">
            <h2 className="text-base font-semibold">{selectedTable?.tableLabel ?? "Masa seçin"}</h2>
            <p className="mt-1 text-xs text-zinc-500">{selectedTable?.hallLabel ?? "Hesap paneli"}</p>
          </div>
          {selectedTable === null ? (
            <StateBlock title="İşlem için masa seçin" />
          ) : selectedTable.mode === "virtual_test" ? (
            <div className="space-y-4 px-4 py-4">
              <StateBlock title="Sanal test masası" />
              <button
                className="h-10 w-full border border-zinc-950 px-4 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                disabled={actionState === "submitting"}
                onClick={() => void createVirtualQrPreview(selectedTable)}
                type="button"
              >
                Fresh QR oluştur
              </button>
              {qrPreview?.tableId === selectedTable.tableId ? (
                <div className="border border-zinc-200 px-4 py-4 text-center">
                  <img
                    alt={`${selectedTable.tableLabel} QR`}
                    className="mx-auto h-56 w-56"
                    src={qrPreview.dataUrl}
                  />
                  <p className="mt-3 text-xs text-zinc-500">
                    Geçerlilik: {new Date(qrPreview.expiresAt).toLocaleTimeString("tr-TR")}
                  </p>
                </div>
              ) : null}
            </div>
          ) : selectedTable.status !== "occupied" || billSummary === null ? (
            <StateBlock title="Bu masada açık oturum yok" />
          ) : (
            <div className="space-y-4 px-4 py-4">
              <DetailRows
                rows={[
                  ["Toplam", `${billSummary.totalMinor} ${billSummary.currency}`],
                  ["Ödenen", `${billSummary.paidMinor} ${billSummary.currency}`],
                  ["Kalan", `${billSummary.remainingMinor} ${billSummary.currency}`],
                  ["Sipariş", billSummary.orderCount.toString()],
                  ["Ödeme", billSummary.paymentCount.toString()]
                ]}
              />
              <form className="grid gap-2 border-t border-zinc-200 pt-4" onSubmit={recordPayment}>
                <input
                  className="h-10 border border-zinc-300 px-3 text-sm"
                  max={billSummary.remainingMinor}
                  min="1"
                  onChange={(event) => setPaymentAmount(event.target.value)}
                  placeholder="Tutar minor"
                  type="number"
                  value={paymentAmount}
                />
                <select
                  className="h-10 border border-zinc-300 bg-white px-3 text-sm"
                  onChange={(event) =>
                    setPaymentMethod(event.target.value as "card" | "cash" | "transfer")
                  }
                  value={paymentMethod}
                >
                  <option value="cash">Nakit</option>
                  <option value="card">Kart</option>
                  <option value="transfer">Transfer</option>
                </select>
                <button
                  className="h-10 border border-zinc-950 bg-zinc-950 px-4 text-sm font-medium text-white disabled:cursor-not-allowed disabled:border-zinc-300 disabled:bg-zinc-300"
                  disabled={
                    actionState === "submitting" ||
                    !paymentAmount ||
                    Number(paymentAmount) <= 0 ||
                    Number(paymentAmount) > billSummary.remainingMinor
                  }
                  type="submit"
                >
                  Ödeme al
                </button>
              </form>
              <button
                className="h-10 w-full border border-zinc-950 px-4 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:border-zinc-300 disabled:bg-zinc-100"
                disabled={actionState === "submitting" || billSummary.remainingMinor !== 0}
                onClick={() => void closeSession()}
                type="button"
              >
                Oturumu kapat
              </button>
              <div className="border-t border-zinc-200 pt-4">
                <h3 className="text-sm font-semibold">Siparişler</h3>
                {orders.length === 0 ? (
                  <p className="mt-2 text-sm text-zinc-500">Sipariş yok</p>
                ) : (
                  <div className="mt-2 max-h-56 divide-y divide-zinc-200 overflow-y-auto">
                    {orders.map((order) => (
                      <div className="py-2 text-sm" key={order.orderId}>
                        <p className="text-xs text-zinc-500">{formatDate(order.submittedAt)}</p>
                        <div className="mt-1 space-y-1">
                          {order.items.map((item) => (
                            <div
                              className="flex justify-between gap-3"
                              key={item.orderItemId}
                            >
                              <span className={item.voided ? "line-through text-zinc-400" : ""}>
                                {item.quantity} x {item.name}
                              </span>
                              <span className="font-medium">
                                {item.quantity * item.unitPriceMinor} {item.currency}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="border-t border-zinc-200 pt-4">
                <h3 className="text-sm font-semibold">Ödemeler</h3>
                {payments.length === 0 ? (
                  <p className="mt-2 text-sm text-zinc-500">Ödeme yok</p>
                ) : (
                  <div className="mt-2 divide-y divide-zinc-200">
                    {payments.map((payment) => (
                      <div className="py-2 text-sm" key={payment.paymentId}>
                        <div className="flex justify-between gap-3">
                          <span>
                            {payment.method} · {payment.status}
                          </span>
                          <span className="font-medium">
                            {payment.amountMinor} {payment.currency}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center justify-between gap-3">
                          <p className="text-xs text-zinc-500">
                            {payment.voidedAt
                              ? `İptal ${formatDate(payment.voidedAt)}`
                              : formatDate(payment.recordedAt)}
                          </p>
                          <button
                            className="h-8 border border-zinc-300 px-2 text-xs font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                            disabled={payment.status !== "recorded" || actionState === "submitting"}
                            onClick={() => void voidPayment(payment)}
                            type="button"
                          >
                            İptal et
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              {actionState === "error" && error ? <StateBlock title={error} tone="error" /> : null}
            </div>
          )}
        </aside>
      </section>
    </main>
  );
}

type TenantWorkspaceKey = "dashboard" | "halls" | "stations" | "menu" | "staff" | "settings";

const tenantWorkspaces: {key: TenantWorkspaceKey; label: string; path: string}[] = [
  {key: "dashboard", label: "Dashboard", path: "/admin"},
  {key: "halls", label: "Salonlar", path: "/admin/halls"},
  {key: "stations", label: "İstasyonlar", path: "/admin/stations"},
  {key: "menu", label: "Menü", path: "/admin/menu"},
  {key: "staff", label: "Personel", path: "/admin/staff"},
  {key: "settings", label: "Ayarlar", path: "/admin/settings"}
];

function TenantWorkspace({
  actor,
  tenant,
  workspace
}: {
  actor: AuthenticatedActor | null;
  tenant: TenantProfile;
  workspace: TenantWorkspaceKey;
}) {
  if (workspace === "dashboard") {
    return (
      <div className="space-y-5">
        <div className="grid gap-3 md:grid-cols-3">
          <Metric label="Starter veri" value={tenant.starterTemplateState === "applied" ? 1 : 0} />
          <Metric
            label="Admin bootstrap"
            value={tenant.tenantAdminBootstrapState === "completed" ? 1 : 0}
          />
          <Metric label="Lifecycle" value={tenant.status === "active" ? 1 : 0} />
        </div>
        <div className="border border-zinc-200 bg-white px-5 py-5">
          <h3 className="text-sm font-semibold">Kurulum özeti</h3>
          <DetailRows
            rows={[
              ["Tenant", tenant.name],
              ["Subdomain", tenantHost(tenant.subdomain)],
              ["Sektör", tenant.sector ?? "-"],
              ["Kapasite", tenant.capacity?.toString() ?? "-"],
              ["Oturum", actor?.roles.join(", ") || "-"]
            ]}
          />
        </div>
      </div>
    );
  }

  if (workspace === "halls") {
    return <HallManagementWorkspace />;
  }

  if (workspace === "stations") {
    return <StationManagementWorkspace />;
  }

  if (workspace === "menu") {
    return <MenuManagementWorkspace />;
  }

  if (workspace === "staff") {
    return <StaffManagementWorkspace />;
  }

  const copy: Record<TenantWorkspaceKey, [string, string]> = {
    dashboard: ["Dashboard", "Kurulum özeti."],
    halls: ["Salon ve masa yönetimi", "Masalar ayrı sayfaya bölünmeden salon bağlamında yönetilecek."],
    stations: ["İstasyon yönetimi", "Mutfak, kahve ve benzeri hazırlık istasyonları burada yönetilecek."],
    menu: ["Menü yönetimi", "Ürün, varyant, fiyat, uygunluk ve istasyon yönlendirmesi burada yönetilecek."],
    staff: ["Personel yönetimi", "Roller, istasyon yetkileri ve salon yetkileri burada yönetilecek."],
    settings: ["Tenant ayarları", "Profil, operasyonel ayarlar ve audit görünümü burada toplanacak."]
  };
  const [title, body] = copy[workspace];
  return (
    <section className="border border-zinc-200 bg-white px-5 py-5">
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-zinc-600">{body}</p>
      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <StateBlock title="API bağlantısı sıradaki implementasyon adımı" />
        <StateBlock title="Detaylar panel/drawer içinde açılacak" />
      </div>
    </section>
  );
}

function StaffManagementWorkspace() {
  const [staff, setStaff] = useState<StaffProfile[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [halls, setHalls] = useState<HallWithTables[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [actionState, setActionState] = useState<"idle" | "submitting" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    displayName: "",
    hallIds: [] as string[],
    roles: ["cashier"] as string[],
    stationIds: [] as string[],
    username: ""
  });

  useEffect(() => {
    void loadStaffWorkspace();
  }, []);

  async function loadStaffWorkspace() {
    setState("loading");
    setError(null);
    try {
      const [staffPayload, stationPayload, boardPayload] = await Promise.all([
        apiRequest<StaffList>("/api/tenant-setup/staff"),
        apiRequest<StationList>("/api/tenant-setup/stations"),
        apiRequest<HallTableBoard>("/api/tenant-setup/venue/board")
      ]);
      setStaff(staffPayload.items);
      setStations(stationPayload.items.filter((station) => station.enabled));
      setHalls(boardPayload.halls.filter((hall) => hall.enabled));
      setState("ready");
    } catch (loadError) {
      setError(errorMessageFrom(loadError));
      setState("error");
    }
  }

  function toggleRole(role: string) {
    setForm((current) => {
      const roles = current.roles.includes(role)
        ? current.roles.filter((value) => value !== role)
        : [...current.roles, role];
      return {
        ...current,
        hallIds: roles.includes("service_staff") ? current.hallIds : [],
        roles,
        stationIds: roles.includes("station_staff") ? current.stationIds : []
      };
    });
  }

  function toggleScope(scope: "hallIds" | "stationIds", id: string) {
    setForm((current) => ({
      ...current,
      [scope]: current[scope].includes(id)
        ? current[scope].filter((value) => value !== id)
        : [...current[scope], id]
    }));
  }

  async function createStaff(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      actionState === "submitting" ||
      !form.username.trim() ||
      !form.displayName.trim() ||
      form.roles.length === 0
    ) {
      return;
    }
    setActionState("submitting");
    setError(null);
    try {
      const created = await apiRequest<StaffProfile>("/api/tenant-setup/staff", {
        body: JSON.stringify({
          username: form.username.trim(),
          displayName: form.displayName.trim(),
          roles: form.roles,
          stationIds: form.roles.includes("station_staff") ? form.stationIds : [],
          hallIds: form.roles.includes("service_staff") ? form.hallIds : []
        }),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "POST"
      });
      setStaff((current) => [...current, created].sort((a, b) => a.displayName.localeCompare(b.displayName)));
      setForm({
        displayName: "",
        hallIds: [],
        roles: ["cashier"],
        stationIds: [],
        username: ""
      });
      setActionState("idle");
    } catch (createError) {
      setError(errorMessageFrom(createError));
      setActionState("error");
    }
  }

  const canCreate = Boolean(
    form.username.trim() &&
      form.displayName.trim() &&
      form.roles.length > 0 &&
      actionState !== "submitting"
  );
  const roleOptions = [
    ["tenant_admin", "Tenant admin"],
    ["cashier", "Kasiyer"],
    ["station_staff", "İstasyon personeli"],
    ["service_staff", "Servis personeli"]
  ];

  return (
    <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
      <div className="border border-zinc-200 bg-white">
        <div className="flex items-center justify-between border-b border-zinc-200 px-5 py-4">
          <div>
            <h3 className="text-lg font-semibold">Personel</h3>
            <p className="mt-1 text-sm text-zinc-600">
              Kullanıcı adı burada belirlenir. İlk şifre varsayılan olarak 12345678 olur.
            </p>
          </div>
          <button
            className="h-9 border border-zinc-300 px-3 text-sm font-medium hover:bg-zinc-50"
            onClick={() => void loadStaffWorkspace()}
            type="button"
          >
            Yenile
          </button>
        </div>
        {state === "loading" ? (
          <StateBlock title="Personel listesi yükleniyor" />
        ) : state === "error" ? (
          <StateBlock title={error ?? "Personel listesi alınamadı"} tone="error" />
        ) : staff.length === 0 ? (
          <StateBlock title="Henüz personel yok." />
        ) : (
          <div className="divide-y divide-zinc-200">
            {staff.map((item) => (
              <button
                className="block w-full px-5 py-4 text-left hover:bg-zinc-50"
                key={item.userId}
                type="button"
              >
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="font-semibold">{item.displayName}</p>
                    <p className="mt-1 text-sm text-zinc-500">{item.username}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <StatusBadge value={item.status} />
                    {item.firstPasswordRequired ? <StatusBadge value="first_password_required" /> : null}
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {item.roles.map((role) => (
                    <span
                      className="border border-zinc-200 bg-zinc-50 px-2 py-1 text-xs font-medium"
                      key={role}
                    >
                      {staffRoleLabel(role)}
                    </span>
                  ))}
                </div>
                <DetailRows
                  rows={[
                    ["İstasyon scope", item.stationIds.length.toString()],
                    ["Salon scope", item.hallIds.length.toString()],
                    ["Oluşturma", formatDate(item.createdAt)]
                  ]}
                />
              </button>
            ))}
          </div>
        )}
      </div>

      <aside className="border border-zinc-200 bg-white px-5 py-5">
        <h3 className="text-sm font-semibold">Personel ekle</h3>
        <form className="mt-4 space-y-4" onSubmit={(event) => void createStaff(event)}>
          <FieldText
            label="Kullanıcı adı"
            onChange={(value) => setForm((current) => ({...current, username: value}))}
            required
            value={form.username}
          />
          <FieldText
            label="Görünen ad"
            onChange={(value) => setForm((current) => ({...current, displayName: value}))}
            required
            value={form.displayName}
          />
          <div>
            <p className="text-sm font-medium">Roller *</p>
            <div className="mt-2 grid gap-2">
              {roleOptions.map(([role, label]) => (
                <label
                  className="flex min-h-10 items-center gap-2 border border-zinc-200 px-3 text-sm"
                  key={role}
                >
                  <input
                    checked={form.roles.includes(role)}
                    onChange={() => toggleRole(role)}
                    type="checkbox"
                  />
                  <span>{label}</span>
                </label>
              ))}
            </div>
          </div>
          {form.roles.includes("station_staff") ? (
            <div>
              <p className="text-sm font-medium">İstasyon yetkileri</p>
              <div className="mt-2 grid gap-2">
                {stations.length === 0 ? (
                  <p className="text-sm text-zinc-500">Aktif istasyon yok.</p>
                ) : (
                  stations.map((station) => (
                    <label
                      className="flex min-h-10 items-center gap-2 border border-zinc-200 px-3 text-sm"
                      key={station.stationId}
                    >
                      <input
                        checked={form.stationIds.includes(station.stationId)}
                        onChange={() => toggleScope("stationIds", station.stationId)}
                        type="checkbox"
                      />
                      <span>{station.name}</span>
                    </label>
                  ))
                )}
              </div>
            </div>
          ) : null}
          {form.roles.includes("service_staff") ? (
            <div>
              <p className="text-sm font-medium">Salon yetkileri</p>
              <div className="mt-2 grid gap-2">
                {halls.length === 0 ? (
                  <p className="text-sm text-zinc-500">Aktif salon yok.</p>
                ) : (
                  halls.map((hall) => (
                    <label
                      className="flex min-h-10 items-center gap-2 border border-zinc-200 px-3 text-sm"
                      key={hall.hallId}
                    >
                      <input
                        checked={form.hallIds.includes(hall.hallId)}
                        onChange={() => toggleScope("hallIds", hall.hallId)}
                        type="checkbox"
                      />
                      <span>{hall.name}</span>
                    </label>
                  ))
                )}
              </div>
            </div>
          ) : null}
          <div className="border border-emerald-200 bg-emerald-50 px-3 py-3 text-sm text-emerald-950">
            <p className="font-semibold">İlk giriş</p>
            <p className="mt-1">
              Varsayılan şifre 12345678. İlk girişte şifre değişimi zorunlu ve OTP tenant GSM
              numarasına gönderilir.
            </p>
          </div>
          {actionState === "error" && error ? <StateBlock title={error} tone="error" /> : null}
          <button
            className="h-10 w-full bg-zinc-950 px-4 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-300"
            disabled={!canCreate}
            type="submit"
          >
            {actionState === "submitting" ? "Ekleniyor" : "Personel ekle"}
          </button>
        </form>
      </aside>
    </section>
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
        `/api/platform/tenants/${tenantId}/lifecycle-events?limit=5`
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
        `/api/platform/audit-events?${params.toString()}`
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
        apiRequest<ProvisioningState>(`/api/platform/tenants/${tenantId}/provisioning`),
        apiRequest<ProvisioningRecoverySummary>(
          `/api/platform/tenants/${tenantId}/provisioning/recovery-summary`
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
        `/api/platform/tenants/${tenant.tenantId}/provisioning/retry`,
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
        `/api/platform/tenants/${tenant.tenantId}`
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
        `/api/platform/tenants/${tenant.tenantId}/profile`,
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
        `/api/platform/tenants/${tenant.tenantId}/status`,
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
            <p className="mt-1 break-all text-sm text-zinc-500">{tenantHost(tenant.subdomain)}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusBadge value={tenant.status} />
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
            <div className="grid gap-2">
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

function HallManagementWorkspace() {
  const [board, setBoard] = useState<HallTableBoard | null>(null);
  const [selectedHallId, setSelectedHallId] = useState<string | null>(null);
  const [selectedTableId, setSelectedTableId] = useState<string | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [actionState, setActionState] = useState<"idle" | "submitting" | "error">("idle");
  const [actionError, setActionError] = useState<string | null>(null);
  const [newHallName, setNewHallName] = useState("");
  const [newHallOrder, setNewHallOrder] = useState("");
  const [hallEditName, setHallEditName] = useState("");
  const [hallEditOrder, setHallEditOrder] = useState("");
  const [hallDisableReason, setHallDisableReason] = useState("");
  const [disableReason, setDisableReason] = useState("");
  const [tablePickerOpen, setTablePickerOpen] = useState(false);
  const [displayWifiSsid, setDisplayWifiSsid] = useState("");
  const [displayWifiPassword, setDisplayWifiPassword] = useState("");
  const [displayFirmware, setDisplayFirmware] = useState<DisplayFirmwareCreated | null>(null);

  async function loadBoard() {
    setState("loading");
    try {
      const payload = await apiRequest<HallTableBoard>("/api/tenant-setup/venue/board");
      setBoard(payload);
      setSelectedHallId((current) =>
        payload.halls.some((hall) => hall.hallId === current)
          ? current
          : payload.halls[0]?.hallId ?? null
      );
      setSelectedTableId((current) =>
        payload.halls.some((hall) => hall.tables.some((table) => table.tableId === current))
          ? current
          : null
      );
      setState("ready");
    } catch {
      setBoard(null);
      setState("error");
    }
  }

  useEffect(() => {
    void loadBoard();
  }, []);

  const selectedHall = board?.halls.find((hall) => hall.hallId === selectedHallId) ?? null;
  const selectedTable =
    selectedHall?.tables.find((table) => table.tableId === selectedTableId) ?? null;
  const physicalTables =
    selectedHall?.tables.filter((table) => table.mode === "physical" && table.enabled) ?? [];
  const availableVirtualTables =
    selectedHall?.tables.filter(
      (table) =>
        table.mode === "virtual_test" &&
        table.enabled &&
        !table.systemBoundarySlot
    ) ?? [];

  useEffect(() => {
    setHallEditName(selectedHall?.name ?? "");
    setHallEditOrder(selectedHall?.displayOrder.toString() ?? "");
    setHallDisableReason("");
  }, [selectedHall?.hallId, selectedHall?.name, selectedHall?.displayOrder]);

  useEffect(() => {
    setDisplayWifiSsid("");
    setDisplayWifiPassword("");
    setDisplayFirmware(null);
  }, [selectedTable?.tableId]);

  if (state === "loading") {
    return <StateBlock title="Salon ve masa düzeni yükleniyor" />;
  }
  if (state === "error" || board === null) {
    return <StateBlock title="Salon ve masa düzeni alınamadı" tone="error" />;
  }

  async function createHall(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newHallName.trim() || !newHallOrder || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      const created = await apiRequest<HallWithTables>("/api/tenant-setup/halls", {
        body: JSON.stringify({
          name: newHallName.trim(),
          displayOrder: Number(newHallOrder)
        }),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "POST"
      });
      setNewHallName("");
      setNewHallOrder("");
      await loadBoard();
      setSelectedHallId(created.hallId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function promoteTable(table: VenueTable) {
    if (table.systemBoundarySlot || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<VenueTable>(`/api/tenant-setup/tables/${table.tableId}`, {
        body: JSON.stringify({
          name: table.name,
          displayOrder: table.displayOrder,
          mode: "physical"
        }),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "PATCH"
      });
      await loadBoard();
      setSelectedTableId(table.tableId);
      setTablePickerOpen(false);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function updateSelectedHall(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedHall || !hallEditName.trim() || !hallEditOrder || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<HallWithTables>(`/api/tenant-setup/halls/${selectedHall.hallId}`, {
        body: JSON.stringify({
          name: hallEditName.trim(),
          displayOrder: Number(hallEditOrder)
        }),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "PATCH"
      });
      await loadBoard();
      setSelectedHallId(selectedHall.hallId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function disableSelectedHall() {
    if (!selectedHall || !hallDisableReason.trim() || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<HallWithTables>(`/api/tenant-setup/halls/${selectedHall.hallId}/disable`, {
        body: JSON.stringify({reason: hallDisableReason.trim()}),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "POST"
      });
      await loadBoard();
      setSelectedHallId(selectedHall.hallId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function disableSelectedTable() {
    if (!selectedTable || !disableReason.trim() || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<VenueTable>(`/api/tenant-setup/tables/${selectedTable.tableId}/disable`, {
        body: JSON.stringify({reason: disableReason.trim()}),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "POST"
      });
      setDisableReason("");
      await loadBoard();
      setSelectedTableId(selectedTable.tableId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function generateDisplayFirmware(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !selectedTable ||
      selectedTable.mode !== "physical" ||
      !displayWifiSsid.trim() ||
      !displayWifiPassword ||
      actionState === "submitting"
    ) {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      const created = await apiRequest<DisplayFirmwareCreated>(
        `/api/tenant-setup/tables/${selectedTable.tableId}/display-firmware`,
        {
          body: JSON.stringify({
            wifiSsid: displayWifiSsid.trim(),
            wifiPassword: displayWifiPassword
          }),
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": crypto.randomUUID()
          },
          method: "POST"
        }
      );
      setDisplayFirmware(created);
      downloadTextFile(created.fileName, created.firmwareContent, "text/x-arduino");
      setDisplayWifiPassword("");
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }


  return (
    <section className="grid gap-5 xl:grid-cols-[260px_minmax(0,1fr)_340px]">
      <aside className="border border-zinc-200 bg-white">
        <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
          <h3 className="text-sm font-semibold">Salonlar</h3>
          <button
            className="text-sm font-medium text-emerald-700 hover:text-emerald-900"
            onClick={() => void loadBoard()}
            type="button"
          >
            Yenile
          </button>
        </div>
        {board.halls.length === 0 ? (
          <StateBlock title="Henüz salon yok" />
        ) : (
          <div className="divide-y divide-zinc-200">
            {board.halls.map((hall) => (
              <button
                className={`w-full px-4 py-3 text-left text-sm hover:bg-zinc-50 ${
                  selectedHallId === hall.hallId ? "bg-emerald-50" : "bg-white"
                }`}
                key={hall.hallId}
                onClick={() => {
                  setSelectedHallId(hall.hallId);
                  setSelectedTableId(null);
                }}
                type="button"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium">{hall.name}</span>
                  <StatusBadge value={hall.enabled ? "enabled" : "disabled"} />
                </div>
                <p className="mt-1 text-xs text-zinc-500">
                  {hall.tableNumberBase}-{hall.tableNumberBase + 99} / {hall.tables.length} slot
                </p>
              </button>
            ))}
          </div>
        )}
        <form className="space-y-2 border-t border-zinc-200 px-4 py-4" onSubmit={createHall}>
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Salon ekle</p>
          <input
            className="h-10 w-full border border-zinc-300 px-3 text-sm"
            onChange={(event) => setNewHallName(event.target.value)}
            placeholder="Salon adı"
            value={newHallName}
          />
          <input
            className="h-10 w-full border border-zinc-300 px-3 text-sm"
            onChange={(event) => setNewHallOrder(event.target.value)}
            placeholder="Sıra"
            type="number"
            value={newHallOrder}
          />
          <button
            className="h-10 w-full border border-zinc-950 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
            disabled={!newHallName.trim() || !newHallOrder || actionState === "submitting"}
            type="submit"
          >
            Salon ekle
          </button>
        </form>
      </aside>

      <section className="border border-zinc-200 bg-white">
        <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
          <div>
            <h3 className="text-sm font-semibold">{selectedHall?.name ?? "Salon seçilmedi"}</h3>
            <p className="mt-1 text-xs text-zinc-500">
              {selectedHall
                ? `${selectedHall.tableNumberBase}-${selectedHall.tableNumberBase + 99} slot aralığı`
                : "Sıralı slot düzeni"}
            </p>
          </div>
          <span className="text-xs text-zinc-500">
              {board.derivedAt ? formatDate(board.derivedAt) : ""}
          </span>
        </div>
        {selectedHall === null ? (
          <StateBlock title="Salon seçin" />
        ) : (
          <>
            <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-3">
              <span className="text-sm text-zinc-500">
                {physicalTables.length} fiziksel masa
              </span>
              <button
                className="h-9 border border-zinc-950 px-3 text-xs font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                disabled={!selectedHall.enabled}
                onClick={() => setTablePickerOpen(true)}
                type="button"
              >
                Masa ekle
              </button>
            </div>
            {physicalTables.length === 0 ? (
              <StateBlock title="Bu salonda fiziksel masa yok" />
            ) : (
              <div className="grid grid-cols-2 gap-3 p-4 sm:grid-cols-3 lg:grid-cols-4">
                {physicalTables.map((table) => (
                  <button
                    className={`aspect-[4/3] border px-3 py-3 text-left hover:bg-zinc-50 ${
                      selectedTableId === table.tableId
                        ? "border-emerald-600 bg-emerald-50"
                        : "border-zinc-200 bg-white"
                    }`}
                    key={table.tableId}
                    onClick={() => setSelectedTableId(table.tableId)}
                    type="button"
                  >
                    <p className="truncate text-sm font-semibold">{table.name}</p>
                    <p className="mt-1 text-xs text-zinc-500">No {table.tableNumber}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <StatusBadge value={table.enabled ? "enabled" : "disabled"} />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </>
        )}
      </section>

      <aside className="border border-zinc-200 bg-white px-4 py-4">
        <h3 className="text-sm font-semibold">Salon ve masa detayı</h3>
        {selectedHall ? (
          <div className="mt-4 space-y-3 border-b border-zinc-200 pb-4">
            <form className="grid gap-2" onSubmit={updateSelectedHall}>
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                Salon düzenle
              </p>
              <input
                className="h-10 border border-zinc-300 px-3 text-sm"
                onChange={(event) => setHallEditName(event.target.value)}
                placeholder="Salon adı"
                value={hallEditName}
              />
              <input
                className="h-10 border border-zinc-300 px-3 text-sm"
                onChange={(event) => setHallEditOrder(event.target.value)}
                placeholder="Liste sırası"
                type="number"
                value={hallEditOrder}
              />
              <button
                className="h-10 border border-zinc-950 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                disabled={!hallEditName.trim() || !hallEditOrder || actionState === "submitting"}
                type="submit"
              >
                Salonu kaydet
              </button>
            </form>
            <div className="grid gap-2">
              <input
                className="h-10 border border-zinc-300 px-3 text-sm"
                onChange={(event) => setHallDisableReason(event.target.value)}
                placeholder="Salon pasifleştirme nedeni"
                value={hallDisableReason}
              />
              <button
                className="h-10 border border-zinc-300 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                disabled={
                  !selectedHall.enabled ||
                  !hallDisableReason.trim() ||
                  actionState === "submitting"
                }
                onClick={() => void disableSelectedHall()}
                type="button"
              >
                Salonu pasifleştir
              </button>
            </div>
          </div>
        ) : null}
        {selectedTable === null ? (
          <StateBlock title="Bir masa seçin" />
        ) : (
          <div className="mt-4 space-y-4">
            <DetailRows
              rows={[
                ["Masa", selectedTable.name],
                ["Numara", selectedTable.tableNumber.toString()],
                ["Salon", selectedHall?.name ?? "-"],
                ["Sıra", selectedTable.displayOrder.toString()],
                ["Mod", selectedTable.mode],
                ["Sistem slotu", selectedTable.systemBoundarySlot ? "evet" : "hayır"],
                ["Durum", selectedTable.enabled ? "enabled" : "disabled"]
              ]}
            />
            <div className="border-t border-zinc-200 pt-4">
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                Display provisioning
              </p>
              <p className="mt-2 text-sm text-zinc-600">
                ESP32 firmware üretimi yalnızca fiziksel masalarda açılır. Sanal ve sınır
                slotlarında fiziksel ekran kurulumu yapılamaz.
              </p>
            </div>
            {selectedTable.mode === "virtual_test" ? (
              <div className="space-y-2 border-t border-zinc-200 pt-4">
                <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                  Fiziksel masa
                </p>
                <button
                  className="h-10 w-full border border-zinc-950 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                  disabled={selectedTable.systemBoundarySlot || actionState === "submitting"}
                  onClick={() => void promoteTable(selectedTable)}
                  type="button"
                >
                  Fiziksel masaya çevir
                </button>
              </div>
            ) : (
              <form className="space-y-2 border-t border-zinc-200 pt-4" onSubmit={generateDisplayFirmware}>
                <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                  ESP32 ekran
                </p>
                <p className="text-sm text-zinc-600">
                  WiFi bilgileri ve ekran credential yalnızca oluşturulan .ino dosyasında yer alır.
                </p>
                <input
                  className="h-10 w-full border border-zinc-300 px-3 text-sm"
                  onChange={(event) => setDisplayWifiSsid(event.target.value)}
                  placeholder="WiFi SSID"
                  value={displayWifiSsid}
                />
                <input
                  className="h-10 w-full border border-zinc-300 px-3 text-sm"
                  onChange={(event) => setDisplayWifiPassword(event.target.value)}
                  placeholder="WiFi şifresi"
                  type="password"
                  value={displayWifiPassword}
                />
                <button
                  className="h-10 w-full border border-zinc-950 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                  disabled={
                    !displayWifiSsid.trim() ||
                    !displayWifiPassword ||
                    actionState === "submitting"
                  }
                  type="submit"
                >
                  Ekran yazılımını oluştur
                </button>
                {displayFirmware?.tableId === selectedTable.tableId ? (
                  <p className="text-xs text-zinc-500">
                    {displayFirmware.fileName} oluşturuldu. Credential rotate edildi.
                  </p>
                ) : null}
              </form>
            )}
            <div className="space-y-2 border-t border-zinc-200 pt-4">
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                Operasyonlar
              </p>
              <input
                className="h-10 w-full border border-zinc-300 px-3 text-sm"
                onChange={(event) => setDisableReason(event.target.value)}
                placeholder="Pasifleştirme nedeni"
                value={disableReason}
              />
              <button
                className="h-10 w-full border border-zinc-300 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                disabled={
                  !selectedTable.enabled || !disableReason.trim() || actionState === "submitting"
                }
                onClick={() => void disableSelectedTable()}
                type="button"
              >
                Masayı pasifleştir
              </button>
            </div>
          </div>
        )}
        {actionError ? <StateBlock title={actionError} tone="error" /> : null}
      </aside>
      {tablePickerOpen && selectedHall ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/40 px-4">
          <div className="max-h-[85vh] w-full max-w-3xl overflow-hidden border border-zinc-200 bg-white">
            <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
              <div>
                <h3 className="text-sm font-semibold">Masa ekle</h3>
                <p className="mt-1 text-xs text-zinc-500">
                  {selectedHall.name} içindeki uygun sanal slotlardan birini fiziksel masaya çevir.
                </p>
              </div>
              <button
                className="h-9 border border-zinc-300 px-3 text-xs font-medium hover:bg-zinc-50"
                onClick={() => setTablePickerOpen(false)}
                type="button"
              >
                Kapat
              </button>
            </div>
            {availableVirtualTables.length === 0 ? (
              <StateBlock title="Uygun sanal slot yok" />
            ) : (
              <div className="grid max-h-[65vh] gap-3 overflow-auto p-4 sm:grid-cols-3 md:grid-cols-4">
                {availableVirtualTables.map((table) => (
                  <button
                    className="border border-zinc-200 px-3 py-3 text-left hover:border-emerald-600 hover:bg-emerald-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                    disabled={actionState === "submitting"}
                    key={table.tableId}
                    onClick={() => void promoteTable(table)}
                    type="button"
                  >
                    <p className="text-sm font-semibold">{table.name}</p>
                    <p className="mt-1 text-xs text-zinc-500">No {table.tableNumber}</p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function StationManagementWorkspace() {
  const [stations, setStations] = useState<Station[]>([]);
  const [catalog, setCatalog] = useState<MenuSetupCatalog | null>(null);
  const [selectedStationId, setSelectedStationId] = useState<string | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [actionState, setActionState] = useState<"idle" | "submitting" | "error">("idle");
  const [actionError, setActionError] = useState<string | null>(null);
  const [newStationName, setNewStationName] = useState("");
  const [newStationOrder, setNewStationOrder] = useState("");
  const [stationEditName, setStationEditName] = useState("");
  const [stationEditOrder, setStationEditOrder] = useState("");
  const [disableReason, setDisableReason] = useState("");
  const [stationProductName, setStationProductName] = useState("");
  const [stationProductCategoryId, setStationProductCategoryId] = useState("");
  const [stationProductVariantName, setStationProductVariantName] = useState("Standart");
  const [stationProductPrice, setStationProductPrice] = useState("");

  async function loadStations(nextSelectedStationId?: string) {
    setState("loading");
    try {
      const [stationPayload, menuPayload] = await Promise.all([
        apiRequest<StationList>("/api/tenant-setup/stations?include_disabled=true"),
        apiRequest<MenuSetupCatalog>("/api/tenant-setup/menu?include_disabled=true")
      ]);
      setStations(stationPayload.items);
      setCatalog(menuPayload);
      const selectedCandidate =
        nextSelectedStationId ?? selectedStationId ?? stationPayload.items[0]?.stationId ?? null;
      setSelectedStationId(
        stationPayload.items.some((station) => station.stationId === selectedCandidate)
          ? selectedCandidate
          : stationPayload.items[0]?.stationId ?? null
      );
      setStationProductCategoryId((current) => current || menuPayload.categories[0]?.categoryId || "");
      setState("ready");
    } catch {
      setStations([]);
      setCatalog(null);
      setState("error");
    }
  }

  useEffect(() => {
    void loadStations();
  }, []);

  const selectedStation =
    stations.find((station) => station.stationId === selectedStationId) ?? null;
  const stationProducts =
    catalog?.categories.flatMap((category) =>
      category.products
        .filter((product) => product.stationId === selectedStationId)
        .map((product) => ({category, product}))
    ) ?? [];

  useEffect(() => {
    setStationEditName(selectedStation?.name ?? "");
    setStationEditOrder(selectedStation?.displayOrder.toString() ?? "");
    setDisableReason("");
  }, [selectedStation?.stationId, selectedStation?.name, selectedStation?.displayOrder]);

  async function createStation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newStationName.trim() || !newStationOrder || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      const created = await apiRequest<Station>("/api/tenant-setup/stations", {
        body: JSON.stringify({
          name: newStationName.trim(),
          displayOrder: Number(newStationOrder)
        }),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "POST"
      });
      setNewStationName("");
      setNewStationOrder("");
      await loadStations(created.stationId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function disableSelectedStation() {
    if (!selectedStation || !disableReason.trim() || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<Station>(`/api/tenant-setup/stations/${selectedStation.stationId}/disable`, {
        body: JSON.stringify({reason: disableReason.trim()}),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "POST"
      });
      setDisableReason("");
      await loadStations(selectedStation.stationId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function updateSelectedStation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !selectedStation ||
      !stationEditName.trim() ||
      !stationEditOrder ||
      actionState === "submitting"
    ) {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<Station>(`/api/tenant-setup/stations/${selectedStation.stationId}`, {
        body: JSON.stringify({
          name: stationEditName.trim(),
          displayOrder: Number(stationEditOrder)
        }),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "PATCH"
      });
      await loadStations(selectedStation.stationId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function createStationProduct(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !selectedStation ||
      !stationProductCategoryId ||
      !stationProductName.trim() ||
      !stationProductVariantName.trim() ||
      !stationProductPrice ||
      actionState === "submitting"
    ) {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<ProductService>("/api/tenant-setup/menu/products", {
        body: JSON.stringify({
          categoryId: stationProductCategoryId,
          stationId: selectedStation.stationId,
          name: stationProductName.trim(),
          variants: [
            {
              name: stationProductVariantName.trim(),
              priceMinor: Number(stationProductPrice)
            }
          ]
        }),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "POST"
      });
      setStationProductName("");
      setStationProductVariantName("Standart");
      setStationProductPrice("");
      await loadStations(selectedStation.stationId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  if (state === "loading") {
    return <StateBlock title="İstasyonlar yükleniyor" />;
  }
  if (state === "error") {
    return <StateBlock title="İstasyonlar alınamadı" tone="error" />;
  }

  return (
    <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="border border-zinc-200 bg-white">
        <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
          <div>
            <h3 className="text-sm font-semibold">İstasyonlar</h3>
            <p className="mt-1 text-xs text-zinc-500">
              İstasyon sırası listelerdeki görüntüleme sırasıdır
            </p>
          </div>
          <button
            className="text-sm font-medium text-emerald-700 hover:text-emerald-900"
            onClick={() => void loadStations()}
            type="button"
          >
            Yenile
          </button>
        </div>
        {stations.length === 0 ? (
          <StateBlock title="Henüz istasyon yok" />
        ) : (
          <div className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-3">
            {stations.map((station) => (
              <button
                className={`border px-4 py-4 text-left hover:bg-zinc-50 ${
                  selectedStationId === station.stationId
                    ? "border-emerald-600 bg-emerald-50"
                    : "border-zinc-200 bg-white"
                }`}
                key={station.stationId}
                onClick={() => setSelectedStationId(station.stationId)}
                type="button"
              >
                <p className="truncate text-sm font-semibold">{station.name}</p>
                <p className="mt-1 text-xs text-zinc-500">Liste sırası {station.displayOrder}</p>
                <div className="mt-3">
                  <StatusBadge value={station.enabled ? "enabled" : "disabled"} />
                </div>
              </button>
            ))}
          </div>
        )}
        <form
          className="grid gap-2 border-t border-zinc-200 p-4 md:grid-cols-[minmax(0,1fr)_110px_auto]"
          onSubmit={createStation}
        >
          <input
            className="h-10 border border-zinc-300 px-3 text-sm"
            onChange={(event) => setNewStationName(event.target.value)}
            placeholder="İstasyon adı"
            value={newStationName}
          />
          <input
            className="h-10 border border-zinc-300 px-3 text-sm"
            onChange={(event) => setNewStationOrder(event.target.value)}
            placeholder="Liste sırası"
            type="number"
            value={newStationOrder}
          />
          <button
            className="h-10 border border-zinc-950 px-4 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
            disabled={!newStationName.trim() || !newStationOrder || actionState === "submitting"}
            type="submit"
          >
            İstasyon ekle
          </button>
        </form>
      </section>

      <aside className="border border-zinc-200 bg-white px-4 py-4">
        <h3 className="text-sm font-semibold">İstasyon detayı</h3>
        {selectedStation === null ? (
          <StateBlock title="Bir istasyon seçin" />
        ) : (
          <div className="mt-4 space-y-4">
            <DetailRows
              rows={[
                ["İstasyon", selectedStation.name],
                ["Liste sırası", selectedStation.displayOrder.toString()],
                ["Durum", selectedStation.enabled ? "enabled" : "disabled"],
                ["Güncelleme", formatDate(selectedStation.updatedAt)]
              ]}
            />
            <form className="grid gap-2 border-t border-zinc-200 pt-4" onSubmit={updateSelectedStation}>
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                İstasyon düzenle
              </p>
              <input
                className="h-10 w-full border border-zinc-300 px-3 text-sm"
                onChange={(event) => setStationEditName(event.target.value)}
                placeholder="İstasyon adı"
                value={stationEditName}
              />
              <input
                className="h-10 w-full border border-zinc-300 px-3 text-sm"
                onChange={(event) => setStationEditOrder(event.target.value)}
                placeholder="Liste sırası"
                type="number"
                value={stationEditOrder}
              />
              <button
                className="h-10 w-full border border-zinc-950 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                disabled={
                  !stationEditName.trim() ||
                  !stationEditOrder ||
                  actionState === "submitting"
                }
                type="submit"
              >
                İstasyonu kaydet
              </button>
            </form>
            <div className="space-y-2 border-t border-zinc-200 pt-4">
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                Bu istasyondaki ürünler
              </p>
              {stationProducts.length === 0 ? (
                <p className="text-sm text-zinc-500">Ürün yok</p>
              ) : (
                <div className="space-y-2">
                  {stationProducts.map(({category, product}) => (
                    <div className="border border-zinc-200 px-3 py-2" key={product.productId}>
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate text-sm font-medium">{product.name}</span>
                        <StatusBadge value={product.enabled ? "enabled" : "disabled"} />
                      </div>
                      <p className="mt-1 text-xs text-zinc-500">
                        {category.name} / {product.variants[0]?.priceMinor ?? 0} minor
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <form className="grid gap-2 border-t border-zinc-200 pt-4" onSubmit={createStationProduct}>
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                Bu istasyona ürün ekle
              </p>
              <select
                className="h-10 border border-zinc-300 bg-white px-3 text-sm"
                onChange={(event) => setStationProductCategoryId(event.target.value)}
                value={stationProductCategoryId}
              >
                <option value="">Kategori seç</option>
                {catalog?.categories
                  .filter((category) => category.enabled)
                  .map((category) => (
                    <option key={category.categoryId} value={category.categoryId}>
                      {category.name}
                    </option>
                  ))}
              </select>
              <input
                className="h-10 border border-zinc-300 px-3 text-sm"
                onChange={(event) => setStationProductName(event.target.value)}
                placeholder="Ürün adı"
                value={stationProductName}
              />
              <input
                className="h-10 border border-zinc-300 px-3 text-sm"
                onChange={(event) => setStationProductVariantName(event.target.value)}
                placeholder="Varyant"
                value={stationProductVariantName}
              />
              <input
                className="h-10 border border-zinc-300 px-3 text-sm"
                onChange={(event) => setStationProductPrice(event.target.value)}
                placeholder="Fiyat minor"
                type="number"
                value={stationProductPrice}
              />
              <button
                className="h-10 w-full border border-zinc-950 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                disabled={
                  !stationProductCategoryId ||
                  !stationProductName.trim() ||
                  !stationProductVariantName.trim() ||
                  !stationProductPrice ||
                  actionState === "submitting"
                }
                type="submit"
              >
                Ürün ekle
              </button>
            </form>
            <div className="space-y-2 border-t border-zinc-200 pt-4">
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                Operasyonlar
              </p>
              <input
                className="h-10 w-full border border-zinc-300 px-3 text-sm"
                onChange={(event) => setDisableReason(event.target.value)}
                placeholder="Pasifleştirme nedeni"
                value={disableReason}
              />
              <button
                className="h-10 w-full border border-zinc-300 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                disabled={
                  !selectedStation.enabled ||
                  !disableReason.trim() ||
                  actionState === "submitting"
                }
                onClick={() => void disableSelectedStation()}
                type="button"
              >
                İstasyonu pasifleştir
              </button>
            </div>
          </div>
        )}
        {actionError ? <StateBlock title={actionError} tone="error" /> : null}
      </aside>
    </section>
  );
}

function MenuManagementWorkspace() {
  const [catalog, setCatalog] = useState<MenuSetupCatalog | null>(null);
  const [stations, setStations] = useState<Station[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [actionState, setActionState] = useState<"idle" | "submitting" | "error">("idle");
  const [actionError, setActionError] = useState<string | null>(null);
  const [newCategoryName, setNewCategoryName] = useState("");
  const [newCategoryOrder, setNewCategoryOrder] = useState("");
  const [productName, setProductName] = useState("");
  const [productStationId, setProductStationId] = useState("");
  const [variantName, setVariantName] = useState("Standart");
  const [variantPrice, setVariantPrice] = useState("");
  const [detailVariantName, setDetailVariantName] = useState("");
  const [detailVariantPrice, setDetailVariantPrice] = useState("");
  const [modifierGroupName, setModifierGroupName] = useState("");
  const [modifierOptionName, setModifierOptionName] = useState("");
  const [modifierOptionPrice, setModifierOptionPrice] = useState("0");
  const [availabilityReason, setAvailabilityReason] = useState("");

  async function loadMenu(nextCategoryId?: string, nextProductId?: string) {
    setState("loading");
    try {
      const [menuPayload, stationPayload] = await Promise.all([
        apiRequest<MenuSetupCatalog>("/api/tenant-setup/menu?include_disabled=true"),
        apiRequest<StationList>("/api/tenant-setup/stations?include_disabled=true")
      ]);
      setCatalog(menuPayload);
      setStations(stationPayload.items);
      const categoryCandidate =
        nextCategoryId ?? selectedCategoryId ?? menuPayload.categories[0]?.categoryId ?? null;
      const selectedCategory = menuPayload.categories.find(
        (category) => category.categoryId === categoryCandidate
      );
      setSelectedCategoryId(
        selectedCategory?.categoryId ?? menuPayload.categories[0]?.categoryId ?? null
      );
      setSelectedProductId(
        nextProductId ??
          (selectedCategory?.products.some((product) => product.productId === selectedProductId)
            ? selectedProductId
            : null)
      );
      setProductStationId((current) => current || stationPayload.items[0]?.stationId || "");
      setState("ready");
    } catch {
      setCatalog(null);
      setStations([]);
      setState("error");
    }
  }

  useEffect(() => {
    void loadMenu();
  }, []);

  const selectedCategory =
    catalog?.categories.find((category) => category.categoryId === selectedCategoryId) ?? null;
  const selectedProduct =
    selectedCategory?.products.find((product) => product.productId === selectedProductId) ?? null;

  async function createCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newCategoryName.trim() || !newCategoryOrder || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      const created = await apiRequest<MenuCategory>("/api/tenant-setup/menu/categories", {
        body: JSON.stringify({
          name: newCategoryName.trim(),
          displayOrder: Number(newCategoryOrder)
        }),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "POST"
      });
      setNewCategoryName("");
      setNewCategoryOrder("");
      await loadMenu(created.categoryId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function createProduct(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !selectedCategory ||
      !productName.trim() ||
      !productStationId ||
      !variantName.trim() ||
      !variantPrice ||
      actionState === "submitting"
    ) {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      const created = await apiRequest<ProductService>("/api/tenant-setup/menu/products", {
        body: JSON.stringify({
          categoryId: selectedCategory.categoryId,
          stationId: productStationId,
          name: productName.trim(),
          variants: [
            {
              name: variantName.trim(),
              priceMinor: Number(variantPrice)
            }
          ]
        }),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID()
        },
        method: "POST"
      });
      setProductName("");
      setVariantName("Standart");
      setVariantPrice("");
      await loadMenu(created.categoryId, created.productId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function disableSelectedCategory() {
    if (!selectedCategory || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<MenuCategory>(
        `/api/tenant-setup/menu/categories/${selectedCategory.categoryId}/disable`,
        {
          body: JSON.stringify({reason: "tenant_admin_action"}),
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": crypto.randomUUID()
          },
          method: "POST"
        }
      );
      await loadMenu(selectedCategory.categoryId, selectedProductId ?? undefined);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function disableSelectedProduct() {
    if (!selectedProduct || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<ProductService>(
        `/api/tenant-setup/menu/products/${selectedProduct.productId}/disable`,
        {
          body: JSON.stringify({reason: "tenant_admin_action"}),
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": crypto.randomUUID()
          },
          method: "POST"
        }
      );
      await loadMenu(selectedProduct.categoryId, selectedProduct.productId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function addVariant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !selectedProduct ||
      !detailVariantName.trim() ||
      !detailVariantPrice ||
      actionState === "submitting"
    ) {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<ProductVariant>(
        `/api/tenant-setup/menu/products/${selectedProduct.productId}/variants`,
        {
          body: JSON.stringify({
            name: detailVariantName.trim(),
            priceMinor: Number(detailVariantPrice),
            displayOrder: selectedProduct.variants.length + 1,
            isDefault: selectedProduct.variants.length === 0
          }),
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": crypto.randomUUID()
          },
          method: "POST"
        }
      );
      setDetailVariantName("");
      setDetailVariantPrice("");
      await loadMenu(selectedProduct.categoryId, selectedProduct.productId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function saveSimpleModifierConfig(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !selectedProduct ||
      !modifierGroupName.trim() ||
      !modifierOptionName.trim() ||
      actionState === "submitting"
    ) {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<ModifierGroup[]>(
        `/api/tenant-setup/menu/products/${selectedProduct.productId}/modifiers`,
        {
          body: JSON.stringify({
            groups: [
              {
                name: modifierGroupName.trim(),
                required: false,
                minSelections: 0,
                maxSelections: 1,
                displayOrder: 1,
                options: [
                  {
                    name: modifierOptionName.trim(),
                    priceDeltaMinor: Number(modifierOptionPrice || "0")
                  }
                ]
              }
            ]
          }),
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": crypto.randomUUID()
          },
          method: "POST"
        }
      );
      setModifierGroupName("");
      setModifierOptionName("");
      setModifierOptionPrice("0");
      await loadMenu(selectedProduct.categoryId, selectedProduct.productId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  async function markUnavailable() {
    if (!selectedProduct || !availabilityReason.trim() || actionState === "submitting") {
      return;
    }
    setActionState("submitting");
    setActionError(null);
    try {
      await apiRequest<AvailabilityOverride>(
        `/api/tenant-setup/menu/products/${selectedProduct.productId}/availability`,
        {
          body: JSON.stringify({
            state: "unavailable",
            reason: availabilityReason.trim()
          }),
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": crypto.randomUUID()
          },
          method: "POST"
        }
      );
      setAvailabilityReason("");
      await loadMenu(selectedProduct.categoryId, selectedProduct.productId);
      setActionState("idle");
    } catch (error) {
      setActionError(errorMessageFrom(error));
      setActionState("error");
    }
  }

  if (state === "loading") {
    return <StateBlock title="Menü yükleniyor" />;
  }
  if (state === "error" || catalog === null) {
    return <StateBlock title="Menü alınamadı" tone="error" />;
  }

  return (
    <section className="grid gap-5 xl:grid-cols-[260px_minmax(0,1fr)_360px]">
      <aside className="border border-zinc-200 bg-white">
        <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3">
          <h3 className="text-sm font-semibold">Kategoriler</h3>
          <button
            className="text-sm font-medium text-emerald-700 hover:text-emerald-900"
            onClick={() => void loadMenu()}
            type="button"
          >
            Yenile
          </button>
        </div>
        {catalog.categories.length === 0 ? (
          <StateBlock title="Henüz kategori yok" />
        ) : (
          <div className="divide-y divide-zinc-200">
            {catalog.categories.map((category) => (
              <button
                className={`w-full px-4 py-3 text-left text-sm hover:bg-zinc-50 ${
                  selectedCategoryId === category.categoryId ? "bg-emerald-50" : "bg-white"
                }`}
                key={category.categoryId}
                onClick={() => {
                  setSelectedCategoryId(category.categoryId);
                  setSelectedProductId(null);
                }}
                type="button"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium">{category.name}</span>
                  <StatusBadge value={category.enabled ? "enabled" : "disabled"} />
                </div>
                <p className="mt-1 text-xs text-zinc-500">{category.products.length} ürün</p>
              </button>
            ))}
          </div>
        )}
        <form className="space-y-2 border-t border-zinc-200 px-4 py-4" onSubmit={createCategory}>
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Kategori ekle</p>
          <input
            className="h-10 w-full border border-zinc-300 px-3 text-sm"
            onChange={(event) => setNewCategoryName(event.target.value)}
            placeholder="Kategori adı"
            value={newCategoryName}
          />
          <input
            className="h-10 w-full border border-zinc-300 px-3 text-sm"
            onChange={(event) => setNewCategoryOrder(event.target.value)}
            placeholder="Sıra"
            type="number"
            value={newCategoryOrder}
          />
          <button
            className="h-10 w-full border border-zinc-950 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
            disabled={!newCategoryName.trim() || !newCategoryOrder || actionState === "submitting"}
            type="submit"
          >
            Kategori ekle
          </button>
        </form>
      </aside>

      <section className="border border-zinc-200 bg-white">
        <div className="border-b border-zinc-200 px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold">
                {selectedCategory?.name ?? "Kategori seçilmedi"}
              </h3>
              <p className="mt-1 text-xs text-zinc-500">Ürünler ve station routing</p>
            </div>
            {selectedCategory ? (
              <button
                className="h-9 border border-zinc-300 px-3 text-xs font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                disabled={!selectedCategory.enabled || actionState === "submitting"}
                onClick={() => void disableSelectedCategory()}
                type="button"
              >
                Pasifleştir
              </button>
            ) : null}
          </div>
        </div>
        {selectedCategory === null ? (
          <StateBlock title="Kategori seçin" />
        ) : selectedCategory.products.length === 0 ? (
          <StateBlock title="Bu kategoride ürün yok" />
        ) : (
          <div className="divide-y divide-zinc-200">
            {selectedCategory.products.map((product) => (
              <button
                className={`grid w-full gap-2 px-4 py-4 text-left hover:bg-zinc-50 md:grid-cols-[minmax(0,1fr)_160px] ${
                  selectedProductId === product.productId ? "bg-emerald-50" : "bg-white"
                }`}
                key={product.productId}
                onClick={() => setSelectedProductId(product.productId)}
                type="button"
              >
                <div>
                  <p className="truncate text-sm font-semibold">{product.name}</p>
                  <p className="mt-1 text-xs text-zinc-500">
                    {product.variants[0]?.priceMinor ?? 0} minor
                  </p>
                </div>
                <StatusBadge value={product.enabled ? "enabled" : "disabled"} />
              </button>
            ))}
          </div>
        )}
        <form
          className="grid gap-2 border-t border-zinc-200 p-4 md:grid-cols-2"
          onSubmit={createProduct}
        >
          <input
            className="h-10 border border-zinc-300 px-3 text-sm"
            onChange={(event) => setProductName(event.target.value)}
            placeholder="Ürün adı"
            value={productName}
          />
          <select
            className="h-10 border border-zinc-300 bg-white px-3 text-sm"
            onChange={(event) => setProductStationId(event.target.value)}
            value={productStationId}
          >
            <option value="">İstasyon seç</option>
            {stations
              .filter((station) => station.enabled)
              .map((station) => (
                <option key={station.stationId} value={station.stationId}>
                  {station.name}
                </option>
              ))}
          </select>
          <input
            className="h-10 border border-zinc-300 px-3 text-sm"
            onChange={(event) => setVariantName(event.target.value)}
            placeholder="Varyant"
            value={variantName}
          />
          <input
            className="h-10 border border-zinc-300 px-3 text-sm"
            onChange={(event) => setVariantPrice(event.target.value)}
            placeholder="Fiyat minor"
            type="number"
            value={variantPrice}
          />
          <button
            className="h-10 border border-zinc-950 px-4 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100 md:col-span-2"
            disabled={
              !selectedCategory ||
              !productName.trim() ||
              !productStationId ||
              !variantName.trim() ||
              !variantPrice ||
              actionState === "submitting"
            }
            type="submit"
          >
            Ürün ekle
          </button>
        </form>
      </section>

      <aside className="border border-zinc-200 bg-white px-4 py-4">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold">Ürün detayı</h3>
          {selectedProduct ? (
            <button
              className="h-9 border border-zinc-300 px-3 text-xs font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
              disabled={!selectedProduct.enabled || actionState === "submitting"}
              onClick={() => void disableSelectedProduct()}
              type="button"
            >
              Pasifleştir
            </button>
          ) : null}
        </div>
        {selectedProduct === null ? (
          <StateBlock title="Bir ürün seçin" />
        ) : (
          <div className="mt-4 space-y-4">
            <DetailRows
              rows={[
                ["Ürün", selectedProduct.name],
                [
                  "Station",
                  stations.find((item) => item.stationId === selectedProduct.stationId)?.name ??
                    "-"
                ],
                ["Durum", selectedProduct.enabled ? "enabled" : "disabled"],
                ["Varyant", selectedProduct.variants[0]?.name ?? "-"],
                ["Fiyat", selectedProduct.variants[0]?.priceMinor.toString() ?? "-"],
                ["Modifier", selectedProduct.modifierGroups.length.toString()],
                ["Uygunluk", selectedProduct.availability[0]?.state ?? "default"]
              ]}
            />
            <div className="space-y-2">
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                Varyant ekle
              </p>
              <form className="grid gap-2" onSubmit={addVariant}>
                <input
                  className="h-10 border border-zinc-300 px-3 text-sm"
                  onChange={(event) => setDetailVariantName(event.target.value)}
                  placeholder="Varyant adı"
                  value={detailVariantName}
                />
                <input
                  className="h-10 border border-zinc-300 px-3 text-sm"
                  onChange={(event) => setDetailVariantPrice(event.target.value)}
                  placeholder="Fiyat minor"
                  type="number"
                  value={detailVariantPrice}
                />
                <button
                  className="h-10 border border-zinc-950 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                  disabled={
                    !detailVariantName.trim() ||
                    !detailVariantPrice ||
                    actionState === "submitting"
                  }
                  type="submit"
                >
                  Varyant ekle
                </button>
              </form>
            </div>
            <div className="space-y-2 border-t border-zinc-200 pt-4">
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                Modifier config
              </p>
              <form className="grid gap-2" onSubmit={saveSimpleModifierConfig}>
                <input
                  className="h-10 border border-zinc-300 px-3 text-sm"
                  onChange={(event) => setModifierGroupName(event.target.value)}
                  placeholder="Grup adı"
                  value={modifierGroupName}
                />
                <input
                  className="h-10 border border-zinc-300 px-3 text-sm"
                  onChange={(event) => setModifierOptionName(event.target.value)}
                  placeholder="Seçenek adı"
                  value={modifierOptionName}
                />
                <input
                  className="h-10 border border-zinc-300 px-3 text-sm"
                  onChange={(event) => setModifierOptionPrice(event.target.value)}
                  placeholder="Fiyat farkı minor"
                  type="number"
                  value={modifierOptionPrice}
                />
                <button
                  className="h-10 border border-zinc-950 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                  disabled={
                    !modifierGroupName.trim() ||
                    !modifierOptionName.trim() ||
                    actionState === "submitting"
                  }
                  type="submit"
                >
                  Modifier kaydet
                </button>
              </form>
            </div>
            <div className="space-y-2 border-t border-zinc-200 pt-4">
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                Uygunluk
              </p>
              <input
                className="h-10 w-full border border-zinc-300 px-3 text-sm"
                onChange={(event) => setAvailabilityReason(event.target.value)}
                placeholder="Pasiflik nedeni"
                value={availabilityReason}
              />
              <button
                className="h-10 w-full border border-zinc-950 px-3 text-sm font-medium hover:bg-zinc-50 disabled:cursor-not-allowed disabled:bg-zinc-100"
                disabled={!availabilityReason.trim() || actionState === "submitting"}
                onClick={() => void markUnavailable()}
                type="button"
              >
                Geçici unavailable yap
              </button>
            </div>
          </div>
        )}
        {actionError ? <StateBlock title={actionError} tone="error" /> : null}
      </aside>
    </section>
  );
}

function CustomerMenuApp() {
  const [menu, setMenu] = useState<CustomerMenu | null>(null);
  const [cart, setCart] = useState<CustomerCart | null>(null);
  const [presence, setPresence] = useState<PresenceState | null>(null);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [presenceState, setPresenceState] = useState<"idle" | "checking" | "fresh" | "required">(
    "idle"
  );
  const [cartActionState, setCartActionState] = useState<"idle" | "submitting" | "error">("idle");
  const [submitState, setSubmitState] = useState<"idle" | "submitting" | "error" | "done">("idle");
  const [error, setError] = useState<string | null>(null);

  async function loadCustomerMenu() {
    setState("loading");
    setError(null);
    try {
      const payload = await apiRequest<CustomerMenu>("/api/customer/menu", {
        headers: tenantHeaders()
      });
      setMenu(payload);
      setSelectedCategoryId((current) => current ?? payload.categories[0]?.categoryId ?? null);
      setState("ready");
    } catch (requestError) {
      setMenu(null);
      setError(errorMessageFrom(requestError));
      setState("error");
    }
  }

  useEffect(() => {
    void loadCustomerMenu();
  }, []);

  useEffect(() => {
    const qrToken = customerQrTokenFromLocation();
    if (qrToken) {
      void redeemQrToken(qrToken);
      return;
    }
    void loadPresenceState();
    void loadCart();
  }, []);

  async function redeemQrToken(qrToken: string) {
    setPresenceState("checking");
    try {
      const payload = await apiRequest<PresenceRedeemResult>(
        "/api/customer/table-presence/redeem",
        {
          body: JSON.stringify({qrToken}),
          headers: {
            "Content-Type": "application/json",
            ...tenantHeaders()
          },
          method: "POST"
        }
      );
      setPresence({...payload, fresh: true});
      setPresenceState("fresh");
      await loadCart();
      const url = new URL(window.location.href);
      url.searchParams.delete("qrToken");
      url.searchParams.delete("token");
      window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
    } catch {
      setPresence(null);
      setPresenceState("required");
    }
  }

  async function loadPresenceState() {
    setPresenceState("checking");
    try {
      const payload = await apiRequest<PresenceState>("/api/customer/table-presence", {
        headers: tenantHeaders()
      });
      setPresence(payload);
      setPresenceState(payload.fresh ? "fresh" : "required");
    } catch {
      setPresence(null);
      setPresenceState("required");
    }
  }

  async function loadCart() {
    try {
      const payload = await apiRequest<CustomerCart>("/api/customer/cart", {
        headers: tenantHeaders()
      });
      setCart(payload);
    } catch {
      setCart(null);
    }
  }

  async function addSelectedProductToCart() {
    const variant = selectedProduct?.variants[0];
    if (!selectedProduct || !variant || cartActionState === "submitting") {
      return;
    }
    setCartActionState("submitting");
    try {
      const payload = await apiRequest<CustomerCart>("/api/customer/cart/items", {
        body: JSON.stringify({
          clientCartItemId: `${selectedProduct.productId}:${variant.variantId}`,
          productId: selectedProduct.productId,
          variantId: variant.variantId,
          modifierOptionIds: [],
          quantity: 1,
          note: null
        }),
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": crypto.randomUUID(),
          ...tenantHeaders()
        },
        method: "POST"
      });
      setCart(payload);
      setCartActionState("idle");
    } catch {
      setCartActionState("error");
    }
  }

  async function submitCart() {
    if (!cart || cart.items.length === 0 || submitState === "submitting") {
      return;
    }
    setSubmitState("submitting");
    try {
      await apiRequest("/api/customer/orders", {
        body: JSON.stringify({
          cartVersion: cart.version,
          cartItemIds: cart.items.map((item) => item.clientCartItemId)
        }),
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
          "X-CSRF-Token": crypto.randomUUID(),
          ...tenantHeaders()
        },
        method: "POST"
      });
      await loadCart();
      setSubmitState("done");
    } catch {
      setSubmitState("error");
    }
  }

  const selectedCategory =
    menu?.categories.find((category) => category.categoryId === selectedCategoryId) ?? null;
  const selectedProduct =
    selectedCategory?.products.find((product) => product.productId === selectedProductId) ?? null;

  if (state === "loading") {
    return (
      <main className="min-h-screen bg-stone-100 px-4 py-5 text-zinc-950">
        <StateBlock title="Menü yükleniyor" />
      </main>
    );
  }

  if (state === "error" || menu === null) {
    return (
      <main className="min-h-screen bg-stone-100 px-4 py-5 text-zinc-950">
        <StateBlock title={error ?? "Menü alınamadı"} tone="error" />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-stone-100 text-zinc-950">
      <header className="sticky top-0 z-10 border-b border-zinc-200 bg-white px-4 py-4">
        <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">IoTables</p>
        <div className="mt-1 flex items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold">Menü</h1>
          <div className="flex items-center gap-2">
            <span className="border border-zinc-200 px-2 py-1 text-xs text-zinc-600">
              {presenceState === "fresh"
                ? `QR doğrulandı · ${formatDate(presence?.freshUntil ?? menu.derivedAt)}`
                : presenceState === "checking"
                  ? "QR kontrol ediliyor"
                  : "Sipariş için güncel QR gerekir"}
            </span>
            <span className="border border-zinc-200 px-2 py-1 text-xs font-medium">
              Sepet {cart?.items.length ?? 0} · {cart?.displaySubtotalMinor ?? 0}
            </span>
          </div>
        </div>
      </header>
      <section className="px-4 py-4">
        {menu.categories.length === 0 ? (
          <StateBlock title="Şu anda siparişe açık ürün yok" />
        ) : (
          <div className="space-y-4">
            <div className="flex gap-2 overflow-x-auto pb-1">
              {menu.categories.map((category) => (
                <button
                  className={`h-10 shrink-0 border px-4 text-sm font-medium ${
                    selectedCategoryId === category.categoryId
                      ? "border-emerald-600 bg-emerald-50 text-emerald-950"
                      : "border-zinc-300 bg-white"
                  }`}
                  key={category.categoryId}
                  onClick={() => {
                    setSelectedCategoryId(category.categoryId);
                    setSelectedProductId(null);
                  }}
                  type="button"
                >
                  {category.name}
                </button>
              ))}
            </div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {(selectedCategory?.products ?? []).map((product) => (
                <button
                  className={`min-h-36 border bg-white px-4 py-4 text-left hover:bg-zinc-50 ${
                    selectedProductId === product.productId
                      ? "border-emerald-600"
                      : "border-zinc-200"
                  }`}
                  key={product.productId}
                  onClick={() => setSelectedProductId(product.productId)}
                  type="button"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h2 className="text-base font-semibold">{product.name}</h2>
                      {product.description ? (
                        <p className="mt-1 text-sm text-zinc-600">{product.description}</p>
                      ) : null}
                    </div>
                    <span className="shrink-0 text-sm font-semibold">
                      {product.variants[0]?.priceMinor ?? 0}
                    </span>
                  </div>
                  <p className="mt-4 text-xs text-zinc-500">
                    {product.variants.length} varyant · {product.modifierGroups.length} seçenek grubu
                  </p>
                </button>
              ))}
            </div>
          </div>
        )}
      </section>
      {selectedProduct ? (
        <aside className="fixed inset-x-0 bottom-0 border-t border-zinc-200 bg-white px-4 py-4 shadow-lg md:left-auto md:right-6 md:bottom-6 md:w-96 md:border">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">{selectedProduct.name}</h2>
              <p className="mt-1 text-sm text-zinc-600">
                {selectedProduct.description ?? "Ürün detayları"}
              </p>
            </div>
            <button
              className="h-9 border border-zinc-300 px-3 text-sm font-medium"
              onClick={() => setSelectedProductId(null)}
              type="button"
            >
              Kapat
            </button>
          </div>
          <div className="mt-4 space-y-3 text-sm">
            {selectedProduct.variants.map((variant) => (
              <div className="flex justify-between border-b border-zinc-200 py-2" key={variant.variantId}>
                <span>{variant.name}</span>
                <span className="font-medium">{variant.priceMinor}</span>
              </div>
            ))}
            {selectedProduct.modifierGroups.map((group) => (
              <div className="border-b border-zinc-200 py-2" key={group.groupId}>
                <p className="font-medium">{group.name}</p>
                <p className="mt-1 text-xs text-zinc-500">
                  {group.required ? "Zorunlu" : "Opsiyonel"} · {group.options.length} seçenek
                </p>
              </div>
            ))}
          </div>
          <button
            className="mt-4 h-11 w-full border border-zinc-950 bg-zinc-950 px-4 text-sm font-medium text-white disabled:cursor-not-allowed disabled:border-zinc-300 disabled:bg-zinc-300"
            disabled={!selectedProduct.variants[0] || cartActionState === "submitting"}
            onClick={() => void addSelectedProductToCart()}
            type="button"
          >
            {cartActionState === "error" ? "Sepete eklenemedi" : "Sepete ekle"}
          </button>
        </aside>
      ) : null}
      {cart && cart.items.length > 0 ? (
        <div className="fixed inset-x-0 bottom-0 border-t border-zinc-200 bg-white px-4 py-3 md:left-6 md:right-auto md:bottom-6 md:w-80 md:border">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">{cart.items.length} ürün</p>
              <p className="text-xs text-zinc-500">{cart.displaySubtotalMinor} {cart.currency}</p>
            </div>
            <button
              className="h-10 border border-zinc-950 bg-zinc-950 px-4 text-sm font-medium text-white disabled:cursor-not-allowed disabled:border-zinc-300 disabled:bg-zinc-300"
              disabled={submitState === "submitting"}
              onClick={() => void submitCart()}
              type="button"
            >
              {submitState === "done"
                ? "Sipariş alındı"
                : submitState === "error"
                  ? "Tekrar dene"
                  : "Sipariş ver"}
            </button>
          </div>
        </div>
      ) : null}
    </main>
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
  const [state, setState] = useState<"idle" | "otp" | "submitting" | "success" | "error">("idle");
  const [otpState, setOtpState] = useState<TenantCreationOtpState | null>(null);
  const [otpCode, setOtpCode] = useState("");
  const [otpGsm, setOtpGsm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProvisioningResult | null>(null);

  const gsm = form.gsmNumber.trim();
  const otpMatchesGsm = otpState !== null && otpGsm === gsm;
  const canRequestOtp = Boolean(gsm) && state !== "submitting";
  const canSubmit =
    form.name.trim() &&
    form.subdomain.trim() &&
    gsm &&
    otpMatchesGsm &&
    otpCode.trim().length === 6;

  async function requestOtp() {
    if (!canRequestOtp) {
      return;
    }
    setState("submitting");
    setError(null);
    try {
      const payload = await apiRequest<TenantCreationOtpState>(
        "/api/platform/tenant-creation-otp/begin",
        {
          body: JSON.stringify({ gsmNumber: gsm }),
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": crypto.randomUUID()
          },
          method: "POST"
        }
      );
      setOtpState(payload);
      setOtpGsm(gsm);
      setOtpCode("");
      setState("otp");
    } catch (otpError) {
      setError(errorMessageFrom(otpError));
      setState("error");
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit || state === "submitting") {
      return;
    }

    setState("submitting");
    setError(null);
    try {
      const payload = await apiRequest<ProvisioningResult>("/api/platform/tenants", {
        body: JSON.stringify({
          name: form.name.trim(),
          subdomain: form.subdomain.trim(),
          gsmNumber: gsm,
          sector: form.sector || undefined,
          capacity: form.capacity ? Number(form.capacity) : undefined,
          address: form.address.trim() || undefined,
          otpChallengeId: otpState?.otpChallengeId,
          otpCode: otpCode.trim()
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
              onChange={(value) => {
                setForm((current) => ({ ...current, gsmNumber: value }));
                if (value.trim() !== otpGsm) {
                  setOtpState(null);
                  setOtpCode("");
                }
              }}
              required
              value={form.gsmNumber}
            />
            <div className="border border-zinc-200 bg-zinc-50 px-3 py-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">GSM doğrulaması</p>
                  <p className="mt-1 text-xs text-zinc-600">
                    Tenant oluşturma bu numaraya ait OTP doğrulanmadan başlamaz.
                  </p>
                </div>
                <button
                  className="h-9 shrink-0 border border-zinc-300 bg-white px-3 text-sm font-medium hover:bg-zinc-100 disabled:cursor-not-allowed disabled:text-zinc-400"
                  disabled={!canRequestOtp}
                  onClick={requestOtp}
                  type="button"
                >
                  Kod iste
                </button>
              </div>
              {otpState ? (
                <div className="mt-3 grid gap-2">
                  <p className="text-xs text-zinc-600">
                    Kod gönderildi: {otpState.targetHint}
                  </p>
                  <FieldText label="SMS kodu" onChange={setOtpCode} required value={otpCode} />
                </div>
              ) : null}
            </div>
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
                <p className="font-semibold">{tenantHost(result.subdomain)}</p>
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
    throw new ApiRequestError(payload);
  }

  return (await response.json()) as T;
}

function errorMessageFrom(error: unknown): string {
  if (error instanceof ApiRequestError) {
    const baseMessage = apiErrorMessages[error.code] ?? "İşlem tamamlanamadı.";
    const fieldMessage =
      error.fieldErrors.length > 0
        ? ` ${error.fieldErrors.map((field) => field.message).join(" ")}`
        : "";
    const requestMessage = error.requestId ? ` Hata kodu: ${error.requestId}` : "";
    return `${baseMessage}${fieldMessage}${requestMessage}`;
  }
  return error instanceof Error ? error.message : "İstek tamamlanamadı.";
}

const apiErrorMessages: Record<string, string> = {
  active_session_blocks_disable: "Aktif oturum varken bu kayıt devre dışı bırakılamaz.",
  bad_request: "İstek biçimi geçersiz.",
  check_closed: "Adisyon kapalı olduğu için bu işlem yapılamaz.",
  csrf_required: "Güvenlik doğrulaması eksik. Sayfayı yenileyip tekrar deneyin.",
  display_not_authenticated: "Masa ekranı doğrulanamadı.",
  duplicate_category: "Aynı ad veya sıra ile kategori zaten var.",
  duplicate_hall: "Bu salon zaten var.",
  duplicate_menu_item: "Aynı adla ürün, varyant veya seçenek zaten var.",
  duplicate_station: "Bu istasyon zaten var.",
  duplicate_subdomain: "Bu subdomain zaten kullanılıyor.",
  duplicate_table: "Bu masa zaten var.",
  duplicate_tenant_gsm: "Bu GSM numarasıyla kayıtlı bir tenant zaten var.",
  duplicate_username: "Bu kullanıcı adı zaten kullanılıyor.",
  fresh_presence_required: "Devam etmek için masadaki güncel QR kodu tekrar okutun.",
  idempotency_conflict: "Bu işlem anahtarı farklı bir istek için kullanılmış.",
  idempotency_key_required: "Bu işlem için tekrar önleme anahtarı eksik.",
  invalid_credentials: "Kullanıcı adı veya şifre hatalı.",
  invalid_lifecycle_transition: "Bu tenant durumu için istenen geçiş yapılamaz.",
  invalid_preparation_transition: "Bu hazırlık durumunda istenen işlem yapılamaz.",
  invalid_session_state: "Oturumun mevcut durumu bu işleme izin vermiyor.",
  invalid_state: "Mevcut durum bu işleme izin vermiyor.",
  item_not_orderable: "Bu ürün şu anda sipariş edilemiyor.",
  menu_item_requires_default_variant: "Ürünün sipariş edilebilir bir varsayılan varyantı olmalı.",
  not_authorized: "Bu işlemi yapma yetkiniz yok.",
  not_found_or_hidden: "Kayıt bulunamadı veya bu oturum için görünür değil.",
  otp_expired: "Doğrulama kodunun süresi doldu. Yeni kod isteyin.",
  otp_invalid: "Doğrulama kodu hatalı.",
  otp_locked: "Çok fazla deneme yapıldı. Bir süre sonra tekrar deneyin.",
  overpayment_not_allowed: "Ödeme tutarı kalan bakiyeyi aşamaz.",
  payment_cannot_be_voided: "Bu ödeme iptal edilemez.",
  product_variant_mismatch: "Seçilen varyant bu ürüne ait değil.",
  rate_limit_exceeded: "Çok fazla deneme yapıldı. Bir süre sonra tekrar deneyin.",
  reason_required: "Bu işlem için açıklama girmek zorunlu.",
  setup_token_invalid: "Şifre kurulum bağlantısı geçersiz veya süresi dolmuş.",
  session_expired: "Oturum süresi doldu. Tekrar giriş yapın.",
  station_has_active_menu_items: "Bu istasyona bağlı aktif menü ürünleri var.",
  station_has_active_work: "Bu istasyonda aktif hazırlık işi var.",
  station_unavailable: "Seçilen istasyon kullanılamıyor.",
  tenant_unavailable: "Bu işletme şu anda erişilebilir değil.",
  token_consumed: "Bu QR kod daha önce kullanılmış. Masadaki yeni kodu okutun.",
  token_expired: "QR kodun süresi doldu. Masadaki yeni kodu okutun.",
  unauthenticated: "Devam etmek için giriş yapın.",
  validation_failed: "Bazı alanlar hatalı veya eksik.",
  wrong_app_scope: "Bu oturum bu uygulamaya erişemez.",
  wrong_scope: "Bu oturum bu işlem için uygun değil."
};

function auditMetadataSummary(metadata: Record<string, unknown>): string {
  const changedFields = metadata.changedFields;
  if (Array.isArray(changedFields) && changedFields.length > 0) {
    const safeChangedFields = changedFields
      .filter((field): field is string => typeof field === "string")
      .filter(isAuditMetadataKeyVisible);
    return safeChangedFields.length > 0
      ? `Değişen alanlar: ${safeChangedFields.map(auditMetadataKeyLabel).join(", ")}`
      : "Ek detay yok";
  }
  const keys = Object.keys(metadata).filter(isAuditMetadataKeyVisible);
  return keys.length > 0 ? keys.map(auditMetadataKeyLabel).join(", ") : "Ek detay yok";
}

function isAuditMetadataKeyVisible(key: string): boolean {
  const normalized = key.toLowerCase();
  if (
    normalized.includes("credential") ||
    normalized.includes("dns") ||
    normalized.includes("hash") ||
    normalized.includes("otp") ||
    normalized.includes("password") ||
    normalized.includes("secret") ||
    normalized.includes("token")
  ) {
    return false;
  }
  return visibleAuditMetadataKeys.has(key);
}

function auditMetadataKeyLabel(key: string): string {
  return auditMetadataLabels[key] ?? key;
}

const visibleAuditMetadataKeys = new Set([
  "changedFields",
  "role",
  "sector",
  "subdomain",
  "templateKey",
  "templateVersion",
  "username"
]);

const auditMetadataLabels: Record<string, string> = {
  changedFields: "değişen alanlar",
  role: "rol",
  sector: "sektör",
  subdomain: "subdomain",
  templateKey: "starter şablonu",
  templateVersion: "starter sürümü",
  username: "kullanıcı adı"
};

const tenantRootDomains = ["iotables.net", "tabflow.uk"] as const;

function tenantRootDomainFromHostname(hostname: string): string | null {
  return tenantRootDomains.find(
    (rootDomain) => hostname === rootDomain || hostname.endsWith(`.${rootDomain}`)
  ) ?? null;
}

function tenantSubdomainFromHostname(hostname: string): string | null {
  const rootDomain = tenantRootDomainFromHostname(hostname);
  if (!rootDomain || !hostname.endsWith(`.${rootDomain}`)) {
    return null;
  }

  const subdomain = hostname.slice(0, -(rootDomain.length + 1));
  return subdomain && subdomain !== "platform" ? subdomain : null;
}

function tenantRootDomainFromLocation(): string {
  return tenantRootDomainFromHostname(window.location.hostname.toLowerCase()) ?? "iotables.net";
}

function tenantHost(subdomain: string): string {
  return `${subdomain}.${tenantRootDomainFromLocation()}`;
}

type AppSurface =
  | "cashier"
  | "customer"
  | "platform"
  | "service"
  | "station"
  | "tenant"
  | "tenant-public";

function detectAppSurface(): AppSurface {
  const params = new URLSearchParams(window.location.search);
  if (params.get("app") === "cashier") {
    return "cashier";
  }
  if (params.get("app") === "customer") {
    return "customer";
  }
  if (params.get("app") === "service") {
    return "service";
  }
  if (params.get("app") === "station") {
    return "station";
  }
  if (params.get("app") === "tenant") {
    return "tenant";
  }
  if (params.get("app") === "tenant-public") {
    return "tenant-public";
  }
  if (window.location.pathname.startsWith("/order")) {
    return "customer";
  }
  if (window.location.pathname.startsWith("/cashier")) {
    return "cashier";
  }
  if (window.location.pathname.startsWith("/station")) {
    return "station";
  }
  if (window.location.pathname.startsWith("/service")) {
    return "service";
  }
  if (window.location.pathname.startsWith("/login") || window.location.pathname.startsWith("/admin")) {
    return tenantSubdomainFromHostname(window.location.hostname.toLowerCase()) ? "tenant" : "platform";
  }
  return tenantSubdomainFromHostname(window.location.hostname.toLowerCase())
    ? "tenant-public"
    : "platform";
}

function requiresTenantContext(appSurface: AppSurface): boolean {
  return (
    appSurface === "tenant" ||
    appSurface === "tenant-public" ||
    appSurface === "service" ||
    appSurface === "station" ||
    appSurface === "cashier" ||
    appSurface === "customer"
  );
}

function isTenantLoginSurface(
  appSurface: AppSurface
): appSurface is "cashier" | "service" | "station" | "tenant" {
  return (
    appSurface === "tenant" ||
    appSurface === "service" ||
    appSurface === "cashier" ||
    appSurface === "station"
  );
}

function tenantLoginScopeForSurface(
  appSurface: "cashier" | "service" | "station" | "tenant"
): "cashier" | "service" | "station" | "tenant" {
  return appSurface;
}

function tenantLoginDefaultUsername(appSurface: "cashier" | "service" | "station" | "tenant") {
  return appSurface === "tenant" ? tenantSubdomainFromLocation() : "";
}

function tenantLoginHeading(appSurface: "cashier" | "service" | "station" | "tenant"): string {
  if (appSurface === "service") {
    return "Servis girişi";
  }
  if (appSurface === "cashier") {
    return "Kasa girişi";
  }
  if (appSurface === "station") {
    return "İstasyon girişi";
  }
  return "Tenant owner girişi";
}

function tenantSubdomainFromLocation(): string {
  const params = new URLSearchParams(window.location.search);
  const explicitTenant = params.get("tenant")?.trim().toLowerCase();
  if (explicitTenant) {
    return explicitTenant;
  }

  return tenantSubdomainFromHostname(window.location.hostname.toLowerCase()) ?? "demo";
}

function customerQrTokenFromLocation(): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get("qrToken")?.trim() || params.get("token")?.trim() || null;
}

function tenantHeaders(): Record<string, string> {
  const hostname = window.location.hostname.toLowerCase();
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return {"X-Tenant-Subdomain": tenantSubdomainFromLocation()};
  }
  return {};
}

function tenantWorkspaceFromPath(pathname: string): TenantWorkspaceKey {
  const workspace = tenantWorkspaces.find((item) => item.path === pathname);
  return workspace?.key ?? "dashboard";
}

function tenantWorkspacePath(workspace: TenantWorkspaceKey): string {
  return tenantWorkspaces.find((item) => item.key === workspace)?.path ?? "/admin";
}

function tenantWorkspaceLabel(workspace: TenantWorkspaceKey): string {
  return tenantWorkspaces.find((item) => item.key === workspace)?.label ?? "Dashboard";
}

function staffRoleLabel(role: string): string {
  const labels: Record<string, string> = {
    cashier: "Kasiyer",
    service_staff: "Servis personeli",
    station_staff: "İstasyon personeli",
    tenant_admin: "Tenant admin"
  };
  return labels[role] ?? role.replaceAll("_", " ");
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function downloadTextFile(fileName: string, content: string, mimeType: string) {
  const blob = new Blob([content], {type: mimeType});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

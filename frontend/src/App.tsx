const appSurfaces = [
  "PlatformApp",
  "TenantApp",
  "CustomerApp",
  "StationStaffApp",
  "ServiceStaffApp",
  "CashierApp"
];

export function App() {
  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center px-6 py-12">
        <div className="space-y-3">
          <p className="text-sm font-medium uppercase text-emerald-300">IoTables</p>
          <h1 className="max-w-3xl text-4xl font-semibold leading-tight md:text-6xl">
            Operational ordering workspace
          </h1>
        </div>

        <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {appSurfaces.map((surface) => (
            <div
              className="border border-zinc-800 bg-zinc-900/70 px-4 py-4 text-sm font-medium text-zinc-200"
              key={surface}
            >
              {surface}
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

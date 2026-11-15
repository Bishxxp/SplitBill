
export default function OverviewSkeleton() {
  return (
    <div
      role="status"
      aria-label="Loading group information"
      className="animate-pulse space-y-6 motion-reduce:animate-none"
    >
      {/* Balance Skeleton */}
      <section>
        <div className="mb-4 h-6 w-48 rounded bg-slate-200" />

        <div className="grid gap-4 sm:grid-cols-3">
          {[1, 2, 3].map((item) => (
            <div
              key={item}
              className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5"
            >
              <div className="h-4 w-20 rounded bg-slate-200" />
              <div className="h-8 w-32 rounded bg-slate-200" />
              <div className="h-3 w-24 rounded bg-slate-100" />
            </div>
          ))}
        </div>
      </section>

      {/* Expense List Skeleton */}
      <section>
        <div className="mb-4 h-6 w-36 rounded bg-slate-200" />

        <div className="space-y-3">
          {[1, 2, 3].map((item) => (
            <div
              key={item}
              className="rounded-2xl border border-slate-200 bg-white p-5"
            >
              <div className="flex items-center justify-between gap-4">
                <div className="space-y-3">
                  <div className="h-5 w-40 max-w-full rounded bg-slate-200" />
                  <div className="h-3 w-24 rounded bg-slate-100" />
                </div>

                <div className="h-6 w-24 rounded bg-slate-200" />
              </div>
            </div>
          ))}
        </div>
      </section>

      <span className="sr-only">
        Loading expenses and balances...
      </span>
    </div>
  );
}

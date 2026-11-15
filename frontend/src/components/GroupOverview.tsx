"use client";

import { useEffect, useState } from "react";
import ExpenseForm from "@/components/ExpenseForm";
import DeleteExpenseButton from "@/components/DeleteExpenseButton";
import OverviewSkeleton from "@/components/OverviewSkeleton";
import { formatMoney } from "@/lib/format";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Types
type Group = {
  id: number;
  name: string;
  members: string[];
};

type Expense = {
  id: number;
  group_id: number;
  description: string;
  paid_by: string;
  amount: string;
  shares: Record<string, string>;
  is_deleted: boolean;
  created_at: string;
};

type MemberBalance = {
  username: string;
  balance: string;
};

type BalancesResponse = {
  group_id: number;
  balances: MemberBalance[];
};

type OverviewData = {
  expenses: Expense[];
  balances: MemberBalance[];
};

type Props = {
  group: Group;
  user: string;
};

export default function GroupOverview({ group, user }: Props) {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadOverview() {
      setLoading(true);
      setError(null);
      setData(null);

      try {
        const headers = { "X-User": user };

        const [expensesResponse, balancesResponse] = await Promise.all([
          fetch(`${API_URL}/groups/${group.id}/expenses`, {
            headers,
            signal: controller.signal,
          }),
          fetch(`${API_URL}/groups/${group.id}/balances`, {
            headers,
            signal: controller.signal,
          }),
        ]);

        if (!expensesResponse.ok || !balancesResponse.ok) {
          throw new Error("Failed to load group information");
        }

        const expenses: Expense[] = await expensesResponse.json();

        const balanceResult: BalancesResponse = await balancesResponse.json();

        if (!controller.signal.aborted) {
          setData({
            expenses,
            balances: balanceResult.balances,
          });
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "Something went wrong");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadOverview();

    return () => controller.abort();
  }, [group.id, user, refreshKey]);

  return (
    <section className="mt-8 space-y-6">
      {/* Group Header */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-medium text-orange-600">SELECTED GROUP</p>

        <h2 className="mt-2 text-2xl font-bold text-slate-900">{group.name}</h2>

        <p className="mt-2 text-sm text-slate-500">
          Members: {group.members.join(", ")}
        </p>
      </div>

      {/* Add Expense Form */}
      <ExpenseForm
        group={group}
        user={user}
        onCreated={() => {
          setRefreshKey((previous) => previous + 1);
        }}
      />

      {/* Skeleton Loading */}
      {loading && <OverviewSkeleton />}

      {/* Error State with Retry */}
      {error && !loading && (
        <div
          role="alert"
          className="rounded-2xl border border-red-200 bg-red-50 p-6"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-semibold text-red-800">
                Unable to load group information
              </h3>

              <p className="mt-2 text-sm text-red-600">{error}</p>

              <p className="mt-1 text-sm text-red-500">
                Please check your connection and try again.
              </p>
            </div>

            <button
              type="button"
              onClick={() => {
                setRefreshKey((previous) => previous + 1);
              }}
              className="shrink-0 rounded-xl bg-red-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-red-700"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {data && !loading && (
        <>
          {/* Balance Cards */}
          <div>
            <h3 className="mb-4 text-xl font-bold text-slate-900">
              Member Balances
            </h3>

            <div className="grid gap-4 sm:grid-cols-3">
              {data.balances.map((member) => {
                const isNegative = member.balance.startsWith("-");

                const isZero = member.balance === "0.00";

                return (
                  <div
                    key={member.username}
                    className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
                  >
                    <p className="text-sm capitalize text-slate-500">
                      {member.username}
                    </p>

                    <p
                      className={`mt-3 text-2xl font-bold ${
                        isNegative
                          ? "text-red-600"
                          : isZero
                            ? "text-slate-700"
                            : "text-emerald-600"
                      }`}
                    >
                      {formatMoney(member.balance)}
                    </p>

                    <p className="mt-2 text-xs text-slate-400">
                      {isZero
                        ? "Settled up"
                        : isNegative
                          ? "Owes money"
                          : "Gets money back"}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Expense List */}
          <div>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-bold text-slate-900">Expenses</h3>

              <span className="rounded-full bg-orange-50 px-3 py-1 text-xs font-medium text-orange-700">
                {data.expenses.length} expenses
              </span>
            </div>

            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
              {data.expenses.length === 0 ? (
                <div className="p-10 text-center text-slate-500">
                  No expenses yet.
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {data.expenses.map((expense) => (
                    <div key={expense.id} className="p-5">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="min-w-0 flex-1">
                          <h4 className="break-words font-semibold text-slate-900">
                            {expense.description}
                          </h4>

                          <p className="mt-1 text-sm capitalize text-slate-500">
                            Paid by {expense.paid_by}
                          </p>
                        </div>

                        <p className="shrink-0 text-lg font-bold text-slate-900">
                          {formatMoney(expense.amount)}
                        </p>
                      </div>

                      <details className="mt-4">
                        <summary className="cursor-pointer text-sm font-medium text-orange-600">
                          View shares
                        </summary>

                        <div className="mt-3 space-y-2 rounded-xl bg-slate-50 p-4">
                          {Object.entries(expense.shares).map(
                            ([username, amount]) => (
                              <div
                                key={username}
                                className="flex justify-between text-sm"
                              >
                                <span className="capitalize text-slate-600">
                                  {username}
                                </span>
                                <span className="font-medium text-slate-900">
                                  {formatMoney(amount)}
                                </span>
                              </div>
                            ),
                          )}
                        </div>
                      </details>
                      {user === expense.paid_by && (
                        <DeleteExpenseButton
                          groupId={group.id}
                          expenseId={expense.id}
                          user={user}
                          onDeleted={() => {
                            setRefreshKey((previous) => previous + 1);
                          }}
                        />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
}

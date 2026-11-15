
"use client";

import { useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Props = {
  groupId: number;
  expenseId: number;
  user: string;
  onDeleted: () => void;
};

export default function DeleteExpenseButton({
  groupId,
  expenseId,
  user,
  onDeleted,
}: Props) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    if (deleting) return;

    setDeleting(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/groups/${groupId}/expenses/${expenseId}`,
        {
          method: "DELETE",
          headers: {
            "X-User": user,
          },
        }
      );

      if (!response.ok) {
        const body: unknown = await response.json().catch(() => null);
        let message = `Delete failed (${response.status})`;

        if (body && typeof body === "object" && "detail" in body) {
          const detail = (body as { detail: unknown }).detail;

          if (typeof detail === "string") {
            message = detail;
          }
        }

        throw new Error(message);
      }

      setConfirming(false);
      onDeleted();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete expense"
      );
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="mt-4 border-t border-slate-100 pt-4">
      {!confirming ? (
        <button
          type="button"
          onClick={() => {
            setError(null);
            setConfirming(true);
          }}
          className="rounded-lg px-3 py-2 text-sm font-medium text-red-600 transition hover:bg-red-50"
        >
          Delete Expense
        </button>
      ) : (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4">
          <p className="font-medium text-red-800">
            Delete this expense?
          </p>

          <p className="mt-1 text-sm text-red-600">
            This expense will be removed from balances.
          </p>

          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleDelete}
              disabled={deleting}
              className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
            >
              {deleting ? "Deleting..." : "Confirm Delete"}
            </button>

            <button
              type="button"
              onClick={() => {
                setConfirming(false);
                setError(null);
              }}
              disabled={deleting}
              className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {error && (
        <p role="alert" className="mt-3 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

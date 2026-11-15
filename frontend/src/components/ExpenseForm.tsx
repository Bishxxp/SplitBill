
"use client";

import { useRef, useState, type FormEvent } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const MAX_CENTS = 999_999_999_999;

type SplitType = "equal" | "exact";

type Group = {
  id: number;
  name: string;
  members: string[];
};

type Props = {
  group: Group;
  user: string;
  onCreated: () => void;
};

type PreviewShare = {
  username: string;
  cents: number;
};

// Convert a money string into integer satang.
// Examples: "100.00" -> 10000, "0.10" -> 10
function parseCents(value: string): number | null {
  const input = value.trim();

  if (!/^\d+(?:\.\d{1,2})?$/.test(input)) {
    return null;
  }

  const [baht, satang = ""] = input.split(".");
  const cents =
    Number(baht) * 100 + Number(satang.padEnd(2, "0"));

  if (!Number.isSafeInteger(cents) || cents > MAX_CENTS) {
    return null;
  }

  return cents;
}

// Convert integer satang to a money string.
function formatCents(cents: number): string {
  const sign = cents < 0 ? "-" : "";
  const absolute = Math.abs(cents);

  const baht = Math.floor(absolute / 100);
  const satang = String(absolute % 100).padStart(2, "0");

  return `${sign}${baht}.${satang}`;
}

export default function ExpenseForm({
  group,
  user,
  onCreated,
}: Props) {
  // Form state
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [paidBy, setPaidBy] = useState(
    group.members.includes(user) ? user : group.members[0] ?? ""
  );

  const [splitType, setSplitType] = useState<SplitType>("equal");

  const [selectedMembers, setSelectedMembers] = useState<string[]>(
    group.members
  );

  const [exactShares, setExactShares] = useState<Record<string, string>>(
    Object.fromEntries(group.members.map((name) => [name, "0.00"]))
  );

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Preserve the key when retrying the same request.
  const pendingRequest = useRef<{
    signature: string;
    key: string;
  } | null>(null);

  function clearFeedback() {
    setError(null);
    setSuccess(null);
  }

  function toggleMember(name: string) {
    clearFeedback();

    setSelectedMembers((previous) =>
      previous.includes(name)
        ? previous.filter((member) => member !== name)
        : [...previous, name]
    );
  }

  // Keep member order consistent with the Backend.
  const members = group.members.filter((name) =>
    selectedMembers.includes(name)
  );

  // Calculate live preview using integer satang.
  const totalCents = parseCents(amount);

  let previewError: string | null = null;
  let previewShares: PreviewShare[] = [];

  if (totalCents === null || totalCents <= 0) {
    previewError = "Enter a positive amount with up to 2 decimal places.";
  } else if (members.length === 0) {
    previewError = "Select at least one member.";
  } else if (splitType === "equal") {
    const base = Math.floor(totalCents / members.length);
    const remainder = totalCents % members.length;

    previewShares = members.map((username, index) => ({
      username,
      cents: base + (index < remainder ? 1 : 0),
    }));
  } else {
    for (const username of members) {
      const cents = parseCents(exactShares[username] ?? "");

      if (cents === null) {
        previewError = `Invalid amount for ${username}.`;
        break;
      }

      previewShares.push({ username, cents });
    }

    if (!previewError) {
      const allocated = previewShares.reduce(
        (sum, share) => sum + share.cents,
        0
      );

      if (allocated !== totalCents) {
        previewError = `Exact shares total ${formatCents(
          allocated
        )}, but the expense is ${formatCents(totalCents)}.`;
      }
    }
  }

  const canSubmit =
    description.trim().length > 0 &&
    paidBy.length > 0 &&
    previewError === null &&
    totalCents !== null &&
    !submitting;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!canSubmit || totalCents === null) {
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    const payload = {
      description: description.trim(),
      paid_by: paidBy,
      amount: formatCents(totalCents),
      split:
        splitType === "equal"
          ? {
              type: "equal",
              members,
            }
          : {
              type: "exact",
              shares: Object.fromEntries(
                previewShares.map((share) => [
                  share.username,
                  formatCents(share.cents),
                ])
              ),
            },
    };

    // A retry with the same body reuses the same key.
    const signature = JSON.stringify({
      group_id: group.id,
      user,
      payload,
    });

    if (pendingRequest.current?.signature !== signature) {
      pendingRequest.current = {
        signature,
        key: crypto.randomUUID(),
      };
    }

    const idempotencyKey = pendingRequest.current.key;

    try {
      const response = await fetch(
        `${API_URL}/groups/${group.id}/expenses`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-User": user,
            "Idempotency-Key": idempotencyKey,
          },
          body: JSON.stringify(payload),
        }
      );

      if (!response.ok) {
        const body: unknown = await response.json().catch(() => null);
        let message = `Request failed (${response.status})`;

        if (body && typeof body === "object" && "detail" in body) {
          const detail = (body as { detail: unknown }).detail;

          if (typeof detail === "string") {
            message = detail;
          }
        }

        throw new Error(message);
      }

      // Successful: the next expense gets a new key.
      pendingRequest.current = null;

      setDescription("");
      setAmount("");
      setSplitType("equal");
      setSelectedMembers([...group.members]);
      setExactShares(
        Object.fromEntries(
          group.members.map((name) => [name, "0.00"])
        )
      );

      setSuccess("Expense added successfully!");

      // Tell the parent to refresh expenses and balances.
      onCreated();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save expense"
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-slate-900">
          Add New Expense
        </h3>
        <p className="mt-1 text-sm text-slate-500">
          Add a shared expense to {group.name}.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Description */}
        <div>
          <label
            htmlFor="expense-description"
            className="mb-2 block text-sm font-medium text-slate-700"
          >
            Description
          </label>

          <input
            id="expense-description"
            type="text"
            value={description}
            maxLength={255}
            onChange={(event) => {
              setDescription(event.target.value);
              clearFeedback();
            }}
            placeholder="e.g. Dinner at restaurant"
            className="w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-900 outline-none focus:border-orange-500"
            required
          />
        </div>

        {/* Amount and Payer */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label
              htmlFor="expense-amount"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Amount (THB)
            </label>

            <input
              id="expense-amount"
              type="text"
              inputMode="decimal"
              value={amount}
              onChange={(event) => {
                setAmount(event.target.value);
                clearFeedback();
              }}
              placeholder="100.00"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-900 outline-none focus:border-orange-500"
              required
            />
          </div>

          <div>
            <label
              htmlFor="expense-payer"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Paid By
            </label>

            <select
              id="expense-payer"
              value={paidBy}
              onChange={(event) => {
                setPaidBy(event.target.value);
                clearFeedback();
              }}
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 capitalize text-slate-900 outline-none focus:border-orange-500"
            >
              {group.members.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Split Type */}
        <fieldset>
          <legend className="mb-3 text-sm font-medium text-slate-700">
            Split Type
          </legend>

          <div className="grid grid-cols-2 gap-3">
            {(["equal", "exact"] as const).map((type) => (
              <label
                key={type}
                className={`cursor-pointer rounded-xl border p-4 text-center capitalize transition ${
                  splitType === type
                    ? "border-orange-500 bg-orange-50 text-orange-700"
                    : "border-slate-200 text-slate-600"
                }`}
              >
                <input
                  type="radio"
                  name="split-type"
                  value={type}
                  checked={splitType === type}
                  onChange={() => {
                    setSplitType(type);
                    clearFeedback();
                  }}
                  className="sr-only"
                />
                {type} Split
              </label>
            ))}
          </div>
        </fieldset>

        {/* Members */}
        <fieldset>
          <legend className="mb-3 text-sm font-medium text-slate-700">
            Split Between
          </legend>

          <div className="space-y-3">
            {group.members.map((name) => {
              const selected = selectedMembers.includes(name);

              return (
                <div
                  key={name}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 p-4"
                >
                  <label className="flex cursor-pointer items-center gap-3">
                    <input
                      type="checkbox"
                      checked={selected}
                      onChange={() => toggleMember(name)}
                      className="h-4 w-4 accent-orange-500"
                    />
                    <span className="font-medium capitalize text-slate-800">
                      {name}
                    </span>
                  </label>

                  {splitType === "exact" && selected && (
                    <input
                      type="text"
                      inputMode="decimal"
                      aria-label={`${name} share`}
                      value={exactShares[name] ?? ""}
                      onChange={(event) => {
                        setExactShares((previous) => ({
                          ...previous,
                          [name]: event.target.value,
                        }));
                        clearFeedback();
                      }}
                      placeholder="0.00"
                      className="w-32 rounded-lg border border-slate-200 px-3 py-2 text-right text-slate-900 outline-none focus:border-orange-500"
                    />
                  )}
                </div>
              );
            })}
          </div>
        </fieldset>

        {/* Live Preview */}
        <div className="rounded-xl bg-slate-50 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h4 className="font-semibold text-slate-900">
              Live Split Preview
            </h4>

            <span className="text-xs text-slate-500">
              {splitType === "equal" ? "Equal" : "Exact"}
            </span>
          </div>

          {previewShares.length > 0 && (
            <div className="space-y-3">
              {previewShares.map((share) => (
                <div
                  key={share.username}
                  className="flex justify-between text-sm"
                >
                  <span className="capitalize text-slate-600">
                    {share.username}
                  </span>

                  <span className="font-medium text-slate-900">
                    ฿{formatCents(share.cents)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {previewError && (
            <p className="mt-3 text-sm text-red-600">
              {previewError}
            </p>
          )}

          {previewError === null && totalCents !== null && (
            <div className="mt-4 flex justify-between border-t border-slate-200 pt-4 font-semibold text-slate-900">
              <span>Total</span>
              <span>฿{formatCents(totalCents)}</span>
            </div>
          )}
        </div>

        {/* Feedback */}
        {error && (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        )}

        {success && (
          <p role="status" className="text-sm text-emerald-600">
            {success}
          </p>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={!canSubmit}
          className="w-full rounded-xl bg-orange-500 px-5 py-3 font-semibold text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? "Saving Expense..." : "Add Expense"}
        </button>
      </form>
    </section>
  );
}

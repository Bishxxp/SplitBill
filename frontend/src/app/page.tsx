"use client";

import GroupOverview from "@/components/GroupOverview";
import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const USERS = ["alice", "bob", "carol", "dan"];

type Group = {
  id: number;
  name: string;
};

type GroupDetail = Group & {
  members: string[];
};

type GroupResult = {
  user: string;
  groups: GroupDetail[];
  error: string | null;
};

export default function HomePage() {
  // 1. React State
  const [user, setUser] = useState("alice");
  const [result, setResult] = useState<GroupResult | null>(null);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);

  // 2. Fetch groups whenever the user changes
  useEffect(() => {
    const controller = new AbortController();

    async function loadGroups() {
      try {
        const response = await fetch(`${API_URL}/groups`, {
          headers: {
            "X-User": user,
          },
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Failed to load groups (${response.status})`);
        }

        const groupList: Group[] = await response.json();

        // Fetch details and members of each group
        const groupDetails = await Promise.all(
          groupList.map(async (group) => {
            const detailResponse = await fetch(
              `${API_URL}/groups/${group.id}`,
              {
                headers: {
                  "X-User": user,
                },
                signal: controller.signal,
              },
            );

            if (!detailResponse.ok) {
              throw new Error("Failed to load group details");
            }

            return (await detailResponse.json()) as GroupDetail;
          }),
        );

        if (!controller.signal.aborted) {
          setResult({
            user,
            groups: groupDetails,
            error: null,
          });
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setResult({
            user,
            groups: [],
            error:
              error instanceof Error ? error.message : "Something went wrong",
          });
        }
      }
    }

    void loadGroups();

    return () => controller.abort();
  }, [user]);

  const loading = result?.user !== user;
  const groups = result?.user === user ? result.groups : [];
  const error = result?.user === user ? result.error : null;

  const selectedGroup =
    groups.find((group) => group.id === selectedGroupId) ?? null;

  return (
    <div className="min-h-screen bg-[#f7f8fc] text-slate-900">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-500 text-xl font-bold text-white">
              S
            </div>

            <span className="text-xl font-bold">
              Split<span className="text-orange-500">Bill</span>
            </span>
          </div>

          <span className="rounded-full bg-orange-50 px-4 py-2 text-sm font-medium text-orange-700">
            Demo Mode
          </span>
        </div>
      </header>

      {/* Dashboard */}
      <main className="mx-auto max-w-6xl px-6 py-10">
        {/* Page Header */}
        <section className="mb-10 flex flex-wrap items-center justify-between gap-5">
          <div>
            <p className="text-sm font-medium text-orange-600">
              EXPENSE MANAGEMENT
            </p>

            <h1 className="mt-2 text-3xl font-bold">My Dashboard</h1>

            <p className="mt-2 text-slate-500">
              Keep track of shared expenses with your friends.
            </p>
          </div>

          {/* User Selection */}
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <label
              htmlFor="current-user"
              className="mb-2 block text-xs text-slate-500"
            >
              Current User
            </label>

            <select
              id="current-user"
              value={user}
              onChange={(event) => {
                setUser(event.target.value);
                setResult(null);
                setSelectedGroupId(null);
              }}
              className="w-44 rounded-lg border border-slate-200 bg-white px-3 py-2 font-medium capitalize outline-none focus:border-orange-500"
            >
              {USERS.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>
        </section>

        {/* Summary Cards */}
        <section className="mb-10 grid gap-5 sm:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm text-slate-500">Total Groups</p>

            <p className="mt-3 text-3xl font-bold">
              {loading ? "..." : groups.length}
            </p>
          </div>

          <div className="rounded-2xl bg-orange-500 p-6 text-white shadow-sm">
            <p className="text-sm text-orange-100">Current User</p>

            <p className="mt-3 text-2xl font-bold capitalize">{user}</p>
          </div>
        </section>

        {/* Groups */}
        <section>
          <h2 className="text-xl font-bold">Your Groups</h2>

          <p className="mt-1 text-sm text-slate-500">
            Select a group to manage shared expenses.
          </p>

          {/* Loading State */}
          {loading && <p className="mt-6 text-slate-500">Loading groups...</p>}

          {/* Error State */}
          {error && (
            <div
              role="alert"
              className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-red-700"
            >
              {error}. Please check your backend connection.
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && groups.length === 0 && (
            <p className="mt-6 text-slate-500">No groups available.</p>
          )}

          {/* Group Cards */}
          <div className="mt-6 grid gap-5 md:grid-cols-2">
            {groups.map((group) => (
              <button
                key={group.id}
                type="button"
                onClick={() => setSelectedGroupId(group.id)}
                className={`rounded-2xl border bg-white p-6 text-left shadow-sm transition hover:shadow-md ${
                  selectedGroupId === group.id
                    ? "border-orange-500 ring-2 ring-orange-100"
                    : "border-slate-200"
                }`}
              >
                <div className="mb-5 flex items-center justify-between">
                  <span className="text-2xl">
                    {group.id === 1 ? "✈️" : "🍽️"}
                  </span>

                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
                    {group.members.length} members
                  </span>
                </div>

                <h3 className="text-lg font-semibold">{group.name}</h3>

                <p className="mt-2 text-sm text-slate-500">
                  {group.members.join(", ")}
                </p>

                <div className="mt-5 border-t border-slate-100 pt-4 text-sm font-medium text-orange-600">
                  {selectedGroupId === group.id ? "Selected" : "Select group"}
                </div>
              </button>
            ))}
          </div>
        </section>
        {/* Selected Group Overview */}
        {selectedGroup && (
          <GroupOverview
            key={`${user}-${selectedGroup.id}`}
            group={selectedGroup}
            user={user}
          />
        )}
      </main>
    </div>
  );
}

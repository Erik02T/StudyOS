"use client";

import { useEffect, useMemo, useState } from "react";
import { UserRoundPlus } from "lucide-react";
import SectionCard from "../../../components/ui/SectionCard";
import SkeletonBlock from "../../../components/ui/SkeletonBlock";
import ToastStack from "../../../components/ui/ToastStack";
import { useStudyOS } from "../../../components/providers/StudyOSProvider";
import { MEMBER_ROLES, PAGE_SIZE_OPTIONS } from "../../../lib/constants";
import { useNotify } from "../../../lib/use-notify";

function roleBadge(role) {
  if (role === "owner") return "border-warning/50 bg-warning/15 text-warning";
  if (role === "admin") return "border-secondary/50 bg-secondary/15 text-secondary";
  return "border-white/15 bg-white/5 text-slate-200";
}

export default function SettingsPage() {
  const { email, activeOrgId, organizations, refreshOrganizations, apiRequest, logout } = useStudyOS();
  const { items: toasts, push } = useNotify();

  const activeOrganization = useMemo(
    () => organizations.find((org) => org.id === activeOrgId) || organizations[0] || null,
    [organizations, activeOrgId]
  );
  const activeRole = activeOrganization?.role || "member";
  const canManageMembers = activeRole === "owner" || activeRole === "admin";

  const [members, setMembers] = useState([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [memberRoleDrafts, setMemberRoleDrafts] = useState({});
  const [rowLoading, setRowLoading] = useState({});
  const [memberSearch, setMemberSearch] = useState("");
  const [memberRoleFilter, setMemberRoleFilter] = useState("all");
  const [memberSortBy, setMemberSortBy] = useState("created_at");
  const [memberSortDir, setMemberSortDir] = useState("desc");
  const [memberPage, setMemberPage] = useState(1);
  const [memberPageSize, setMemberPageSize] = useState(10);
  const [memberTotal, setMemberTotal] = useState(0);
  const [memberPages, setMemberPages] = useState(1);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviteLoading, setInviteLoading] = useState(false);
  const [removeModalMember, setRemoveModalMember] = useState(null);
  const [error, setError] = useState("");

  const [subscription, setSubscription] = useState(null);
  const [billingLoading, setBillingLoading] = useState(false);
  const [billingError, setBillingError] = useState("");
  const [planUpdating, setPlanUpdating] = useState(false);

  const [verificationToken, setVerificationToken] = useState("");
  const [passwordResetEmail, setPasswordResetEmail] = useState(email || "");

  useEffect(() => {
    setPasswordResetEmail(email || "");
  }, [email]);

  useEffect(() => {
    setMemberPage(1);
  }, [memberSearch, memberRoleFilter, memberSortBy, memberSortDir, memberPageSize, activeOrgId]);

  async function refreshMembers() {
    if (!activeOrgId) return;
    setMembersLoading(true);
    try {
      setError("");
      const params = new URLSearchParams();
      params.set("page", String(memberPage));
      params.set("page_size", String(memberPageSize));
      params.set("sort_by", memberSortBy);
      params.set("sort_dir", memberSortDir);
      if (memberSearch.trim()) params.set("search", memberSearch.trim());
      if (memberRoleFilter !== "all") params.set("role", memberRoleFilter);

      const payload = await apiRequest({
        path: `/organizations/${activeOrgId}/members?${params.toString()}`,
      });
      setMembers(payload.items || []);
      setMemberTotal(payload.total || 0);
      setMemberPages(payload.pages || 1);
      setMemberRoleDrafts((prev) => {
        const next = {};
        (payload.items || []).forEach((member) => {
          next[member.user_id] = prev[member.user_id] || member.role;
        });
        return next;
      });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setMembersLoading(false);
    }
  }

  async function refreshSubscription() {
    if (!activeOrgId) return;
    setBillingLoading(true);
    try {
      setBillingError("");
      const payload = await apiRequest({ path: "/billing/subscription" });
      setSubscription(payload);
    } catch (requestError) {
      setBillingError(requestError.message);
      setSubscription(null);
    } finally {
      setBillingLoading(false);
    }
  }

  useEffect(() => {
    if (!activeOrgId) return;
    refreshMembers();
  }, [activeOrgId, memberPage, memberPageSize, memberSearch, memberRoleFilter, memberSortBy, memberSortDir]);

  useEffect(() => {
    if (!activeOrgId) return;
    refreshSubscription();
  }, [activeOrgId]);

  async function inviteMember(event) {
    event.preventDefault();
    if (!activeOrgId) return;
    setInviteLoading(true);
    try {
      setError("");
      await apiRequest({
        method: "POST",
        path: `/organizations/${activeOrgId}/members/invite`,
        body: { email: inviteEmail, role: inviteRole },
      });
      setInviteEmail("");
      setInviteRole("member");
      push("ok", "Member invited.");
      await Promise.all([refreshMembers(), refreshOrganizations()]);
    } catch (requestError) {
      setError(requestError.message);
      push("error", requestError.message);
    } finally {
      setInviteLoading(false);
    }
  }

  async function saveRole(member) {
    const nextRole = memberRoleDrafts[member.user_id] || member.role;
    if (nextRole === member.role) return;
    setRowLoading((prev) => ({ ...prev, [member.user_id]: "role" }));
    try {
      setError("");
      await apiRequest({
        method: "PATCH",
        path: `/organizations/${activeOrgId}/members/${member.user_id}/role`,
        body: { role: nextRole },
      });
      push("ok", `${member.email} role updated to ${nextRole}.`);
      await Promise.all([refreshMembers(), refreshOrganizations()]);
    } catch (requestError) {
      setError(requestError.message);
      push("error", requestError.message);
    } finally {
      setRowLoading((prev) => ({ ...prev, [member.user_id]: "" }));
    }
  }

  async function removeMember(member) {
    setRowLoading((prev) => ({ ...prev, [member.user_id]: "remove" }));
    try {
      setError("");
      await apiRequest({
        method: "DELETE",
        path: `/organizations/${activeOrgId}/members/${member.user_id}`,
      });
      push("ok", `${member.email} removed.`);
      setRemoveModalMember(null);
      await Promise.all([refreshMembers(), refreshOrganizations()]);
    } catch (requestError) {
      setError(requestError.message);
      push("error", requestError.message);
    } finally {
      setRowLoading((prev) => ({ ...prev, [member.user_id]: "" }));
    }
  }

  async function updatePlan(plan) {
    setPlanUpdating(true);
    try {
      setBillingError("");
      await apiRequest({
        method: "PATCH",
        path: "/billing/subscription",
        body: { plan },
      });
      push("ok", `Plan switched to ${plan}.`);
      await refreshSubscription();
    } catch (requestError) {
      setBillingError(requestError.message);
      push("error", requestError.message);
    } finally {
      setPlanUpdating(false);
    }
  }

  async function requestEmailVerification() {
    try {
      const payload = await apiRequest({ method: "POST", path: "/auth/request-email-verification" });
      if (payload.action_token) setVerificationToken(payload.action_token);
      push("ok", payload.message || "Verification email requested.");
    } catch (requestError) {
      push("error", requestError.message);
    }
  }

  async function confirmEmailVerification() {
    if (!verificationToken.trim()) return;
    try {
      await apiRequest({
        method: "POST",
        path: "/auth/verify-email",
        body: { token: verificationToken.trim() },
      });
      push("ok", "Email verified.");
      setVerificationToken("");
    } catch (requestError) {
      push("error", requestError.message);
    }
  }

  async function requestPasswordReset(event) {
    event.preventDefault();
    try {
      const payload = await apiRequest({
        method: "POST",
        path: "/auth/request-password-reset",
        body: { email: passwordResetEmail },
      });
      push("ok", payload.message || "Password reset requested.");
      if (payload.action_token) setVerificationToken(payload.action_token);
    } catch (requestError) {
      push("error", requestError.message);
    }
  }

  return (
    <div className="grid gap-4">
      {error ? <p className="rounded-xl border border-danger/45 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p> : null}

      <section className="grid gap-4 xl:grid-cols-2">
        <SectionCard title="Account" description="Identity, verification and session controls.">
          <div className="grid gap-3">
            <div className="rounded-xl border border-white/10 bg-white/5 p-3">
              <p className="text-xs text-slate-400">Signed in as</p>
              <p className="font-medium">{email || "Unknown user"}</p>
              <p className="mt-1 text-xs text-slate-400">
                Active organization: {activeOrganization?.name || "--"} ({activeRole})
              </p>
            </div>

            <div className="grid gap-2 sm:grid-cols-2">
              <button
                type="button"
                onClick={requestEmailVerification}
                className="rounded-xl border border-secondary/45 bg-secondary/15 px-3 py-2 text-sm text-secondary"
              >
                Request email verification
              </button>
              <button
                type="button"
                onClick={logout}
                className="rounded-xl border border-danger/45 bg-danger/15 px-3 py-2 text-sm text-danger"
              >
                Logout
              </button>
            </div>

            <div className="grid gap-2 rounded-xl border border-white/10 bg-white/5 p-3">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Action Token</p>
              <input
                value={verificationToken}
                onChange={(event) => setVerificationToken(event.target.value)}
                placeholder="Paste token to verify email"
                className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
              />
              <button
                type="button"
                onClick={confirmEmailVerification}
                className="rounded-xl border border-primary/45 bg-primary/20 px-3 py-2 text-sm text-primary"
              >
                Verify email with token
              </button>
            </div>

            <form onSubmit={requestPasswordReset} className="grid gap-2 rounded-xl border border-white/10 bg-white/5 p-3">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Password Reset</p>
              <input
                type="email"
                value={passwordResetEmail}
                onChange={(event) => setPasswordResetEmail(event.target.value)}
                placeholder="email for reset"
                className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
              />
              <button type="submit" className="rounded-xl border border-primary/45 bg-primary/20 px-3 py-2 text-sm text-primary">
                Request password reset
              </button>
            </form>
          </div>
        </SectionCard>

        <SectionCard title="Billing" description="Plan limits and subscription status.">
          {billingError ? <p className="mb-3 rounded-xl border border-danger/45 bg-danger/10 px-3 py-2 text-sm text-danger">{billingError}</p> : null}
          {billingLoading ? (
            <div className="grid gap-2">
              <SkeletonBlock className="h-14" />
              <SkeletonBlock className="h-24" />
            </div>
          ) : !subscription ? (
            <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-400">
              Subscription data unavailable for current role.
            </p>
          ) : (
            <div className="grid gap-3">
              <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                <p className="text-xs text-slate-400">Current plan</p>
                <p className="text-xl font-semibold">{subscription.plan}</p>
                <p className="text-xs text-slate-400">
                  Status: {subscription.status} · Period {subscription.current_period_start} → {subscription.current_period_end}
                </p>
              </div>
              <div className="grid gap-2">
                {(subscription.usage || []).map((item) => (
                  <div key={item.metric} className="rounded-xl border border-white/10 bg-white/5 p-3">
                    <div className="flex items-center justify-between text-xs">
                      <span>{item.metric}</span>
                      <span>
                        {item.used}/{item.limit}
                      </span>
                    </div>
                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-secondary to-primary"
                        style={{ width: `${Math.min((item.used / Math.max(item.limit, 1)) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <button
                  type="button"
                  disabled={planUpdating}
                  onClick={() => updatePlan("free")}
                  className="rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm text-slate-200 disabled:opacity-60"
                >
                  Switch to Free
                </button>
                <button
                  type="button"
                  disabled={planUpdating}
                  onClick={() => updatePlan("pro")}
                  className="rounded-xl border border-primary/45 bg-primary/20 px-3 py-2 text-sm text-primary disabled:opacity-60"
                >
                  Switch to Pro
                </button>
              </div>
            </div>
          )}
        </SectionCard>
      </section>

      <SectionCard
        title="Organization Administration"
        description="Invite, promote, demote and remove members with contextual confirmation."
      >
        {!canManageMembers ? (
          <p className="rounded-xl border border-warning/40 bg-warning/10 p-3 text-sm text-warning">
            Only owner/admin can manage organization members.
          </p>
        ) : (
          <form
            data-testid="invite-form"
            onSubmit={inviteMember}
            className="mb-4 grid gap-2 rounded-xl border border-white/10 bg-white/5 p-3 lg:grid-cols-[2fr_1fr_auto]"
          >
            <input
              type="email"
              value={inviteEmail}
              onChange={(event) => setInviteEmail(event.target.value)}
              placeholder="member@email.com"
              className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
              required
            />
            <select
              value={inviteRole}
              onChange={(event) => setInviteRole(event.target.value)}
              className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
            >
              {MEMBER_ROLES.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={inviteLoading}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-primary/45 bg-primary/20 px-4 py-2 text-sm text-primary disabled:opacity-60"
            >
              <UserRoundPlus size={15} />
              {inviteLoading ? "Inviting..." : "Invite"}
            </button>
          </form>
        )}

        <div className="mb-4 grid gap-2 lg:grid-cols-5">
          <input
            value={memberSearch}
            onChange={(event) => setMemberSearch(event.target.value)}
            placeholder="search email, role, user_id"
            className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100 lg:col-span-2"
          />
          <select
            value={memberRoleFilter}
            onChange={(event) => setMemberRoleFilter(event.target.value)}
            className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
          >
            <option value="all">all roles</option>
            {MEMBER_ROLES.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
          <select
            value={memberSortBy}
            onChange={(event) => setMemberSortBy(event.target.value)}
            className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
          >
            <option value="created_at">sort: created_at</option>
            <option value="email">sort: email</option>
            <option value="role">sort: role</option>
          </select>
          <select
            value={memberSortDir}
            onChange={(event) => setMemberSortDir(event.target.value)}
            className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100"
          >
            <option value="desc">desc</option>
            <option value="asc">asc</option>
          </select>
        </div>

        {membersLoading ? (
          <div className="grid gap-2">
            {Array.from({ length: 6 }).map((_, idx) => (
              <div key={idx} className="rounded-xl border border-white/10 bg-white/5 p-3">
                <SkeletonBlock className="h-4 w-1/3" />
                <SkeletonBlock className="mt-2 h-3 w-2/3" />
              </div>
            ))}
          </div>
        ) : !members.length ? (
          <p className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-400">No members found.</p>
        ) : (
          <div className="grid gap-2">
            {members.map((member) => {
              const rowState = rowLoading[member.user_id] || "";
              const canEdit = canManageMembers && member.email !== email && !rowState;
              const currentDraftRole = memberRoleDrafts[member.user_id] || member.role;
              return (
                <div
                  key={member.user_id}
                  data-testid={`member-row-${member.user_id}`}
                  className="grid gap-3 rounded-xl border border-white/10 bg-white/5 p-3 lg:grid-cols-[1fr_auto]"
                >
                  <div>
                    <p className="font-medium">{member.email}</p>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                      <span>user_id {member.user_id}</span>
                      <span className={`rounded-full border px-2 py-0.5 ${roleBadge(member.role)}`}>{member.role}</span>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <select
                      data-testid={`member-role-select-${member.user_id}`}
                      value={currentDraftRole}
                      disabled={!canEdit}
                      onChange={(event) =>
                        setMemberRoleDrafts((prev) => ({ ...prev, [member.user_id]: event.target.value }))
                      }
                      className="rounded-xl border border-white/15 bg-background px-3 py-2 text-sm text-slate-100 disabled:opacity-60"
                    >
                      {MEMBER_ROLES.map((role) => (
                        <option key={role} value={role}>
                          {role}
                        </option>
                      ))}
                    </select>
                    <button
                      data-testid={`member-save-role-${member.user_id}`}
                      type="button"
                      disabled={!canEdit}
                      onClick={() => saveRole(member)}
                      className="rounded-xl border border-secondary/45 bg-secondary/15 px-3 py-2 text-xs text-secondary disabled:opacity-60"
                    >
                      {rowState === "role" ? "Saving..." : "Save role"}
                    </button>
                    <button
                      data-testid={`member-remove-${member.user_id}`}
                      type="button"
                      disabled={!canEdit}
                      onClick={() => setRemoveModalMember(member)}
                      className="rounded-xl border border-danger/45 bg-danger/15 px-3 py-2 text-xs text-danger disabled:opacity-60"
                    >
                      {rowState === "remove" ? "Removing..." : "Remove"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <span>Total {memberTotal}</span>
          <select
            value={memberPageSize}
            onChange={(event) => setMemberPageSize(Number(event.target.value) || 10)}
            className="rounded-lg border border-white/15 bg-background px-2 py-1"
          >
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size}/page
              </option>
            ))}
          </select>
          <button
            type="button"
            disabled={memberPage <= 1}
            onClick={() => setMemberPage((prev) => Math.max(1, prev - 1))}
            className="rounded-lg border border-white/15 bg-white/5 px-3 py-1 disabled:opacity-60"
          >
            Prev
          </button>
          <span>
            Page {memberPage} / {memberPages}
          </span>
          <button
            type="button"
            disabled={memberPage >= memberPages}
            onClick={() => setMemberPage((prev) => Math.min(memberPages, prev + 1))}
            className="rounded-lg border border-white/15 bg-white/5 px-3 py-1 disabled:opacity-60"
          >
            Next
          </button>
        </div>
      </SectionCard>

      {removeModalMember ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/65 p-4">
          <div className="glass w-full max-w-lg rounded-2xl p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-danger">Confirm Removal</p>
            <h3 className="mt-1 text-xl font-semibold">Remove member from organization?</h3>
            <p className="mt-2 text-sm text-slate-300">
              You are removing <strong>{removeModalMember.email}</strong> from{" "}
              <strong>{activeOrganization?.name || "current organization"}</strong>.
            </p>
            <p className="mt-2 rounded-xl border border-warning/35 bg-warning/10 p-2 text-xs text-warning">
              Impact: this user loses immediate access to dashboard, planner, reviews and analytics for this workspace.
            </p>
            <div className="mt-4 flex flex-wrap justify-end gap-2">
              <button
                type="button"
                onClick={() => setRemoveModalMember(null)}
                className="rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm"
              >
                Cancel
              </button>
              <button
                data-testid="confirm-remove-member"
                type="button"
                onClick={() => removeMember(removeModalMember)}
                className="rounded-xl border border-danger/45 bg-danger/15 px-3 py-2 text-sm text-danger"
              >
                Confirm removal
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <ToastStack items={toasts} />
    </div>
  );
}

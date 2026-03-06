import React, { useEffect, useMemo, useState } from "react";
import { apiRequest } from "./api";

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function getPasswordStrength(password) {
  if (!password) return { score: 0, label: "Vazia" };
  let score = 0;
  if (password.length >= 8) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  if (score <= 2) return { score, label: "Fraca" };
  if (score <= 4) return { score, label: "Media" };
  return { score, label: "Forte" };
}

function getAuthFieldErrors({ authMode, email, password, confirmPassword }) {
  const errors = {};
  if (!email.trim()) errors.email = "Digite seu e-mail.";
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = "Formato de e-mail invalido.";

  if (!password) errors.password = "Digite sua senha.";
  else if (password.length < 6) errors.password = "A senha precisa ter pelo menos 6 caracteres.";

  if (authMode === "register") {
    if (!confirmPassword) errors.confirmPassword = "Confirme sua senha.";
    else if (password !== confirmPassword) errors.confirmPassword = "As senhas nao coincidem.";
  }
  return errors;
}

function TrendChart({ points }) {
  const size = { w: 640, h: 220, p: 20 };
  if (!points.length) return <div className="empty">Sem dados de trend.</div>;
  const stepX = (size.w - size.p * 2) / Math.max(points.length - 1, 1);
  const toY = (v) => size.h - size.p - (v / 100) * (size.h - size.p * 2);
  const line = points
    .map((point, idx) => `${size.p + idx * stepX},${toY(point.productivity_index)}`)
    .join(" ");

  return (
    <svg viewBox={`0 0 ${size.w} ${size.h}`} className="trend-svg" role="img" aria-label="Trend chart">
      <rect x="0" y="0" width={size.w} height={size.h} fill="transparent" />
      <polyline fill="none" stroke="#0B8A6A" strokeWidth="3" points={line} />
      {points.map((point, idx) => (
        <circle key={point.date} cx={size.p + idx * stepX} cy={toY(point.productivity_index)} r="4" fill="#F26A2E" />
      ))}
    </svg>
  );
}

function Heatmap({ items }) {
  return (
    <div className="heatmap">
      {items.map((item) => {
        const intensity = clamp(item.avg_productivity_index / 100, 0, 1);
        const bg = `rgba(11, 138, 106, ${0.15 + intensity * 0.75})`;
        return (
          <div className="heatmap-cell" key={item.bucket} style={{ background: bg }}>
            <strong>{item.bucket}</strong>
            <span>{item.sessions} sessoes</span>
            <span>{item.avg_productivity_index}% prod.</span>
          </div>
        );
      })}
    </div>
  );
}

const MEMBER_ROLES = ["member", "admin", "owner"];
const PAGE_SIZE_OPTIONS = [5, 10, 20];

export default function App() {
  const [apiBase, setApiBase] = useState(localStorage.getItem("studyos_api_base") || "http://127.0.0.1:8010");
  const [token, setToken] = useState(localStorage.getItem("studyos_token") || "");
  const [email, setEmail] = useState(localStorage.getItem("studyos_email") || "");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [authMode, setAuthMode] = useState("login");
  const [authAttempted, setAuthAttempted] = useState(false);
  const [touched, setTouched] = useState({ email: false, password: false, confirmPassword: false });
  const [activeView, setActiveView] = useState("dashboard");

  const [days, setDays] = useState(30);
  const [dashboard, setDashboard] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [reviewQuality, setReviewQuality] = useState({});
  const [error, setError] = useState("");
  const [toasts, setToasts] = useState([]);

  const [organizations, setOrganizations] = useState([]);
  const [selectedOrgId, setSelectedOrgId] = useState(Number(localStorage.getItem("studyos_org_id")) || null);
  const [members, setMembers] = useState([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [inviteLoading, setInviteLoading] = useState(false);
  const [rowLoading, setRowLoading] = useState({});

  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [memberRoleDrafts, setMemberRoleDrafts] = useState({});
  const [memberSearch, setMemberSearch] = useState("");
  const [memberRoleFilter, setMemberRoleFilter] = useState("all");
  const [memberSortBy, setMemberSortBy] = useState("created_at");
  const [memberSortDir, setMemberSortDir] = useState("desc");
  const [memberPage, setMemberPage] = useState(1);
  const [memberPageSize, setMemberPageSize] = useState(10);
  const [memberTotal, setMemberTotal] = useState(0);
  const [totalMemberPages, setTotalMemberPages] = useState(1);
  const [removeModalMember, setRemoveModalMember] = useState(null);

  const [sessionForm, setSessionForm] = useState({
    completed_tasks: 1,
    study_minutes: 60,
    focus_score: 75,
    time_block: "19:00-21:00",
  });

  const authReady = useMemo(() => Boolean(apiBase && token), [apiBase, token]);
  const authErrors = useMemo(
    () => getAuthFieldErrors({ authMode, email, password, confirmPassword }),
    [authMode, email, password, confirmPassword]
  );
  const passwordStrength = useMemo(() => getPasswordStrength(password), [password]);
  const isAuthValid = useMemo(() => Object.keys(authErrors).length === 0, [authErrors]);
  const showFieldError = (fieldName) => authErrors[fieldName] && (authAttempted || touched[fieldName]);

  const activeOrganization = useMemo(
    () => organizations.find((org) => org.id === selectedOrgId) || organizations[0] || null,
    [organizations, selectedOrgId]
  );
  const activeOrgId = activeOrganization?.id ?? null;
  const activeOrgRole = activeOrganization?.role ?? "member";
  const canManageMembers = activeOrgRole === "owner" || activeOrgRole === "admin";

  useEffect(() => {
    if (memberPage > totalMemberPages) setMemberPage(totalMemberPages);
  }, [memberPage, totalMemberPages]);

  useEffect(() => localStorage.setItem("studyos_api_base", apiBase), [apiBase]);
  useEffect(() => localStorage.setItem("studyos_token", token), [token]);
  useEffect(() => localStorage.setItem("studyos_email", email), [email]);
  useEffect(() => {
    if (activeOrgId) localStorage.setItem("studyos_org_id", String(activeOrgId));
  }, [activeOrgId]);

  function pushToast(type, text) {
    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    setToasts((prev) => [...prev, { id, type, text }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, 3500);
  }

  async function refreshOrganizations(overrideToken) {
    const data = await apiRequest({
      baseUrl: apiBase,
      token: overrideToken || token,
      path: "/organizations/",
    });
    setOrganizations(data);
    return data;
  }

  async function refreshDashboard(orgId, overrideToken) {
    if (!orgId) {
      setDashboard(null);
      return;
    }
    const data = await apiRequest({
      baseUrl: apiBase,
      token: overrideToken || token,
      organizationId: orgId,
      path: `/analytics/dashboard?days=${days}`,
    });
    setDashboard(data);
  }

  async function refreshDueReviews(orgId, overrideToken) {
    if (!orgId) {
      setReviews([]);
      return;
    }
    const data = await apiRequest({
      baseUrl: apiBase,
      token: overrideToken || token,
      organizationId: orgId,
      path: "/reviews/due",
    });
    setReviews(data);
  }

  async function refreshMembers(orgId, overrideToken, showLoader = true) {
    if (!orgId) {
      setMembers([]);
      setMemberTotal(0);
      setTotalMemberPages(1);
      return;
    }
    if (showLoader) setMembersLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(memberPage));
      params.set("page_size", String(memberPageSize));
      params.set("sort_by", memberSortBy);
      params.set("sort_dir", memberSortDir);
      if (memberSearch.trim()) params.set("search", memberSearch.trim());
      if (memberRoleFilter !== "all") params.set("role", memberRoleFilter);
      const data = await apiRequest({
        baseUrl: apiBase,
        token: overrideToken || token,
        organizationId: orgId,
        path: `/organizations/${orgId}/members?${params.toString()}`,
      });
      setMembers(data.items || []);
      setMemberTotal(data.total || 0);
      setTotalMemberPages(data.pages || 1);
      setMemberRoleDrafts((prev) => {
        const next = {};
        (data.items || []).forEach((member) => {
          next[member.user_id] = prev[member.user_id] || member.role;
        });
        return next;
      });
    } finally {
      if (showLoader) setMembersLoading(false);
    }
  }

  async function refreshAll(overrideToken) {
    setError("");
    const orgs = await refreshOrganizations(overrideToken);
    const targetOrg = orgs.find((org) => org.id === selectedOrgId) || orgs[0] || null;
    const targetOrgId = targetOrg?.id ?? null;
    if (targetOrgId && targetOrgId !== selectedOrgId) {
      setSelectedOrgId(targetOrgId);
    }
    await Promise.all([
      refreshDashboard(targetOrgId, overrideToken),
      refreshDueReviews(targetOrgId, overrideToken),
      refreshMembers(targetOrgId, overrideToken, true),
    ]);
  }

  useEffect(() => {
    if (!authReady) return;
    refreshAll().catch((requestError) => setError(requestError.message));
  }, [authReady, days]);

  useEffect(() => {
    if (!authReady || !activeOrgId) return;
    Promise.all([refreshDashboard(activeOrgId), refreshDueReviews(activeOrgId), refreshMembers(activeOrgId, undefined, true)]).catch(
      (requestError) => setError(requestError.message)
    );
  }, [selectedOrgId]);

  useEffect(() => {
    setMemberPage(1);
  }, [memberSearch, memberRoleFilter, memberSortBy, memberSortDir, memberPageSize, selectedOrgId]);

  useEffect(() => {
    if (!authReady || !activeOrgId) return;
    refreshMembers(activeOrgId, undefined, true).catch((requestError) => setError(requestError.message));
  }, [memberPage, memberPageSize, memberSearch, memberRoleFilter, memberSortBy, memberSortDir]);

  async function handleAuth(event) {
    event.preventDefault();
    setAuthAttempted(true);
    if (!isAuthValid) {
      setError("Revise os campos do formulario de autenticacao.");
      return;
    }
    try {
      setError("");
      const path = authMode === "register" ? "/auth/register" : "/auth/login";
      const response = await apiRequest({
        baseUrl: apiBase,
        method: "POST",
        path,
        body: { email, password },
      });
      setToken(response.access_token);
      setPassword("");
      setConfirmPassword("");
      setAuthAttempted(false);
      setTouched({ email: false, password: false, confirmPassword: false });
      await refreshAll(response.access_token);
      pushToast("ok", authMode === "register" ? "Conta criada e login concluido." : "Login realizado com sucesso.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  function logout() {
    setToken("");
    setOrganizations([]);
    setSelectedOrgId(null);
    setMembers([]);
    setDashboard(null);
    setReviews([]);
    pushToast("ok", "Sessao encerrada.");
  }

  async function submitReview(review) {
    const quality = Number(reviewQuality[review.task_id] ?? 4);
    try {
      setError("");
      await apiRequest({
        baseUrl: apiBase,
        token,
        organizationId: activeOrgId,
        method: "POST",
        path: "/reviews/answer",
        body: { task_id: review.task_id, quality },
      });
      await apiRequest({
        baseUrl: apiBase,
        token,
        organizationId: activeOrgId,
        method: "POST",
        path: "/sessions/finalize",
        body: { source: "review", study_minutes: review.estimated_time, quality, time_block: sessionForm.time_block },
      });
      pushToast("ok", `Revisao da task ${review.task_id} concluida.`);
      await Promise.all([refreshDashboard(activeOrgId), refreshDueReviews(activeOrgId)]);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function submitSession(event) {
    event.preventDefault();
    try {
      setError("");
      await apiRequest({
        baseUrl: apiBase,
        token,
        organizationId: activeOrgId,
        method: "POST",
        path: "/sessions/finalize",
        body: { source: "manual", ...sessionForm },
      });
      pushToast("ok", "Sessao finalizada e performance atualizada.");
      await refreshDashboard(activeOrgId);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function inviteMember(event) {
    event.preventDefault();
    if (!activeOrgId) return;
    try {
      setError("");
      setInviteLoading(true);
      await apiRequest({
        baseUrl: apiBase,
        token,
        organizationId: activeOrgId,
        method: "POST",
        path: `/organizations/${activeOrgId}/members/invite`,
        body: { email: inviteEmail, role: inviteRole },
      });
      setInviteEmail("");
      setInviteRole("member");
      pushToast("ok", "Membro convidado com sucesso.");
      await refreshMembers(activeOrgId, undefined, false);
    } catch (requestError) {
      setError(requestError.message);
      pushToast("error", requestError.message);
    } finally {
      setInviteLoading(false);
    }
  }

  async function updateMemberRole(member) {
    if (!activeOrgId) return;
    const nextRole = memberRoleDrafts[member.user_id] || member.role;
    if (nextRole === member.role) return;
    try {
      setError("");
      setRowLoading((prev) => ({ ...prev, [member.user_id]: "role" }));
      await apiRequest({
        baseUrl: apiBase,
        token,
        organizationId: activeOrgId,
        method: "PATCH",
        path: `/organizations/${activeOrgId}/members/${member.user_id}/role`,
        body: { role: nextRole },
      });
      pushToast("ok", `Papel de ${member.email} atualizado para ${nextRole}.`);
      await Promise.all([refreshMembers(activeOrgId, undefined, false), refreshOrganizations()]);
    } catch (requestError) {
      setError(requestError.message);
      pushToast("error", requestError.message);
    } finally {
      setRowLoading((prev) => ({ ...prev, [member.user_id]: "" }));
    }
  }

  function openRemoveModal(member) {
    setRemoveModalMember(member);
  }

  function closeRemoveModal() {
    setRemoveModalMember(null);
  }

  async function confirmRemoveMember() {
    if (!activeOrgId || !removeModalMember) return;
    const member = removeModalMember;
    try {
      setError("");
      setRowLoading((prev) => ({ ...prev, [member.user_id]: "remove" }));
      await apiRequest({
        baseUrl: apiBase,
        token,
        organizationId: activeOrgId,
        method: "DELETE",
        path: `/organizations/${activeOrgId}/members/${member.user_id}`,
      });
      pushToast("ok", `${member.email} removido da organizacao.`);
      await refreshMembers(activeOrgId, undefined, false);
      closeRemoveModal();
    } catch (requestError) {
      setError(requestError.message);
      pushToast("error", requestError.message);
    } finally {
      setRowLoading((prev) => ({ ...prev, [member.user_id]: "" }));
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <h1>StudyOS Dashboard</h1>
        <p>Motor adaptativo de aprendizado com visao real de evolucao.</p>
      </header>

      <section className="panel controls">
        <label>
          API Base
          <input value={apiBase} onChange={(e) => setApiBase(e.target.value)} placeholder="http://127.0.0.1:8010" />
        </label>
        <form className="inline-form" onSubmit={handleAuth}>
          <div className="auth-mode">
            <button
              type="button"
              className={authMode === "login" ? "auth-pill active" : "auth-pill"}
              onClick={() => {
                setAuthMode("login");
                setAuthAttempted(false);
                setConfirmPassword("");
                setTouched((prev) => ({ ...prev, confirmPassword: false }));
              }}
            >
              Entrar
            </button>
            <button
              type="button"
              className={authMode === "register" ? "auth-pill active" : "auth-pill"}
              onClick={() => {
                setAuthMode("register");
                setAuthAttempted(false);
              }}
            >
              Criar conta
            </button>
          </div>
          <label>
            Email
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onBlur={() => setTouched((prev) => ({ ...prev, email: true }))}
              placeholder="seu@email.com"
            />
            {showFieldError("email") ? <small className="field-error">{authErrors.email}</small> : null}
          </label>
          <label>
            Senha
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
              placeholder="sua senha"
            />
            {showFieldError("password") ? <small className="field-error">{authErrors.password}</small> : null}
            {authMode === "register" ? (
              <small className="field-hint">
                Forca da senha: <strong>{passwordStrength.label}</strong>
              </small>
            ) : null}
          </label>
          {authMode === "register" ? (
            <label>
              Confirmar senha
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                onBlur={() => setTouched((prev) => ({ ...prev, confirmPassword: true }))}
                placeholder="repita sua senha"
              />
              {showFieldError("confirmPassword") ? (
                <small className="field-error">{authErrors.confirmPassword}</small>
              ) : null}
            </label>
          ) : null}
          <button type="submit" disabled={!isAuthValid}>
            {authMode === "register" ? "Registrar" : "Login"}
          </button>
        </form>
        <label>
          Janela (dias)
          <input type="number" min="7" max="365" value={days} onChange={(e) => setDays(Number(e.target.value))} />
        </label>
        <div className="action-stack">
          <button disabled={!authReady} onClick={() => refreshAll()}>
            Atualizar Painel
          </button>
          <button type="button" className="ghost" disabled={!authReady} onClick={logout}>
            Logout
          </button>
        </div>
      </section>

      <section className="panel controls org-controls">
        <label>
          Organizacao
          <select value={activeOrgId || ""} onChange={(e) => setSelectedOrgId(Number(e.target.value) || null)}>
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name} ({org.role})
              </option>
            ))}
          </select>
        </label>
        <div className="org-meta">
          <strong>Role atual:</strong> {activeOrgRole}
        </div>
      </section>

      <section className="panel view-tabs">
        <button
          type="button"
          className={activeView === "dashboard" ? "auth-pill active" : "auth-pill"}
          onClick={() => setActiveView("dashboard")}
        >
          Dashboard
        </button>
        <button
          type="button"
          className={activeView === "admin" ? "auth-pill active" : "auth-pill"}
          onClick={() => setActiveView("admin")}
        >
          Administracao
        </button>
      </section>

      {error ? <div className="alert error">{error}</div> : null}

      {activeView === "dashboard" ? (
        <section className="grid">
          <article className="panel">
            <h2>Evolucao</h2>
            <div className="kpi">
              <span>Evolution Score</span>
              <strong>{dashboard?.progress?.evolution_score ?? "--"}</strong>
            </div>
            <div className="kpi">
              <span>Consistencia</span>
              <strong>{dashboard?.consistency?.consistency_rate ?? "--"}%</strong>
            </div>
            <div className="kpi">
              <span>Streak atual</span>
              <strong>{dashboard?.consistency?.current_streak ?? "--"} dias</strong>
            </div>
          </article>

          <article className="panel wide">
            <h2>Trend de Produtividade</h2>
            <TrendChart points={dashboard?.trend ?? []} />
          </article>

          <article className="panel wide">
            <h2>Heatmap por Horario</h2>
            <Heatmap items={dashboard?.heatmap?.heatmap ?? []} />
          </article>

          <article className="panel">
            <h2>Finalizar Sessao</h2>
            <form className="stack" onSubmit={submitSession}>
              <label>
                Tasks concluidas
                <input
                  type="number"
                  min="0"
                  value={sessionForm.completed_tasks}
                  onChange={(e) => setSessionForm({ ...sessionForm, completed_tasks: Number(e.target.value) })}
                />
              </label>
              <label>
                Minutos estudados
                <input
                  type="number"
                  min="0"
                  value={sessionForm.study_minutes}
                  onChange={(e) => setSessionForm({ ...sessionForm, study_minutes: Number(e.target.value) })}
                />
              </label>
              <label>
                Focus score
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={sessionForm.focus_score}
                  onChange={(e) => setSessionForm({ ...sessionForm, focus_score: Number(e.target.value) })}
                />
              </label>
              <label>
                Time block
                <input
                  value={sessionForm.time_block}
                  onChange={(e) => setSessionForm({ ...sessionForm, time_block: e.target.value })}
                />
              </label>
              <button type="submit" disabled={!authReady || !activeOrgId}>
                Finalizar Sessao
              </button>
            </form>
          </article>

          <article className="panel wide">
            <h2>Revisoes Pendentes</h2>
            {!reviews.length ? <div className="empty">Sem revisoes pendentes.</div> : null}
            <div className="review-list">
              {reviews.map((review) => (
                <div className="review-item" key={review.task_id}>
                  <div>
                    <strong>{review.title}</strong>
                    <p>
                      {review.subject} | {review.category} | {review.estimated_time} min
                    </p>
                  </div>
                  <div className="review-actions">
                    <select
                      value={reviewQuality[review.task_id] ?? 4}
                      onChange={(e) => setReviewQuality({ ...reviewQuality, [review.task_id]: Number(e.target.value) })}
                    >
                      <option value="0">0</option>
                      <option value="1">1</option>
                      <option value="2">2</option>
                      <option value="3">3</option>
                      <option value="4">4</option>
                      <option value="5">5</option>
                    </select>
                    <button disabled={!authReady || !activeOrgId} onClick={() => submitReview(review)}>
                      Finalizar Revisao
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </article>
        </section>
      ) : (
        <section className="grid">
          <article className="panel wide admin-panel">
            <h2>Administracao da Organizacao</h2>
            {!canManageMembers ? (
              <p className="empty">Somente owner/admin podem gerenciar membros.</p>
            ) : (
              <form className="members-invite" onSubmit={inviteMember}>
                <label>
                  Email do usuario
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="usuario@dominio.com"
                    required
                  />
                </label>
                <label>
                  Papel
                  <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}>
                    {MEMBER_ROLES.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                </label>
                <button type="submit" disabled={!authReady || !activeOrgId || inviteLoading}>
                  {inviteLoading ? "Convidando..." : "Convidar"}
                </button>
              </form>
            )}

            <div className="admin-filters">
              <label>
                Buscar
                <input
                  value={memberSearch}
                  onChange={(e) => setMemberSearch(e.target.value)}
                  placeholder="email, role ou user_id"
                />
              </label>
              <label>
                Filtrar role
                <select value={memberRoleFilter} onChange={(e) => setMemberRoleFilter(e.target.value)}>
                  <option value="all">todos</option>
                  {MEMBER_ROLES.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Ordenar por
                <select value={memberSortBy} onChange={(e) => setMemberSortBy(e.target.value)}>
                  <option value="created_at">created_at</option>
                  <option value="email">email</option>
                  <option value="role">role</option>
                </select>
              </label>
              <label>
                Direcao
                <select value={memberSortDir} onChange={(e) => setMemberSortDir(e.target.value)}>
                  <option value="desc">desc</option>
                  <option value="asc">asc</option>
                </select>
              </label>
              <label>
                Itens por pagina
                <select value={memberPageSize} onChange={(e) => setMemberPageSize(Number(e.target.value))}>
                  {PAGE_SIZE_OPTIONS.map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {membersLoading ? (
              <div className="members-list">
                {[...Array(5)].map((_, idx) => (
                  <div className="member-item skeleton" key={idx}>
                    <div className="skeleton-line short" />
                    <div className="skeleton-line" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="members-list">
                {!members.length ? <div className="empty">Nenhum membro encontrado.</div> : null}
                {members.map((member) => {
                  const currentRowAction = rowLoading[member.user_id] || "";
                  const canEdit = canManageMembers && member.email !== email && !currentRowAction;
                  return (
                    <div className="member-item" key={member.user_id}>
                      <div>
                        <strong>{member.email}</strong>
                        <p>
                          user_id: {member.user_id} | role atual: {member.role}
                        </p>
                      </div>
                      <div className="member-actions">
                        <select
                          value={memberRoleDrafts[member.user_id] || member.role}
                          disabled={!canEdit}
                          onChange={(e) =>
                            setMemberRoleDrafts((prev) => ({
                              ...prev,
                              [member.user_id]: e.target.value,
                            }))
                          }
                        >
                          {MEMBER_ROLES.map((role) => (
                            <option key={role} value={role}>
                              {role}
                            </option>
                          ))}
                        </select>
                        <button type="button" className="ghost" disabled={!canEdit} onClick={() => updateMemberRole(member)}>
                          {currentRowAction === "role" ? "Salvando..." : "Salvar papel"}
                        </button>
                        <button type="button" className="danger" disabled={!canEdit} onClick={() => openRemoveModal(member)}>
                          {currentRowAction === "remove" ? "Removendo..." : "Remover"}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="pagination">
              <span className="muted-total">Total: {memberTotal}</span>
              <button
                type="button"
                className="ghost"
                disabled={memberPage <= 1}
                onClick={() => setMemberPage((prev) => Math.max(1, prev - 1))}
              >
                Anterior
              </button>
              <span>
                Pagina {memberPage} de {totalMemberPages}
              </span>
              <button
                type="button"
                className="ghost"
                disabled={memberPage >= totalMemberPages}
                onClick={() => setMemberPage((prev) => Math.min(totalMemberPages, prev + 1))}
              >
                Proxima
              </button>
            </div>
          </article>
        </section>
      )}

      {removeModalMember ? (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Confirmar remocao de membro">
          <div className="modal-card">
            <h3>Confirmar remocao de membro</h3>
            <p>
              Voce esta removendo <strong>{removeModalMember.email}</strong> da organizacao{" "}
              <strong>{activeOrganization?.name || "atual"}</strong>.
            </p>
            <p className="impact">
              Impacto: a pessoa perdera acesso imediato ao dashboard, tarefas, revisoes e analytics desta organizacao.
            </p>
            <div className="modal-actions">
              <button type="button" className="ghost" onClick={closeRemoveModal}>
                Cancelar
              </button>
              <button
                type="button"
                className="danger"
                onClick={confirmRemoveMember}
                disabled={rowLoading[removeModalMember.user_id] === "remove"}
              >
                {rowLoading[removeModalMember.user_id] === "remove" ? "Removendo..." : "Confirmar remocao"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <div className="toast-stack">
        {toasts.map((toast) => (
          <div key={toast.id} className={toast.type === "ok" ? "toast ok" : "toast error"}>
            {toast.text}
          </div>
        ))}
      </div>
    </div>
  );
}

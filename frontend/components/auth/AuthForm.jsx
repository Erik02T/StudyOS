"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useStudyOS } from "../providers/StudyOSProvider";
import { getAuthFieldErrors, getPasswordStrength } from "../../lib/formatters";

export default function AuthForm({ mode }) {
  const router = useRouter();
  const { loading, login, register } = useStudyOS();
  const [nextPath, setNextPath] = useState("/dashboard");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [touched, setTouched] = useState({ email: false, password: false, confirmPassword: false });
  const [error, setError] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const value = new URLSearchParams(window.location.search).get("next");
    if (value) setNextPath(value);
  }, []);

  const errors = useMemo(
    () => getAuthFieldErrors({ mode, email, password, confirmPassword }),
    [mode, email, password, confirmPassword]
  );
  const passwordStrength = useMemo(() => getPasswordStrength(password), [password]);
  const isValid = Object.keys(errors).length === 0;

  function showError(field) {
    return errors[field] && (submitted || touched[field]);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitted(true);
    if (!isValid) return;

    try {
      setError("");
      if (mode === "register") {
        await register({ userEmail: email, password });
      } else {
        await login({ userEmail: email, password });
      }
      router.replace(nextPath || "/dashboard");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="glass w-full rounded-3xl p-6 lg:p-7">
      <h1 className="text-2xl font-semibold">{mode === "register" ? "Create account" : "Login"}</h1>
      <p className="mt-1 text-sm text-slate-400">
        {mode === "register"
          ? "Set up your StudyOS workspace in under a minute."
          : "Access your dashboard, planner and adaptive learning engine."}
      </p>

      <div className="mt-5 grid gap-4">
        <label className="grid gap-1 text-sm">
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            onBlur={() => setTouched((prev) => ({ ...prev, email: true }))}
            placeholder="you@email.com"
            className="rounded-xl border border-white/15 bg-card px-3 py-2"
          />
          {showError("email") ? <span className="text-xs text-danger">{errors.email}</span> : null}
        </label>

        <label className="grid gap-1 text-sm">
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
            placeholder="Your password"
            className="rounded-xl border border-white/15 bg-card px-3 py-2"
          />
          {showError("password") ? <span className="text-xs text-danger">{errors.password}</span> : null}
          {mode === "register" ? (
            <span className={`text-xs ${passwordStrength.color}`}>Password strength: {passwordStrength.label}</span>
          ) : null}
        </label>

        {mode === "register" ? (
          <label className="grid gap-1 text-sm">
            Confirm password
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              onBlur={() => setTouched((prev) => ({ ...prev, confirmPassword: true }))}
              placeholder="Repeat password"
              className="rounded-xl border border-white/15 bg-card px-3 py-2"
            />
            {showError("confirmPassword") ? (
              <span className="text-xs text-danger">{errors.confirmPassword}</span>
            ) : null}
          </label>
        ) : null}
      </div>

      {error ? <p className="mt-4 rounded-xl border border-danger/45 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</p> : null}

      <button
        type="submit"
        disabled={loading || !isValid}
        className="mt-5 w-full rounded-xl border border-primary/50 bg-primary px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-70"
      >
        {loading ? "Loading..." : mode === "register" ? "Create account" : "Login"}
      </button>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
        {mode === "register" ? (
          <p>
            Already have an account?{" "}
            <Link href="/auth/login" className="text-secondary">
              Login
            </Link>
          </p>
        ) : (
          <p>
            New here?{" "}
            <Link href="/auth/register" className="text-secondary">
              Create account
            </Link>
          </p>
        )}
        <p className="text-xs text-slate-500">Google/GitHub login coming soon.</p>
      </div>
    </form>
  );
}

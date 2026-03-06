export function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

export function toPercent(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `${Number(value).toFixed(digits)}%`;
}

export function toFixed(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return Number(value).toFixed(digits);
}

export function capitalize(text) {
  if (!text) return "";
  return `${text.charAt(0).toUpperCase()}${text.slice(1)}`;
}

export function getPasswordStrength(password) {
  if (!password) return { score: 0, label: "Empty", color: "text-slate-400" };

  let score = 0;
  if (password.length >= 8) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;

  if (score <= 2) return { score, label: "Weak", color: "text-danger" };
  if (score <= 4) return { score, label: "Medium", color: "text-warning" };
  return { score, label: "Strong", color: "text-success" };
}

export function getAuthFieldErrors({ mode, email, password, confirmPassword }) {
  const errors = {};
  if (!email.trim()) errors.email = "Enter your email.";
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = "Invalid email format.";

  if (!password) errors.password = "Enter your password.";
  else if (password.length < 6) errors.password = "Password needs at least 6 characters.";

  if (mode === "register") {
    if (!confirmPassword) errors.confirmPassword = "Confirm your password.";
    else if (password !== confirmPassword) errors.confirmPassword = "Passwords do not match.";
  }
  return errors;
}

export const ADMIN_PASSWORD_STORAGE_KEY = "ai-profile-admin-password";

export function getStoredAdminPassword() {
  return sessionStorage.getItem(ADMIN_PASSWORD_STORAGE_KEY) || "";
}

export function setStoredAdminPassword(password) {
  sessionStorage.setItem(ADMIN_PASSWORD_STORAGE_KEY, password);
}

export function clearStoredAdminPassword() {
  sessionStorage.removeItem(ADMIN_PASSWORD_STORAGE_KEY);
}

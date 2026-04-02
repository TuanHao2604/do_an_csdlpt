/**
 * API helper cho NovaBank B
 * Kết nối tới Bank B backend (port 5002) qua Vite proxy
 */

const BANK_API = '/api';
const COORDINATOR_API = '/coordinator';

// --- Auth ---
export async function loginAPI(username: string, password: string) {
  const res = await fetch(`${BANK_API}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
    credentials: 'include',
  });
  return res.json();
}

export async function logoutAPI() {
  const res = await fetch(`${BANK_API}/logout`, {
    method: 'POST',
    credentials: 'include',
  });
  return res.json();
}

// --- Account ---
export async function getBalance(accountNumber: string) {
  const res = await fetch(`${BANK_API}/accounts/${accountNumber}/balance`, {
    credentials: 'include',
  });
  return res.json();
}

export async function getAccountInfo(accountNumber: string) {
  const res = await fetch(`${BANK_API}/accounts/${accountNumber}/info`, {
    credentials: 'include',
  });
  return res.json();
}

export async function listAccounts() {
  const res = await fetch(`${BANK_API}/accounts`, {
    credentials: 'include',
  });
  return res.json();
}

// --- Transactions ---
export async function getTransactions(accountNumber: string) {
  const res = await fetch(`${BANK_API}/transactions/${accountNumber}`, {
    credentials: 'include',
  });
  return res.json();
}

// --- Transfer ---
export async function internalTransfer(fromAccount: string, toAccount: string, amount: number) {
  const res = await fetch(`${BANK_API}/internal/transfer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from_account: fromAccount,
      to_account: toAccount,
      amount,
    }),
    credentials: 'include',
  });
  return res.json();
}

export async function crossBankTransfer(fromAccount: string, toAccount: string, amount: number) {
  const res = await fetch(`${COORDINATOR_API}/transfer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from_account: fromAccount,
      to_account: toAccount,
      amount,
    }),
    credentials: 'include',
  });
  const data = await res.json();
  return { ...data, httpStatus: res.status };
}

// --- Coordinator ---
export async function getTransferStatus(txnId: string) {
  const res = await fetch(`${COORDINATOR_API}/status/${txnId}`);
  return res.json();
}

export async function setCrashSimulation(enabled: boolean, crashPoint: string = 'after_prepare', delaySeconds: number = 15) {
  const res = await fetch(`${COORDINATOR_API}/simulate-crash`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      enabled,
      crash_point: crashPoint,
      delay_seconds: delaySeconds,
    }),
  });
  return res.json();
}

export async function getCrashConfig() {
  const res = await fetch(`${COORDINATOR_API}/simulate-crash`);
  return res.json();
}

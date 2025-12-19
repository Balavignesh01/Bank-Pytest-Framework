import React, { useState, useEffect } from 'react'

// async function runBackendTests(actionLabel) {
//   try {
//     const res = await fetch("http://127.0.0.1:5001/api/run-tests", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ action: actionLabel }),
//     })

//     const data = await res.json()
//     return data.success === true
//   } catch (err) {
//     console.warn("Test backend not reachable:", err)
//     return false
//   }
// }

const STORAGE_KEY = 'bcf_accounts_v1'
const SESSION_KEY = 'bcf_session_v1'
function loadAccounts() {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveAccounts(accounts) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(accounts))
}

function loadSession() {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(SESSION_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveSession(session) {
  if (typeof window === 'undefined') return
  if (!session) {
    window.localStorage.removeItem(SESSION_KEY)
  } else {
    window.localStorage.setItem(SESSION_KEY, JSON.stringify(session))
  }
}

function generateAccountId(existingIds) {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  let id = ''
  for (let i = 0; i < 6; i++) {
    id += chars[Math.floor(Math.random() * chars.length)]
  }
  if (existingIds && existingIds.includes(id)) {
    return generateAccountId(existingIds)
  }
  return id
}

function ensureAdmin(accounts) {
  if (accounts.some(a => a.isAdmin)) {
    return accounts
  }
  const admin = {
    accountId: 'ADMIN1',
    username: 'admin',
    password: 'admin123',
    balance: 0,
    isAdmin: true,
    history: [],
  }
  return [admin, ...accounts]
}

function formatCurrency(amount) {
  const value = Number(amount || 0)
  return '₹ ' + value.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatDateTime(ts) {
  try {
    return new Date(ts).toLocaleString('en-IN')
  } catch {
    return ''
  }
}

function App() {
  const [testPopup, setTestPopup] = useState({
    open: false,
    phase: 'running',
    message: '',
  })

  const [accounts, setAccounts] = useState(() => ensureAdmin(loadAccounts()))
  const [currentUser, setCurrentUser] = useState(() => loadSession())
  const [view, setView] = useState('login')
  const [toast, setToast] = useState(null)
  const [showSwitchModal, setShowSwitchModal] = useState(false)

  useEffect(() => {
    setAccounts(prev => ensureAdmin(prev))
  }, [])

  useEffect(() => {
    saveAccounts(accounts)
  }, [accounts])

  useEffect(() => {
    saveSession(currentUser)
  }, [currentUser])

  function showToast(kind, message) {
    setToast({ kind, message })
    setTimeout(() => setToast(null), 2600)
  }
  async function runBackendTests(actionLabel) {
    setTestPopup({
      open: true,
      phase: 'running',
      message: 'Running backend tests…',
    })

    try {
      const res = await fetch("http://127.0.0.1:5001/api/run-tests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: actionLabel }),
      })

      const data = await res.json()

      if (data.success) {
        setTestPopup({
          open: true,
          phase: 'success',
          message: 'Backend validation successful',
        })


        setTimeout(() => {
          setTestPopup(prev => ({ ...prev, open: false }))
        }, 900)

        return true
      }

      setTestPopup({
        open: true,
        phase: 'error',
        message: 'Backend tests failed. Action blocked.',
      })


      setTimeout(() => {
        setTestPopup(prev => ({ ...prev, open: false }))
      }, 1200)

      return false
    } catch (err) {
      setTestPopup({
        open: true,
        phase: 'error',
        message: 'Test server not reachable',
      })

      setTimeout(() => {
        setTestPopup(prev => ({ ...prev, open: false }))
      }, 1200)

      return false
    }
  }



  async function handleCreateAccount({
    username,
    password,
    initialBalance,
    onIdGenerated,
  }) {
    // 1️⃣ Run backend tests FIRST
    const testsOk = await runBackendTests('create-account')
    if (!testsOk) {
      showToast('error', 'Account creation blocked: backend validation failed')
      return null
    }

    // 2️⃣ Client-side validation
    const trimmedUser = username.trim()
    if (!trimmedUser || !password) {
      showToast('error', 'Username and password are required')
      return null
    }

    const startingBalance = Number(initialBalance || 0)
    if (Number.isNaN(startingBalance) || startingBalance < 0) {
      showToast('error', 'Initial balance must be zero or positive')
      return null
    }

    // 3️⃣ Create account ONLY after tests pass
    const ids = accounts.map(a => a.accountId)
    const accountId = generateAccountId(ids)

    const account = {
      accountId,
      username: trimmedUser,
      password,
      balance: startingBalance,
      isAdmin: false,
      history: [],
    }

    setAccounts(prev => [...prev, account])

    showToast('success', `Account created. ID: ${accountId}`)

    if (onIdGenerated) {
      onIdGenerated(accountId)
    }

    return accountId
  }

  async function handleLogin({ accountId, password }) {
    const id = accountId.trim()
    const acc = accounts.find(
      a => a.accountId === id && a.password === password
    )

    // 1️⃣ Local validation FIRST
    if (!acc) {
      showToast('error', 'Invalid account ID or password')
      return
    }

    // 2️⃣ Run backend tests AFTER validation
    const testsOk = await runBackendTests('login')
    if (!testsOk) {
      showToast('error', 'Login blocked: backend validation failed')
      return
    }

    // 3️⃣ Apply login
    setCurrentUser(acc)
    setView('dashboard')
    showToast('success', `Welcome back, ${acc.username}`)
  }



  function handleLogout() {
    setCurrentUser(null)
    setView('login')
    showToast('info', 'You have been logged out')
  }

  async function handleTransfer({ toAccountId, amount }) {
    if (!currentUser) return

    // 1️⃣ Block admin transfers early
    if (currentUser.isAdmin) {
      showToast('error', 'Admin account cannot transfer funds')
      return
    }

    // 2️⃣ Run backend tests FIRST
    const testsOk = await runBackendTests('transfer-funds')
    if (!testsOk) {
      showToast('error', 'Transfer blocked: backend validation failed')
      return
    }

    // 3️⃣ Client-side validation
    const trimmedTo = toAccountId.trim()
    const numeric = Number(amount)

    if (!trimmedTo || Number.isNaN(numeric) || numeric <= 0) {
      showToast('error', 'Enter a positive amount and destination ID')
      return
    }

    const from = accounts.find(a => a.accountId === currentUser.accountId)
    const to = accounts.find(a => a.accountId === trimmedTo)

    if (!from) {
      showToast('error', 'Source account not found in local data')
      return
    }
    if (!to) {
      showToast('error', 'Destination account not found')
      return
    }
    if (from.accountId === to.accountId) {
      showToast('error', 'Cannot transfer to the same account')
      return
    }
    if (from.balance < numeric) {
      showToast('error', 'Insufficient funds')
      return
    }

    // 4️⃣ Apply state changes ONLY after tests pass
    const ts = Date.now()
    const updated = accounts.map(a => {
      if (a.accountId === from.accountId) {
        const history = a.history || []
        return {
          ...a,
          balance: (a.balance || 0) - numeric,
          history: [
            ...history,
            { type: 'debit', to: to.accountId, amount: numeric, ts },
          ],
        }
      }
      if (a.accountId === to.accountId) {
        const history = a.history || []
        return {
          ...a,
          balance: (a.balance || 0) + numeric,
          history: [
            ...history,
            { type: 'credit', from: from.accountId, amount: numeric, ts },
          ],
        }
      }
      return a
    })

    setAccounts(updated)

    const newFrom = updated.find(a => a.accountId === from.accountId)
    setCurrentUser(newFrom)

    showToast(
      'success',
      `Transferred ${formatCurrency(numeric)} to ${to.accountId}`,
    )
  }

  function handleAdminPasswordChange(targetId, newPassword) {
    const trimmed = targetId.trim()
    const pwd = newPassword.trim()
    if (!trimmed || !pwd) {
      showToast('error', 'Target account and new password are required')
      return
    }
    const exists = accounts.some(a => a.accountId === trimmed)
    if (!exists) {
      showToast('error', 'Account not found')
      return
    }

    const updated = accounts.map(a =>
      a.accountId === trimmed ? { ...a, password: pwd } : a,
    )
    setAccounts(updated)
    if (currentUser && currentUser.accountId === trimmed) {
      setCurrentUser(updated.find(a => a.accountId === trimmed))
    }
    showToast('success', 'Password updated')
  }

  async function handleAdminAddFunds(targetId, amount) {
    const testsOk = await runBackendTests('admin-add-funds')
    if (!testsOk) {
      showToast('error', 'Admin action blocked: backend validation failed')
      return
    }
    const trimmed = targetId.trim()
    const numeric = Number(amount)
    if (!trimmed || Number.isNaN(numeric) || numeric <= 0) {
      showToast('error', 'Enter a positive amount and target Account ID')
      return
    }
    const existing = accounts.find(
      a => a.accountId === trimmed && !a.isAdmin
    )
    if (!existing) {
      showToast('error', 'Customer account not found')
      return
    }
    const ts = Date.now()
    const updated = accounts.map(a => {
      if (a.accountId === trimmed) {
        const history = a.history || []
        return {
          ...a,
          balance: (a.balance || 0) + numeric,
          history: [
            ...history,
            { type: 'credit-admin', from: 'ADMIN', amount: numeric, ts },
          ],
        }
      }
      return a
    })
    setAccounts(updated)
    if (currentUser && currentUser.accountId === trimmed) {
      setCurrentUser(updated.find(a => a.accountId === trimmed))
    }
    showToast('success', `Added ${formatCurrency(numeric)} to ${trimmed}`)
  }
  function openSwitchModal() {
    if (accounts.length > 1) {
      setShowSwitchModal(true)
    }
  }
  function handleSwitchAccount(accountId) {
    const acc = accounts.find(a => a.accountId === accountId)
    if (!acc) return
    setCurrentUser(acc)
    setView('dashboard')
    setShowSwitchModal(false)
    showToast('success', `Switched to ${acc.username}`)
  }

  const canSwitch = accounts.length > 1

  return (
    <div className="app-shell">
      <Sidebar
        view={view}
        setView={setView}
        currentUser={currentUser}
        onLogout={handleLogout}
      />
      <main className="main">
        <Header />
        <AccountSnapshot
          currentUser={currentUser}
          canSwitch={canSwitch}
          onOpenSwitch={openSwitchModal}
        />
        <ContentArea
          view={view}
          setView={setView}
          currentUser={currentUser}
          accounts={accounts}
          onCreateAccount={handleCreateAccount}
          onLogin={handleLogin}
          onTransfer={handleTransfer}
          onAdminPasswordChange={handleAdminPasswordChange}
          onAdminAddFunds={handleAdminAddFunds}
          showToast={showToast}
        />
        {toast && <Toast kind={toast.kind} message={toast.message} />}
        {showSwitchModal && (
          <AccountSwitchModal
            accounts={accounts}
            currentUser={currentUser}
            onClose={() => setShowSwitchModal(false)}
            onSwitch={handleSwitchAccount}
          />
        )}
        <TestPopup
          open={testPopup.open}
          phase={testPopup.phase}
          message={testPopup.message}
          onClose={() =>
            setTestPopup(prev => ({ ...prev, open: false }))
          }
        />

      </main>
    </div>
  )
}
function TestPopup({ open, phase, message }) {
  if (!open) return null

  const icon =
    phase === 'running'
      ? '⏳'
      : phase === 'success'
        ? '✅'
        : '❌'

  return (
    <div className="modal-backdrop">
      <div
        className="modal-panel"
        style={{
          maxWidth: 360,
          textAlign: 'center',
          pointerEvents: 'none', // 🔒 no interaction
        }}
      >
        <div className="modal-title">
          {icon} Backend Validation
        </div>
        <div style={{ marginTop: 14, fontSize: 14 }}>
          {message}
        </div>
      </div>
    </div>
  )
}


function Sidebar({ view, setView, currentUser, onLogout }) {
  const loggedIn = !!currentUser
  const isAdmin = currentUser?.isAdmin

  function NavItem({ id, icon, title, subtitle, disabled }) {
    const active = view === id
    const classes = [
      'nav-item',
      active ? 'active' : '',
      disabled ? 'disabled' : '',
    ]
      .filter(Boolean)
      .join(' ')

    function handleClick() {
      if (disabled) return
      if (id === 'logout') {
        onLogout()
      } else {
        setView(id)
      }
    }

    return (
      <li className={classes} onClick={handleClick}>
        <div className="nav-item-icon">{icon}</div>
        <div>
          <div className="nav-item-label-main">{title}</div>
          {subtitle && <div className="nav-item-label-sub">{subtitle}</div>}
        </div>
      </li>
    )
  }
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-circle">M</div>
        <div>
          <div className="sidebar-title-main">MIT Bank</div>
          <div className="sidebar-title-sub">Secure · Simple · Local</div>
        </div>
      </div>
      <div className="sidebar-tagline">
        Use Account ID and password seamlessly across all flows.
      </div>
      <nav>
        <div className="sidebar-section-label">Session</div>
        <ul className="nav-list">
          <NavItem
            id="login"
            icon="⌂"
            title={loggedIn ? 'Switch / Login' : 'Login'}
            subtitle="Use Account ID + Password"
            disabled={false}
          />
          <NavItem
            id="create"
            icon="✚"
            title="Create Account"
            subtitle="Generate 6-char ID"
            disabled={false}
          />
        </ul>

        <div className="sidebar-section-label">Banking</div>
        <ul className="nav-list">
          <NavItem
            id="dashboard"
            icon="ⓘ"
            title="Account Details"
            subtitle="Snapshot of your account"
            disabled={!loggedIn}
          />
          <NavItem
            id="transfer"
            icon="⇄"
            title="Transfer Funds"
            subtitle="Send to another ID"
            disabled={!loggedIn || isAdmin}
          />
          <NavItem
            id="admin"
            icon="⚙"
            title="Admin"
            subtitle="View & edit accounts"
            disabled={!isAdmin}
          />
        </ul>

        <div className="sidebar-section-label">System</div>
        <ul className="nav-list">
          <NavItem
            id="logout"
            icon="⏻"
            title="Logout"
            subtitle="Clear active session"
            disabled={!loggedIn}
          />
        </ul>
      </nav>

      <div className="sidebar-footer">
        {currentUser ? (
          <div>
            Logged in as <strong>{currentUser.username}</strong>
          </div>
        ) : (
          <div>Not signed in.</div>
        )}
      </div>
    </aside>
  )
}

function Header() {
  return (
    <header className="main-header">
      <div>
        <div className="main-title">Welcome to MIT Bank</div>
        <div className="main-subtitle">
          A simple glassmorphic UI where a single Account ID and password drive login,
          account view, transfers, and admin actions.
        </div>
      </div>
    </header>
  )
}

function AccountSnapshot({ currentUser, canSwitch, onOpenSwitch }) {
  const loggedIn = !!currentUser
  const isAdmin = currentUser?.isAdmin
  return (
    <div className="snapshot">
      <span className="snapshot-label">Account snapshot:</span>
      {loggedIn ? (
        <>
          <span>{currentUser.username}</span>
          <span className="snapshot-id">{currentUser.accountId}</span>
          {isAdmin ? (
            <span className="snapshot-pill">Admin account · No balance</span>
          ) : (
            <span className="snapshot-pill">
              Balance {formatCurrency(currentUser.balance)}
            </span>
          )}
          {canSwitch && (
            <button
              type="button"
              className="button ghost"
              style={{ padding: '4px 10px', fontSize: 11, marginLeft: 8 }}
              onClick={onOpenSwitch}
            >
              Switch account
            </button>
          )}
        </>
      ) : (
        <span>Not logged in — create or login from the left menu.</span>
      )}
    </div>
  )
}

function ContentArea({
  view,
  setView,
  currentUser,
  accounts,
  onCreateAccount,
  onLogin,
  onTransfer,
  onAdminPasswordChange,
  onAdminAddFunds,
  showToast,
}) {
  let title = 'Login (Account ID)'
  let subtitle = 'Sign in using the Account ID and password you created earlier.'
  let body = (
    <LoginForm
      onLogin={onLogin}
      onSwitchToCreate={() => setView('create')}
    />
  )

  if (view === 'create') {
    title = 'Create Account'
    subtitle =
      'Register a new user. The system will generate a unique 6-character Account ID for login and transfers.'
    body = <CreateAccountForm onCreateAccount={onCreateAccount} showToast={showToast} />
  } else if (view === 'dashboard') {
    title = 'Account Details'
    subtitle =
      'View the basic details, current balance, and recent activity of the active account.'
    body = <DashboardView currentUser={currentUser} />
  } else if (view === 'transfer') {
    title = 'Transfer Funds'
    subtitle = 'Send money from the active account to another Account ID.'
    body = <TransferForm currentUser={currentUser} onTransfer={onTransfer} />
  } else if (view === 'admin') {
    title = 'Admin · Manage Accounts'
    subtitle =
      'As admin, you can inspect accounts created in this browser, view their history, update passwords, and add funds.'
    body = (
      <AdminView
        currentUser={currentUser}
        accounts={accounts}
        onAdminPasswordChange={onAdminPasswordChange}
        onAdminAddFunds={onAdminAddFunds}
      />
    )
  }

  return (
    <section className="content-card">
      <div className="content-card-title">{title}</div>
      <div className="content-card-subtitle">{subtitle}</div>
      {body}
    </section>
  )
}

function LoginForm({ onLogin, onSwitchToCreate }) {
  const [accountId, setAccountId] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    onLogin({ accountId, password })
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="form-row">
        <label className="label">Account ID</label>
        <input
          className="input"
          value={accountId}
          onChange={e => setAccountId(e.target.value)}
          placeholder="e.g. A2B9KX"
        />
      </div>
      <div className="form-row">
        <label className="label">Password</label>
        <input
          className="input"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="********"
        />
      </div>
      <div className="button-row">
        <button type="submit" className="button primary">
          Login
        </button>
        <button
          type="button"
          className="button ghost"
          onClick={onSwitchToCreate}
        >
          Create Account
        </button>
      </div>
      <div className="helper-text">
        Demo admin account: ID <strong>ADMIN1</strong>, password{' '}
        <strong>admin123</strong>.
      </div>
    </form>
  )
}

function CreateAccountForm({ onCreateAccount, showToast }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [initialBalance, setInitialBalance] = useState('')
  const [newId, setNewId] = useState('')

  useEffect(() => {
    if (!newId) return
    const timer = setTimeout(() => {
      setNewId('')
    }, 60_000)
    return () => clearTimeout(timer)
  }, [newId])

  function handleSubmit(e) {
    e.preventDefault()
    onCreateAccount({
      username,
      password,
      initialBalance,
      onIdGenerated: id => setNewId(id),
    })
    setUsername('')
    setPassword('')
    setInitialBalance('')
  }

  function handleCopy() {
    if (!newId || typeof navigator === 'undefined' || !navigator.clipboard) return
    navigator.clipboard.writeText(newId).then(
      () => {
        if (showToast) showToast('success', 'Account ID copied')
      },
      () => {
        if (showToast) showToast('error', 'Could not copy Account ID')
      },
    )
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="form-row">
        <label className="label">Username</label>
        <input
          className="input"
          value={username}
          onChange={e => setUsername(e.target.value)}
          placeholder="Customer name"
        />
      </div>
      <div className="form-row">
        <label className="label">Password</label>
        <input
          className="input"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="Set a login password"
        />
      </div>
      <div className="form-row">
        <label className="label">
          Initial balance <span style={{ opacity: 0.7 }}>(optional)</span>
        </label>
        <input
          className="input"
          value={initialBalance}
          onChange={e => setInitialBalance(e.target.value)}
          placeholder="0.00"
        />
      </div>
      <div className="button-row">
        <button type="submit" className="button primary">
          Create Account
        </button>
      </div>
      {newId && (
        <div className="helper-text">
          New account created:
          <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span
              style={{
                padding: '4px 10px',
                borderRadius: 999,
                border: '1px solid #e5e7eb',
                background: '#f9fafb',
                fontFamily:
                  'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                letterSpacing: '0.14em',
                textTransform: 'uppercase',
                fontSize: 11,
              }}
            >
              {newId}
            </span>
            <button
              type="button"
              className="button ghost"
              style={{ padding: '5px 12px', fontSize: 11 }}
              onClick={handleCopy}
            >
              Copy ID
            </button>
          </div>
          <div style={{ marginTop: 4, fontSize: 11, color: '#6b7280' }}>
            This ID will stay visible here for about a minute. Use it with the password
            above to login and to transfer funds.
          </div>
        </div>
      )}
    </form>
  )
}

function DashboardView({ currentUser }) {
  if (!currentUser) {
    return (
      <div className="helper-text">
        Login first to see account details. Use the left menu to sign in.
      </div>
    )
  }

  const isAdmin = currentUser.isAdmin
  const history = currentUser.history || []
  const recent = [...history].sort((a, b) => b.ts - a.ts).slice(0, 6)

  return (
    <div className="form">
      <div className="form-row">
        <label className="label">Account holder</label>
        <div>{currentUser.username}</div>
      </div>
      <div className="form-row">
        <label className="label">Account ID</label>
        <div style={{ letterSpacing: '0.14em', textTransform: 'uppercase' }}>
          {currentUser.accountId}
        </div>
      </div>
      {!isAdmin && (
        <div className="form-row">
          <label className="label">Current balance</label>
          <div style={{ fontSize: 18, fontWeight: 700 }}>
            {formatCurrency(currentUser.balance)}
          </div>
        </div>
      )}
      {isAdmin && (
        <div className="form-row">
          <label className="label">Admin account</label>
          <div>
            This account does not hold funds. Use the Admin view to add money to customer
            accounts.
          </div>
        </div>
      )}
      <div className="form-row" style={{ marginTop: 12 }}>
        <label className="label">Recent activity</label>
        {recent.length === 0 ? (
          <div className="helper-text">
            No transactions recorded yet for this account.
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>When</th>
                <th>Type</th>
                <th>Counterparty</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((tx, idx) => (
                <tr key={idx}>
                  <td>{formatDateTime(tx.ts)}</td>
                  <td>
                    {tx.type === 'debit'
                      ? 'Sent'
                      : tx.type === 'credit'
                        ? 'Received'
                        : 'Admin credit'}
                  </td>
                  <td>{tx.to || tx.from || '-'}</td>
                  <td>{formatCurrency(tx.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function TransferForm({ currentUser, onTransfer }) {
  const [toAccountId, setToAccountId] = useState('')
  const [amount, setAmount] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    onTransfer({ toAccountId, amount })
  }

  if (!currentUser) {
    return (
      <div className="helper-text">
        Login first to transfer funds. Use the left menu to sign in.
      </div>
    )
  }

  if (currentUser.isAdmin) {
    return (
      <div className="helper-text">
        Admin account cannot transfer funds. Use the Admin view to add money to customer
        accounts.
      </div>
    )
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="form-row">
        <label className="label">From account</label>
        <div>
          <strong>{currentUser.username}</strong>{' '}
          <span style={{ letterSpacing: '0.1em', textTransform: 'uppercase' }}>
            · {currentUser.accountId}
          </span>
        </div>
      </div>
      <div className="form-row">
        <label className="label">To Account ID</label>
        <input
          className="input"
          value={toAccountId}
          onChange={e => setToAccountId(e.target.value)}
          placeholder="Destination Account ID"
        />
      </div>
      <div className="form-row">
        <label className="label">Amount</label>
        <input
          className="input"
          value={amount}
          onChange={e => setAmount(e.target.value)}
          placeholder="Amount to transfer"
        />
      </div>
      <div className="button-row">
        <button type="submit" className="button primary">
          Transfer
        </button>
      </div>
      <div className="helper-text">
        This demo updates balances only in your browser storage and does not call
        any backend API.
      </div>
    </form>
  )
}

function AdminView({ currentUser, accounts, onAdminPasswordChange, onAdminAddFunds }) {
  const [editAccountId, setEditAccountId] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [fundAccountId, setFundAccountId] = useState('')
  const [fundAmount, setFundAmount] = useState('')
  const [selectedId, setSelectedId] = useState('')

  if (!currentUser || !currentUser.isAdmin) {
    return (
      <div className="helper-text">
        Only admin accounts can access this view. Login with ADMIN1 / admin123 in
        this demo.
      </div>
    )
  }

  function handlePasswordSubmit(e) {
    e.preventDefault()
    onAdminPasswordChange(editAccountId, newPassword)
    setNewPassword('')
  }

  function handleFundsSubmit(e) {
    e.preventDefault()
    onAdminAddFunds(fundAccountId, fundAmount)
    setFundAmount('')
  }

  const customerAccounts = accounts.filter(a => !a.isAdmin)
  const selected = accounts.find(a => a.accountId === selectedId)
  const history = selected?.history || []
  const recent = [...history].sort((a, b) => b.ts - a.ts).slice(0, 6)

  return (
    <div className="form">
      <div className="admin-subcard">
        <div className="form-row">
          <label className="label">Customer accounts in this browser</label>
          {customerAccounts.length === 0 ? (
            <div className="helper-text">No customer accounts created yet.</div>
          ) : (
            <div style={{ maxHeight: 200, overflow: 'auto' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>Balance</th>
                  </tr>
                </thead>
                <tbody>
                  {customerAccounts.map(acc => (
                    <tr
                      key={acc.accountId}
                      style={{
                        cursor: 'pointer',
                        backgroundColor:
                          selectedId === acc.accountId ? '#eef2ff' : 'transparent',
                      }}
                      onClick={() => setSelectedId(acc.accountId)}
                    >
                      <td
                        style={{
                          letterSpacing: '0.1em',
                          textTransform: 'uppercase',
                        }}
                      >
                        {acc.accountId}
                      </td>
                      <td>{acc.username}</td>
                      <td>{formatCurrency(acc.balance)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="admin-subcard">
        <div className="form-row">
          <label className="label">Update customer password</label>
        </div>
        <form className="form" onSubmit={handlePasswordSubmit}>
          <div className="form-row">
            <input
              className="input"
              value={editAccountId}
              onChange={e => setEditAccountId(e.target.value)}
              placeholder="Target Account ID"
            />
          </div>
          <div className="form-row">
            <input
              className="input"
              type="password"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              placeholder="New password"
            />
          </div>
          <div className="button-row">
            <button type="submit" className="button primary">
              Update Password
            </button>
          </div>
        </form>
      </div>

      <div className="admin-subcard">
        <div className="form-row">
          <label className="label">Add funds to account</label>
        </div>
        <form className="form" onSubmit={handleFundsSubmit}>
          <div className="form-row">
            <input
              className="input"
              value={fundAccountId}
              onChange={e => setFundAccountId(e.target.value)}
              placeholder="Target Account ID"
            />
          </div>
          <div className="form-row">
            <input
              className="input"
              value={fundAmount}
              onChange={e => setFundAmount(e.target.value)}
              placeholder="Amount to add"
            />
          </div>
          <div className="button-row">
            <button type="submit" className="button primary">
              Add Money
            </button>
          </div>
        </form>
      </div>

      <div className="admin-subcard">
        <div className="form-row">
          <label className="label">Selected account activity</label>
          {selected ? (
            <>
              <div style={{ fontSize: 13, marginBottom: 6 }}>
                {selected.username} ·{' '}
                <span
                  style={{
                    letterSpacing: '0.14em',
                    textTransform: 'uppercase',
                    fontSize: 11,
                  }}
                >
                  {selected.accountId}
                </span>
              </div>
              {recent.length === 0 ? (
                <div className="helper-text">
                  No transactions recorded yet for this account.
                </div>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>When</th>
                      <th>Type</th>
                      <th>Counterparty</th>
                      <th>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent.map((tx, idx) => (
                      <tr key={idx}>
                        <td>{formatDateTime(tx.ts)}</td>
                        <td>
                          {tx.type === 'debit'
                            ? 'Sent'
                            : tx.type === 'credit'
                              ? 'Received'
                              : 'Admin credit'}
                        </td>
                        <td>{tx.to || tx.from || '-'}</td>
                        <td>{formatCurrency(tx.amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          ) : (
            <div className="helper-text">
              Click a customer row above to inspect recent transactions.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function AccountSwitchModal({ accounts, currentUser, onClose, onSwitch }) {
  const handleBackdropClick = e => {
    if (e.target.classList.contains('modal-backdrop')) {
      onClose()
    }
  }

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-panel">
        <div className="modal-title">Switch account</div>
        <div className="modal-subtitle">
          Pick another account created in this browser and switch the active session.
        </div>
        <div className="modal-list">
          {accounts.map(acc => (
            <div key={acc.accountId} className="modal-list-item">
              <div>
                <div>
                  {acc.username}
                  {acc.isAdmin ? ' (admin)' : ''}
                </div>
                <div className="modal-account-id">{acc.accountId}</div>
              </div>
              <button
                type="button"
                className="button ghost"
                style={{ padding: '5px 10px', fontSize: 11 }}
                disabled={currentUser && currentUser.accountId === acc.accountId}
                onClick={() => onSwitch(acc.accountId)}
              >
                {currentUser && currentUser.accountId === acc.accountId
                  ? 'Active'
                  : 'Switch'}
              </button>
            </div>
          ))}
        </div>
        <div className="modal-footer">
          <button
            type="button"
            className="button primary"
            style={{ padding: '6px 16px', fontSize: 12 }}
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

function Toast({ kind, message }) {
  const label =
    kind === 'error' ? 'Error' : kind === 'success' ? 'Success' : 'Info'
  const classes = ['toast']
  if (kind === 'error') classes.push('toast-error')
  else if (kind === 'success') classes.push('toast-success')
  else classes.push('toast-info')

  return (
    <div className={classes.join(' ')}>
      <strong style={{ marginRight: 6 }}>{label}:</strong>
      <span>{message}</span>
    </div>
  )
}
export default App
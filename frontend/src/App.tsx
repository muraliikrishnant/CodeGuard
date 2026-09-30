import { useState } from "react";
import "./App.css";

interface Finding {
  file_path: string;
  line_number: number;
  secret_type: string;
  detector: string;
  verdict: string;
  suppression_reason: string;
  llm_label: string | null;
  llm_confidence: number | null;
  llm_reasoning: string | null;
  commit_sha: string;
}

interface ScanResult {
  scan_id: string;
  timestamp: string;
  total_candidates: number;
  findings_count: number;
  suppressed_count: number;
  errors_count: number;
  findings: Finding[];
  suppressed: Finding[];
  errors: string[];
}

function App() {
  const [repoPath, setRepoPath] = useState("");
  const [provider, setProvider] = useState("nvidia");
  const [history, setHistory] = useState(true);
  const [threshold, setThreshold] = useState(0.8);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"findings" | "suppressed">("findings");

  const runScan = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("http://localhost:8001/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_path: repoPath, history, provider, threshold }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Scan failed");
      }
      setResult(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <span className="header-logo">🛡️</span>
          <h1>CodeGuard</h1>
        </div>
        <nav className="header-nav">
          <a href="#scan">Scan</a>
          <a href="#docs">Docs</a>
          <a href="https://github.com/muraliikrishnant/CodeGuard" target="_blank" rel="noreferrer">
            GitHub
          </a>
          <a href="#scan" className="header-cta">
            Run a Scan
          </a>
        </nav>
      </header>

      <main className="main-content">
        <h2 className="page-title">Secret Scanner</h2>
        <p className="page-subtitle">
          Git-aware secret detection with LLM-powered triage
        </p>

        <section className="scan-form" id="scan">
          <div className="form-row">
            <label>
              Repository Path
              <input
                type="text"
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
                placeholder="/path/to/local/git/repo"
              />
            </label>
          </div>
          <div className="form-row form-row-inline">
            <label>
              LLM Provider
              <select value={provider} onChange={(e) => setProvider(e.target.value)}>
                <option value="nvidia">NVIDIA</option>
                <option value="none">None (detect-secrets only)</option>
              </select>
            </label>
            <label>
              Confidence Threshold
              <input
                type="number"
                min="0"
                max="1"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
              />
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={history}
                onChange={(e) => setHistory(e.target.checked)}
              />
              Scan git history
            </label>
          </div>
          <button onClick={runScan} disabled={loading || !repoPath} className="scan-btn">
            {loading ? "Scanning..." : "Run Scan"}
          </button>
        </section>

        {error && <div className="error-banner">{error}</div>}

        {result && (
          <section className="results">
            <div className="stats-grid">
              <StatCard value={result.total_candidates} label="Candidates" />
              <StatCard value={result.findings_count} label="Findings" variant="danger" />
              <StatCard value={result.suppressed_count} label="Suppressed" variant="success" />
              <StatCard value={result.errors_count} label="Errors" variant="warning" />
            </div>

            <div className="tabs">
              <button
                className={activeTab === "findings" ? "tab active" : "tab"}
                onClick={() => setActiveTab("findings")}
              >
                Findings ({result.findings.length})
              </button>
              <button
                className={activeTab === "suppressed" ? "tab active" : "tab"}
                onClick={() => setActiveTab("suppressed")}
              >
                Suppressed ({result.suppressed.length})
              </button>
            </div>

            <div className="findings-list">
              {(activeTab === "findings" ? result.findings : result.suppressed).map((f, i) => (
                <FindingCard key={i} finding={f} />
              ))}
              {(activeTab === "findings" ? result.findings : result.suppressed).length === 0 && (
                <p className="empty-state">No {activeTab} to display.</p>
              )}
            </div>

            {result.errors.length > 0 && (
              <details style={{ marginTop: "1.5rem" }}>
                <summary
                  style={{
                    cursor: "pointer",
                    fontSize: "0.85rem",
                    color: "var(--text-muted)",
                    fontWeight: 600,
                  }}
                >
                  {result.errors.length} error{result.errors.length > 1 ? "s" : ""} during scan
                </summary>
                <ul
                  style={{
                    marginTop: "0.5rem",
                    fontSize: "0.8rem",
                    color: "var(--text-muted)",
                    fontFamily: "var(--font-mono)",
                    listStyle: "none",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.35rem",
                  }}
                >
                  {result.errors.map((err, i) => (
                    <li key={i} style={{ wordBreak: "break-all" }}>
                      {err}
                    </li>
                  ))}
                </ul>
              </details>
            )}

            <div className="meta">
              <span>Scan ID: {result.scan_id}</span>
              <span>{result.timestamp}</span>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

function StatCard({ value, label, variant }: { value: number; label: string; variant?: string }) {
  return (
    <div className={`stat-card ${variant ? `stat-${variant}` : ""}`}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

function FindingCard({ finding }: { finding: Finding }) {
  const [expanded, setExpanded] = useState(false);
  const vc =
    finding.verdict === "leak"
      ? "verdict-leak"
      : finding.verdict === "needs_review"
        ? "verdict-review"
        : "verdict-suppressed";

  return (
    <div className={`finding-card ${vc}`} onClick={() => setExpanded(!expanded)}>
      <div className="finding-header">
        <span className="finding-file">
          {finding.file_path}:{finding.line_number}
        </span>
        <span className={`verdict-badge ${vc}`}>{finding.verdict}</span>
      </div>
      <div className="finding-meta">
        <span className="badge">{finding.secret_type}</span>
        <span className="badge badge-secondary">{finding.detector}</span>
        <span className="commit-sha">{finding.commit_sha.slice(0, 7)}</span>
      </div>
      {expanded && (
        <div className="finding-details">
          {finding.llm_label && (
            <div className="llm-info">
              <strong>LLM:</strong> {finding.llm_label} (
              {((finding.llm_confidence ?? 0) * 100).toFixed(0)}%)
              <p>{finding.llm_reasoning}</p>
            </div>
          )}
          {finding.suppression_reason && (
            <p>
              <strong>Reason:</strong> {finding.suppression_reason}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default App;

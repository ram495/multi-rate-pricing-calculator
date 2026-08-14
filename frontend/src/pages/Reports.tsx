import { useState, type FormEvent } from "react";
import * as api from "../api/documents";
import type { ReportSummary } from "../api/types";
import { ApiError } from "../api/client";

function money(n: number) {
  return `$${n.toFixed(2)}`;
}

function firstOfMonth() {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10);
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

export function Reports() {
  const [dateFrom, setDateFrom] = useState(firstOfMonth());
  const [dateTo, setDateTo] = useState(today());
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const runReport = async (e?: FormEvent) => {
    e?.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await api.getReportSummary(dateFrom, dateTo);
      setSummary(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load report.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Reports</h1>
      {error && <div className="form-error">{error}</div>}

      <form className="inline-form card" onSubmit={runReport}>
        <div className="form-row">
          <label>
            From
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </label>
          <label>
            To
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "Loading..." : "Show Report"}
          </button>
        </div>
      </form>

      {summary && (
        <div className="summary-grid">
          <div className="summary-card">
            <div className="summary-label">Documents</div>
            <div className="summary-value">{summary.document_count}</div>
          </div>
          <div className="summary-card">
            <div className="summary-label">Sum of grand totals</div>
            <div className="summary-value">{money(summary.sum_grand_total)}</div>
          </div>
          <div className="summary-card">
            <div className="summary-label">Sum of total tax</div>
            <div className="summary-value">{money(summary.sum_total_tax)}</div>
          </div>
          <div className="summary-card">
            <div className="summary-label">Sum of total discount</div>
            <div className="summary-value">{money(summary.sum_total_discount)}</div>
          </div>
        </div>
      )}
    </div>
  );
}

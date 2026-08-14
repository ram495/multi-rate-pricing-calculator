import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import * as api from "../api/documents";
import type { Document } from "../api/types";
import { ApiError } from "../api/client";

function money(n: number) {
  return `$${n.toFixed(2)}`;
}

export function Documents() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [title, setTitle] = useState("");
  const [customer, setCustomer] = useState("");
  const [issueDate, setIssueDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [creating, setCreating] = useState(false);

  const load = () => {
    api
      .listDocuments()
      .then(setDocuments)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load documents."));
  };

  useEffect(load, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setCreating(true);
    try {
      const doc = await api.createDocument({ title, customer, issue_date: issueDate });
      navigate(`/documents/${doc.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create document.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <div className="documents-header">
        <h1>Documents</h1>
        <button type="button" onClick={() => setShowCreateForm((v) => !v)}>
          {showCreateForm ? "Cancel" : "+ New document"}
        </button>
      </div>
      {error && <div className="form-error">{error}</div>}

      {showCreateForm && (
        <form className="inline-form card" onSubmit={handleCreate}>
          <h2>New document</h2>
          <div className="form-row">
            <label>
              Title
              <input value={title} onChange={(e) => setTitle(e.target.value)} required />
            </label>
            <label>
              Customer
              <input value={customer} onChange={(e) => setCustomer(e.target.value)} required />
            </label>
            <label>
              Issue date
              <input
                type="date"
                value={issueDate}
                onChange={(e) => setIssueDate(e.target.value)}
                required
              />
            </label>
            <button type="submit" disabled={creating}>
              {creating ? "Creating..." : "Create document"}
            </button>
          </div>
        </form>
      )}

      {documents === null ? (
        <p>Loading...</p>
      ) : documents.length === 0 ? (
        <p>No documents yet.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Customer</th>
              <th>Issue date</th>
              <th>Status</th>
              <th>Grand total</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id}>
                <td>
                  <Link to={`/documents/${doc.id}`}>{doc.title}</Link>
                </td>
                <td>{doc.customer}</td>
                <td>{doc.issue_date}</td>
                <td>
                  <span className={`badge badge-${doc.status}`}>{doc.status}</span>
                </td>
                <td>{money(doc.grand_total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

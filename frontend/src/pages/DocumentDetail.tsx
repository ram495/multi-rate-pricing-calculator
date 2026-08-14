import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import * as api from "../api/documents";
import type { Document, DiscountType, LineItem, LineItemInput } from "../api/types";
import { ApiError } from "../api/client";

function money(n: number) {
  return `$${n.toFixed(2)}`;
}

const emptyForm = {
  description: "",
  quantity: "1",
  unit_price: "0.00",
  discount_type: "none" as DiscountType,
  discount_value: "",
  tax_percent: "",
};

type FormState = typeof emptyForm;

function lineToForm(line: LineItem): FormState {
  return {
    description: line.description,
    quantity: String(line.quantity),
    unit_price: String(line.unit_price),
    discount_type: line.discount_type,
    discount_value: line.discount_value !== null ? String(line.discount_value) : "",
    tax_percent: line.tax_percent !== null ? String(line.tax_percent) : "",
  };
}

export function DocumentDetail() {
  const { id } = useParams();
  const documentId = Number(id);
  const navigate = useNavigate();

  const [doc, setDoc] = useState<Document | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [headerForm, setHeaderForm] = useState({ title: "", customer: "", issue_date: "" });
  const [savingHeader, setSavingHeader] = useState(false);

  const [lineForm, setLineForm] = useState<FormState>(emptyForm);
  const [editingLineId, setEditingLineId] = useState<number | null>(null);
  const [savingLine, setSavingLine] = useState(false);
  const [duplicating, setDuplicating] = useState(false);

  const load = () => {
    api
      .getDocument(documentId)
      .then((data) => {
        setDoc(data);
        setHeaderForm({ title: data.title, customer: data.customer, issue_date: data.issue_date });
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load document."));
  };

  useEffect(load, [documentId]);

  if (!doc) {
    return <div>{error || "Loading..."}</div>;
  }

  const isDraft = doc.status === "draft";

  const handleHeaderSave = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSavingHeader(true);
    try {
      const updated = await api.updateDocument(documentId, headerForm);
      setDoc(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update document.");
    } finally {
      setSavingHeader(false);
    }
  };

  const handleLineSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSavingLine(true);
    const payload: LineItemInput = {
      description: lineForm.description,
      quantity: lineForm.quantity,
      unit_price: lineForm.unit_price,
      discount_type: lineForm.discount_type,
      discount_value: lineForm.discount_type === "none" ? null : lineForm.discount_value,
      tax_percent: lineForm.tax_percent === "" ? null : lineForm.tax_percent,
    };
    try {
      const updated = editingLineId
        ? await api.updateLine(documentId, editingLineId, payload)
        : await api.createLine(documentId, payload);
      setDoc(updated);
      setLineForm(emptyForm);
      setEditingLineId(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save line item.");
    } finally {
      setSavingLine(false);
    }
  };

  const startEdit = (line: LineItem) => {
    setEditingLineId(line.id);
    setLineForm(lineToForm(line));
  };

  const cancelEdit = () => {
    setEditingLineId(null);
    setLineForm(emptyForm);
  };

  const handleDeleteLine = async (lineId: number) => {
    setError(null);
    try {
      const updated = await api.deleteLine(documentId, lineId);
      setDoc(updated);
      // If the deleted line was open in the edit form, reset it — otherwise
      // "Update line" would PATCH a line that no longer exists.
      if (editingLineId === lineId) {
        setEditingLineId(null);
        setLineForm(emptyForm);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete line item.");
    }
  };

  const handleFinalize = async () => {
    setError(null);
    try {
      const updated = await api.finalizeDocument(documentId);
      setDoc(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to finalize document.");
    }
  };

  const handleDuplicate = async () => {
    setError(null);
    setDuplicating(true);
    try {
      const copy = await api.duplicateDocument(documentId);
      navigate(`/documents/${copy.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to duplicate document.");
    } finally {
      setDuplicating(false);
    }
  };

  const handleDeleteDocument = async () => {
    if (!confirm("Delete this draft document?")) return;
    setError(null);
    try {
      await api.deleteDocument(documentId);
      navigate("/documents");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to delete document.");
    }
  };

  return (
    <div>
      <div className="detail-header">
        <h1>{doc.title}</h1>
        <span className={`badge badge-${doc.status}`}>{doc.status}</span>
        <Link to={`/documents/${documentId}/print`} className="print-link">
          Print / PDF
        </Link>
      </div>
      {error && <div className="form-error">{error}</div>}

      <form id="document-header-form" className="inline-form card" onSubmit={handleHeaderSave}>
        <div className="form-row">
          <label>
            Title
            <input
              value={headerForm.title}
              disabled={!isDraft}
              onChange={(e) => setHeaderForm({ ...headerForm, title: e.target.value })}
              required
            />
          </label>
          <label>
            Customer
            <input
              value={headerForm.customer}
              disabled={!isDraft}
              onChange={(e) => setHeaderForm({ ...headerForm, customer: e.target.value })}
              required
            />
          </label>
          <label>
            Issue date
            <input
              type="date"
              value={headerForm.issue_date}
              disabled={!isDraft}
              onChange={(e) => setHeaderForm({ ...headerForm, issue_date: e.target.value })}
              required
            />
          </label>
        </div>
      </form>

      <table className="data-table">
        <thead>
          <tr>
            <th>Description</th>
            <th>Qty</th>
            <th>Unit price</th>
            <th>Discount</th>
            <th>Tax %</th>
            <th>Subtotal</th>
            <th>Discount amt</th>
            <th>Tax amt</th>
            <th>Total</th>
            {isDraft && <th></th>}
          </tr>
        </thead>
        <tbody>
          {doc.lines.map((line) => (
            <tr key={line.id}>
              <td>{line.description}</td>
              <td>{line.quantity}</td>
              <td>{money(line.unit_price)}</td>
              <td>
                {line.discount_type === "none"
                  ? "—"
                  : line.discount_type === "fixed"
                  ? money(line.discount_value ?? 0)
                  : `${line.discount_value}%`}
              </td>
              <td>{line.tax_percent !== null ? `${line.tax_percent}%` : "—"}</td>
              <td>{money(line.subtotal)}</td>
              <td>{money(line.discount_amount)}</td>
              <td>{money(line.tax_amount)}</td>
              <td>{money(line.total)}</td>
              {isDraft && (
                <td className="row-actions">
                  <button type="button" className="link-button" onClick={() => startEdit(line)}>
                    Edit
                  </button>
                  <button
                    type="button"
                    className="link-button danger"
                    onClick={() => handleDeleteLine(line.id)}
                  >
                    Delete
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan={5}>Totals</td>
            <td>{money(doc.subtotal)}</td>
            <td>{money(doc.total_discount)}</td>
            <td>{money(doc.total_tax)}</td>
            <td>{money(doc.grand_total)}</td>
            {isDraft && <td></td>}
          </tr>
        </tfoot>
      </table>

      {isDraft && (
        <form className="inline-form card" onSubmit={handleLineSubmit}>
          <h2>{editingLineId ? "Edit line item" : "Add line item"}</h2>
          <div className="form-row">
            <label>
              Description
              <input
                value={lineForm.description}
                onChange={(e) => setLineForm({ ...lineForm, description: e.target.value })}
                required
              />
            </label>
            <label>
              Quantity
              <input
                type="number"
                step="0.01"
                min="1"
                value={lineForm.quantity}
                onChange={(e) => setLineForm({ ...lineForm, quantity: e.target.value })}
                required
              />
            </label>
            <label>
              Unit price
              <input
                type="number"
                step="0.01"
                min="0"
                value={lineForm.unit_price}
                onChange={(e) => setLineForm({ ...lineForm, unit_price: e.target.value })}
                required
              />
            </label>
            <label>
              Discount type
              <select
                value={lineForm.discount_type}
                onChange={(e) =>
                  setLineForm({
                    ...lineForm,
                    discount_type: e.target.value as DiscountType,
                    discount_value: "",
                  })
                }
              >
                <option value="none">None</option>
                <option value="fixed">Fixed amount</option>
                <option value="percent">Percent</option>
              </select>
            </label>
            {lineForm.discount_type !== "none" && (
              <label>
                {lineForm.discount_type === "fixed" ? "Discount ($)" : "Discount (%)"}
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max={lineForm.discount_type === "percent" ? 100 : undefined}
                  value={lineForm.discount_value}
                  onChange={(e) => setLineForm({ ...lineForm, discount_value: e.target.value })}
                  required
                />
              </label>
            )}
            <label>
              Tax %
              <input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={lineForm.tax_percent}
                onChange={(e) => setLineForm({ ...lineForm, tax_percent: e.target.value })}
              />
            </label>
            <button type="submit" disabled={savingLine}>
              {savingLine ? "Saving..." : editingLineId ? "Update line" : "Add line"}
            </button>
            {editingLineId && (
              <button type="button" className="secondary" onClick={cancelEdit}>
                Cancel
              </button>
            )}
          </div>
        </form>
      )}

      <div className="detail-actions">
        {isDraft && (
          <>
            <button type="submit" form="document-header-form" disabled={savingHeader}>
              {savingHeader ? "Saving..." : "Save details"}
            </button>
            <button
              type="button"
              onClick={handleFinalize}
              disabled={doc.lines.length === 0}
              title={doc.lines.length === 0 ? "Add at least one line item first" : ""}
            >
              Finalize document
            </button>
          </>
        )}
        {!isDraft && (
          <button type="button" onClick={handleDuplicate} disabled={duplicating}>
            {duplicating ? "Duplicating..." : "Duplicate into new draft"}
          </button>
        )}
        {isDraft && (
          <button type="button" className="danger" onClick={handleDeleteDocument}>
            Delete document
          </button>
        )}
      </div>
      {!isDraft && (
        <p className="muted">This document is finalized and can no longer be edited.</p>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import * as api from "../api/documents";
import type { Document } from "../api/types";
import { ApiError } from "../api/client";

function money(n: number) {
  return `$${n.toFixed(2)}`;
}

export function DocumentPrint() {
  const { id } = useParams();
  const documentId = Number(id);
  const [doc, setDoc] = useState<Document | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getDocument(documentId)
      .then(setDoc)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load document."));
  }, [documentId]);

  if (!doc) {
    return <div className="print-page">{error || "Loading..."}</div>;
  }

  return (
    <div className="print-page">
      <div className="print-toolbar no-print">
        <Link to={`/documents/${documentId}`}>&larr; Back to document</Link>
        <button type="button" onClick={() => window.print()}>
          Print / Save as PDF
        </button>
      </div>

      <div className="print-sheet">
        <div className="print-header">
          <h1>{doc.title}</h1>
          <span className={`badge badge-${doc.status}`}>{doc.status}</span>
        </div>

        <div className="print-meta">
          <div>
            <div className="print-meta-label">Customer</div>
            <div>{doc.customer}</div>
          </div>
          <div>
            <div className="print-meta-label">Issue date</div>
            <div>{doc.issue_date}</div>
          </div>
        </div>

        <table className="data-table print-table">
          <thead>
            <tr>
              <th>Description</th>
              <th>Qty</th>
              <th>Unit price</th>
              <th>Discount</th>
              <th>Tax %</th>
              <th>Total</th>
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
                <td>{money(line.total)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="print-totals">
          <div>
            <span>Subtotal</span>
            <span>{money(doc.subtotal)}</span>
          </div>
          <div>
            <span>Discount</span>
            <span>-{money(doc.total_discount)}</span>
          </div>
          <div>
            <span>Tax</span>
            <span>{money(doc.total_tax)}</span>
          </div>
          <div className="print-grand-total">
            <span>Grand total</span>
            <span>{money(doc.grand_total)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

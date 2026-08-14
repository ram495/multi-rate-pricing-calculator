import { apiFetch } from "./client";
import type { Document, LineItemInput, ReportSummary } from "./types";

export function listDocuments() {
  return apiFetch<Document[]>("/documents/");
}

export function getDocument(id: number) {
  return apiFetch<Document>(`/documents/${id}/`);
}

export function createDocument(data: { title: string; customer: string; issue_date: string }) {
  return apiFetch<Document>("/documents/", { method: "POST", body: data });
}

export function updateDocument(
  id: number,
  data: Partial<{ title: string; customer: string; issue_date: string }>
) {
  return apiFetch<Document>(`/documents/${id}/`, { method: "PATCH", body: data });
}

export function deleteDocument(id: number) {
  return apiFetch<void>(`/documents/${id}/`, { method: "DELETE" });
}

export function finalizeDocument(id: number) {
  return apiFetch<Document>(`/documents/${id}/finalize/`, { method: "POST" });
}

export function createLine(documentId: number, data: LineItemInput) {
  return apiFetch<Document>(`/documents/${documentId}/lines/`, { method: "POST", body: data });
}

export function updateLine(documentId: number, lineId: number, data: Partial<LineItemInput>) {
  return apiFetch<Document>(`/documents/${documentId}/lines/${lineId}/`, {
    method: "PATCH",
    body: data,
  });
}

export function deleteLine(documentId: number, lineId: number) {
  return apiFetch<Document>(`/documents/${documentId}/lines/${lineId}/`, { method: "DELETE" });
}

export function getReportSummary(dateFrom?: string, dateTo?: string) {
  const params = new URLSearchParams();
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  const qs = params.toString();
  return apiFetch<ReportSummary>(`/reports/summary/${qs ? `?${qs}` : ""}`);
}

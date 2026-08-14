export type DiscountType = "none" | "fixed" | "percent";
export type DocumentStatus = "draft" | "finalized";

export interface LineItem {
  id: number;
  description: string;
  quantity: number;
  unit_price: number;
  discount_type: DiscountType;
  discount_value: number | null;
  tax_percent: number | null;
  sort_order: number;
  subtotal: number;
  discount_amount: number;
  after_discount: number;
  tax_amount: number;
  total: number;
}

export interface Document {
  id: number;
  title: string;
  customer: string;
  issue_date: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
  lines: LineItem[];
  subtotal: number;
  total_discount: number;
  total_tax: number;
  grand_total: number;
}

export interface ReportSummary {
  document_count: number;
  sum_grand_total: number;
  sum_total_tax: number;
  sum_total_discount: number;
}

export interface LineItemInput {
  description: string;
  quantity: string;
  unit_price: string;
  discount_type: DiscountType;
  discount_value: string | null;
  tax_percent: string | null;
}

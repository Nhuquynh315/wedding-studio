import type { components } from '@/lib/api-types'

// ── Auth ──────────────────────────────────────────────────────
export type Token = components['schemas']['Token']
export type UserCreate = components['schemas']['UserCreate']
export type UserLogin = components['schemas']['UserLogin']
export type UserPublic = components['schemas']['UserPublic']
export type UserUpdate = components['schemas']['UserUpdate']
export type PasswordChange = components['schemas']['PasswordChange']

// ── Wedding ───────────────────────────────────────────────────
export type WeddingCreate = components['schemas']['WeddingCreate']
export type WeddingUpdate = components['schemas']['WeddingUpdate']
export type WeddingPublic = components['schemas']['WeddingPublic']

// ── Guest ─────────────────────────────────────────────────────
export type GuestCreate = components['schemas']['GuestCreate']
export type GuestUpdate = components['schemas']['GuestUpdate']
export type GuestPublic = components['schemas']['GuestPublic']
export type GuestList = components['schemas']['GuestList']
export type RSVPStatus = components['schemas']['RSVPStatus']
export type BulkRSVPUpdate = components['schemas']['BulkRSVPUpdate']
export type BulkRSVPResult = components['schemas']['BulkRSVPResult']
export type CSVImportResult = components['schemas']['CSVImportResult']

// ── Budget ────────────────────────────────────────────────────
export type BudgetCategoryCreate = components['schemas']['BudgetCategoryCreate']
export type BudgetCategoryUpdate = components['schemas']['BudgetCategoryUpdate']
export type BudgetCategoryPublic = components['schemas']['BudgetCategoryPublic']
export type ExpenseCreate = components['schemas']['ExpenseCreate']
export type ExpenseUpdate = components['schemas']['ExpenseUpdate']
export type ExpensePublic = components['schemas']['ExpensePublic']
export type ScaleBudgetRequest = components['schemas']['ScaleBudgetRequest']
export type ScaleBudgetResult = components['schemas']['ScaleBudgetResult']
export type BudgetSummary = components['schemas']['BudgetSummary']

// ── Vendor ────────────────────────────────────────────────────
export type VendorCreate = components['schemas']['VendorCreate']
export type VendorUpdate = components['schemas']['VendorUpdate']
export type VendorPublic = components['schemas']['VendorPublic']
export type VendorStatus = components['schemas']['VendorStatus']

// ── Checklist ─────────────────────────────────────────────────
export type ChecklistItemCreate = components['schemas']['ChecklistItemCreate']
export type ChecklistItemUpdate = components['schemas']['ChecklistItemUpdate']
export type ChecklistItemPublic = components['schemas']['ChecklistItemPublic']
export type ChecklistCategory = components['schemas']['ChecklistCategory']
export type ChecklistPriority = components['schemas']['ChecklistPriority']
export type BulkCompleteRequest = components['schemas']['BulkCompleteRequest']
export type BulkCompleteResult = components['schemas']['BulkCompleteResult']

// ── Seating ───────────────────────────────────────────────────
export type WeddingTableCreate = components['schemas']['WeddingTableCreate']
export type WeddingTableUpdate = components['schemas']['WeddingTableUpdate']
export type WeddingTablePublic = components['schemas']['WeddingTablePublic']
export type WeddingTableWithGuests = components['schemas']['WeddingTableWithGuests']

// ── Design ────────────────────────────────────────────────────
export type ColorEntry = components['schemas']['ColorEntry']
export type FontPairing = components['schemas']['FontPairing']
export type GeneratedTheme = components['schemas']['GeneratedTheme']
export type DesignPublic = components['schemas']['DesignPublic']
export type GenerateDesignRequest = components['schemas']['GenerateDesignRequest']
// Tone and Layout are inlined by OpenAPI — derive them from the schema
export type Tone = GenerateDesignRequest['tone']
export type Layout = GeneratedTheme['layout']

// ── Errors ────────────────────────────────────────────────────
// ProblemDetails is the RFC 7807 envelope the backend sends for all errors.
// FastAPI doesn't register it as an OpenAPI component, so we define it here.
export type ProblemDetails = {
  type: string
  title: string
  status: number
  detail?: string
  instance?: string
  [key: string]: unknown
}

export const STATUS_COLORS: Record<string, string> = {
  Draft: "default",
  Submitted: "processing",
  SpecGenerated: "success",
  SpecReviewPending: "warning",
  AudioGenerated: "success",
  AudioGenerationFailed: "error",
  QCReady: "success",
  QCFailed: "error",
  WwiseImported: "success",
  WwiseImportFailed: "error",
  BankBuilt: "success",
  BankBuildFailed: "error",
  UEBound: "success",
  UEBindFailed: "error",
  BindingReviewPending: "warning",
  QARun: "processing",
  ReviewPending: "warning",
  Approved: "success",
  Rejected: "error",
  RolledBack: "default",
};

export const PIPELINE_STEPS = [
  "Draft", "Submitted", "SpecGenerated", "AudioGenerated", "QCReady",
  "WwiseImported", "BankBuilt", "UEBound", "QARun", "ReviewPending", "Approved",
];

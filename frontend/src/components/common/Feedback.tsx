export function ErrorMessage({ children }: { children: string }) {
  return <div className="feedback feedback-error" role="alert">{children}</div>;
}

export function SuccessMessage({ children }: { children: string }) {
  return <div className="feedback feedback-success" role="status">{children}</div>;
}

export function LoadingState({ label = "Cargando información..." }: { label?: string }) {
  return <div className="empty-state">{label}</div>;
}

export function EmptyState({ children }: { children: string }) {
  return <div className="empty-state">{children}</div>;
}

import type { LucideIcon } from "lucide-react";

export function StatCard({
  icon: Icon,
  label,
  value,
  note,
}: {
  icon: LucideIcon;
  label: string;
  value: string | number;
  note: string;
}) {
  return (
    <article className="stat-card">
      <div className="stat-icon"><Icon size={20} /></div>
      <p className="stat-label">{label}</p>
      <strong>{value}</strong>
      <span>{note}</span>
    </article>
  );
}

export function StatusBadge({ value }: { value: string }) {
  const tone = /ACTIVA|DISPONIBLE|PAGADO|AL_DIA/i.test(value)
    ? "status-good"
    : /PENDIENTE|PROGRAMADA|EN_SUBASTA/i.test(value)
      ? "status-pending"
      : /DESIERTA|FINALIZADA|SUSPENDIDO|RECHAZADO|ADJUDICADO/i.test(value)
        ? "status-muted"
        : "status-neutral";
  return <span className={`status-badge ${tone}`}>{value.replaceAll("_", " ")}</span>;
}

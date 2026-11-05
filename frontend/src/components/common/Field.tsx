import type { InputHTMLAttributes, SelectHTMLAttributes } from "react";
import type { ReactNode } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export function Field({ label, id, ...props }: InputProps) {
  const fieldId = id ?? props.name;
  return (
    <label className="field" htmlFor={fieldId}>
      <span>{label}</span>
      <input id={fieldId} {...props} />
    </label>
  );
}

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  children: ReactNode;
};

export function SelectField({ label, id, children, ...props }: SelectProps) {
  const fieldId = id ?? props.name;
  return (
    <label className="field" htmlFor={fieldId}>
      <span>{label}</span>
      <select id={fieldId} {...props}>{children}</select>
    </label>
  );
}

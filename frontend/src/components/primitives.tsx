/** Primitivos de formulário no estilo e-Nota (label acima, asterisco vermelho,
 *  estados de erro e somente-leitura). Todos controlados. */

import { type ReactNode } from 'react';
import type { Option } from '../api/lookups';

interface FieldProps {
  label: string;
  required?: boolean;
  error?: string;
  hint?: string;
  className?: string;
  children: ReactNode;
}

export function Field({ label, required, error, hint, className, children }: FieldProps) {
  return (
    <div className={`field${className ? ` ${className}` : ''}`}>
      <label className="field__label">
        {label}
        {required && <span className="field__req">*</span>}
      </label>
      {children}
      {error && <span className="field__error">{error}</span>}
      {!error && hint && <span className="field__hint">{hint}</span>}
    </div>
  );
}

interface TextInputProps {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  maxLength?: number;
  error?: boolean;
  disabled?: boolean;
  type?: 'text' | 'date' | 'email' | 'tel';
}

export function TextInput({ value, onChange, placeholder, maxLength, error, disabled, type = 'text' }: TextInputProps) {
  return (
    <input
      className={`input${error ? ' input--error' : ''}`}
      type={type}
      value={value}
      maxLength={maxLength}
      placeholder={placeholder}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}

interface TextAreaProps {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  maxLength?: number;
  error?: boolean;
  rows?: number;
}

export function TextArea({ value, onChange, placeholder, maxLength, error, rows = 4 }: TextAreaProps) {
  return (
    <textarea
      className={`input${error ? ' input--error' : ''}`}
      rows={rows}
      value={value}
      maxLength={maxLength}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}

interface SelectProps {
  value: string;
  onChange: (v: string) => void;
  options: Option[];
  placeholder?: string;
  error?: boolean;
  disabled?: boolean;
}

export function Select({ value, onChange, options, placeholder = 'Selecione...', error, disabled }: SelectProps) {
  return (
    <select
      className={`select${error ? ' select--error' : ''}`}
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">{placeholder}</option>
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

interface RadioGroupProps {
  name: string;
  value: string;
  onChange: (v: string) => void;
  options: Option[];
  inline?: boolean;
}

export function RadioGroup({ name, value, onChange, options, inline }: RadioGroupProps) {
  return (
    <div className={`radio-group${inline ? ' radio-group--inline' : ''}`}>
      {options.map((o) => (
        <label key={o.value} className="radio">
          <input
            type="radio"
            name={name}
            checked={value === o.value}
            onChange={() => onChange(o.value)}
          />
          {o.label}
        </label>
      ))}
    </div>
  );
}

interface CheckboxProps {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}

export function Checkbox({ checked, onChange, label }: CheckboxProps) {
  return (
    <label className="checkbox-row">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      {label}
    </label>
  );
}

interface MoneyInputProps {
  value: string;
  onChange: (v: string) => void;
  error?: boolean;
  disabled?: boolean;
  prefix?: string;
}

export function MoneyInput({ value, onChange, error, disabled, prefix = 'R$' }: MoneyInputProps) {
  return (
    <div className="input-money">
      <span className="input-money__prefix">{prefix}</span>
      <input
        className={`input${error ? ' input--error' : ''}${disabled ? ' input--readonly' : ''}`}
        inputMode="decimal"
        value={value}
        disabled={disabled}
        placeholder="0,00"
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

/** Campo somente-leitura (cinza) — para valores calculados pelo sistema. */
export function ReadOnlyField({ label, value, hint, money }: { label: string; value: string; hint?: string; money?: boolean }) {
  return (
    <Field label={label} hint={hint}>
      {money ? (
        <div className="input-money">
          <span className="input-money__prefix">R$</span>
          <input className="input input--readonly" value={value} disabled readOnly />
        </div>
      ) : (
        <input className="input input--readonly" value={value} disabled readOnly />
      )}
    </Field>
  );
}

export function Card({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <div className="card">
      {title && <h2 className="card__title">{title}</h2>}
      {children}
    </div>
  );
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="section">
      <h3 className="section__title">{title}</h3>
      {children}
    </div>
  );
}

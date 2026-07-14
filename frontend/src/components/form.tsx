/** Reusable form primitives — TextField, NumField, SelectField,
 *  TextAreaField, BoolRadio, Section, AddBtn, RemBtn. Same visual
 *  language as CyberFraud Data Entry (KSP navy + yellow + red).
 *
 *  Kept in one file so any FIR-entry tab can pick what it needs
 *  without further file spelunking. */
import type { ReactNode } from 'react';
import { Plus, Trash2 } from 'lucide-react';

export function Section({
  title, children, cols = 3,
}: { title: string; children: ReactNode; cols?: 2 | 3 | 4 | 6 }) {
  const gridClass = {
    2: 'grid grid-cols-1 sm:grid-cols-2 gap-4',
    3: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4',
    4: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4',
    6: 'grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4',
  }[cols];
  return (
    <div
      className="rounded-2xl p-5"
      style={{
        background: '#fff',
        border: '1px solid rgba(0,0,0,0.06)',
        boxShadow: '0 6px 16px rgba(0,0,0,0.08)',
      }}
    >
      <h3
        className="text-sm font-bold mb-4 uppercase tracking-wide"
        style={{ color: 'var(--ksp-red)' }}
      >
        {title}
      </h3>
      <div className={gridClass}>{children}</div>
    </div>
  );
}

interface FieldWrap {
  wrapperClassName?: string;
}

export function TextField({
  label, value, onChange, placeholder, type = 'text',
  readOnly = false, maxLength, inputMode, wrapperClassName,
}: FieldWrap & {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  readOnly?: boolean;
  maxLength?: number;
  inputMode?: 'text' | 'numeric' | 'email' | 'tel';
}) {
  return (
    <div className={wrapperClassName}>
      <label className="block text-xs font-semibold mb-1" style={{ color: 'var(--ksp-navy)' }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => !readOnly && onChange(e.target.value)}
        readOnly={readOnly}
        maxLength={maxLength}
        inputMode={inputMode}
        className="w-full px-3 py-2 rounded-xl text-sm outline-none"
        style={{
          border: readOnly ? '1px solid rgba(11,44,74,0.15)' : '2px solid var(--ksp-navy)',
          background: readOnly ? 'rgba(11,44,74,0.04)' : '#fff',
          color: readOnly ? 'rgba(0,0,0,0.6)' : 'inherit',
          cursor: readOnly ? 'not-allowed' : 'text',
        }}
        placeholder={readOnly ? '' : placeholder ?? ''}
      />
    </div>
  );
}

export function NumField({
  label, value, onChange, wrapperClassName, step = 1, min = 0,
}: FieldWrap & {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
  step?: number;
  min?: number;
}) {
  return (
    <div className={wrapperClassName}>
      <label className="block text-xs font-semibold mb-1" style={{ color: 'var(--ksp-navy)' }}>
        {label}
      </label>
      <input
        type="number"
        min={min}
        step={step}
        value={value ?? ''}
        onChange={(e) => {
          const raw = e.target.value;
          onChange(raw === '' ? null : Number(raw));
        }}
        className="w-full px-3 py-2 rounded-xl text-sm outline-none"
        style={{ border: '2px solid var(--ksp-navy)', background: '#fff' }}
      />
    </div>
  );
}

export function SelectField({
  label, value, onChange, options, wrapperClassName,
}: FieldWrap & {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className={wrapperClassName}>
      <label className="block text-xs font-semibold mb-1" style={{ color: 'var(--ksp-navy)' }}>
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 rounded-xl text-sm font-semibold outline-none"
        style={{
          border: '2px solid var(--ksp-navy)',
          background: 'var(--ksp-navy)',
          color: 'var(--ksp-yellow)',
        }}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

export function TextAreaField({
  label, value, onChange, rows = 3, maxLength,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  rows?: number;
  maxLength?: number;
}) {
  return (
    <div className="col-span-full">
      <label className="block text-xs font-semibold mb-1" style={{ color: 'var(--ksp-navy)' }}>
        {label}
      </label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        maxLength={maxLength}
        className="w-full px-3 py-2 rounded-xl text-sm outline-none resize-y"
        style={{ border: '2px solid var(--ksp-navy)', background: '#fff' }}
      />
      {maxLength !== undefined && (
        <p className="text-xs mt-1" style={{ color: 'rgba(11,44,74,0.4)' }}>
          {value.length} / {maxLength} characters
        </p>
      )}
    </div>
  );
}

export function BoolRadio({
  label, value, onChange, wrapperClassName, trueLabel = 'Yes', falseLabel = 'No',
}: FieldWrap & {
  label: string;
  value: boolean | null;
  onChange: (v: boolean | null) => void;
  trueLabel?: string;
  falseLabel?: string;
}) {
  const pill = (active: boolean) => ({
    background: active ? 'var(--ksp-navy)' : '#fff',
    color: active ? 'var(--ksp-yellow)' : 'var(--ksp-navy)',
    border: active ? '2px solid var(--ksp-navy)' : '2px solid rgba(11,44,74,0.18)',
    cursor: 'pointer' as const,
  });
  return (
    <div className={wrapperClassName}>
      <label className="block text-xs font-semibold mb-1" style={{ color: 'var(--ksp-navy)' }}>
        {label}
      </label>
      <div className="flex gap-2">
        <button type="button" onClick={() => onChange(true)}
          className="px-3 py-1 rounded-lg text-xs font-bold" style={pill(value === true)}>
          {trueLabel}
        </button>
        <button type="button" onClick={() => onChange(false)}
          className="px-3 py-1 rounded-lg text-xs font-bold" style={pill(value === false)}>
          {falseLabel}
        </button>
        {value !== null && (
          <button type="button" onClick={() => onChange(null)}
            className="px-3 py-1 rounded-lg text-xs" style={{ color: 'rgba(0,0,0,0.4)' }}>
            Clear
          </button>
        )}
      </div>
    </div>
  );
}

export function AddBtn({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <button type="button" onClick={onClick}
      className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-xl transition"
      style={{ background: 'var(--ksp-navy)', color: 'var(--ksp-yellow)', border: '2px solid rgba(0,0,0,0.25)' }}>
      <Plus className="w-4 h-4" /> {label}
    </button>
  );
}

export function RemBtn({ onClick }: { onClick: () => void }) {
  return (
    <button type="button" onClick={onClick}
      className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg transition"
      style={{ background: 'rgba(177,0,0,0.08)', color: 'var(--ksp-red)', border: '1px solid rgba(177,0,0,0.2)' }}>
      <Trash2 className="w-3.5 h-3.5" /> Remove
    </button>
  );
}

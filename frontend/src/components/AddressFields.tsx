/** Campos de endereço reaproveitáveis (endNac e endExt), na ordem da tela e-Nota. */

import type { EndNac, EndExt } from '../types/dps';
import type { Errors } from '../state/DpsContext';
import { searchPaises, searchMunicipiosApi } from '../api/lookups';
import { Field, TextInput, Select } from './primitives';
import { useOptions } from './useOptions';

interface NacProps {
  end: EndNac;
  onField: (field: keyof EndNac, value: string) => void;
  errors: Errors;
  prefix: string;
}

export function EndNacFields({ end, onField, errors, prefix }: NacProps) {
  const municipios = useOptions(searchMunicipiosApi);
  return (
    <div className="grid grid-3" style={{ marginTop: 'var(--space-3)' }}>
      <Field label="CEP" required error={errors[`${prefix}.CEP`]}>
        <TextInput value={end.CEP} maxLength={8} onChange={(v) => onField('CEP', v)} error={!!errors[`${prefix}.CEP`]} />
      </Field>
      <Field label="Logradouro" required error={errors[`${prefix}.xLgr`]} className="col-span-2">
        <TextInput value={end.xLgr} maxLength={255} onChange={(v) => onField('xLgr', v)} error={!!errors[`${prefix}.xLgr`]} />
      </Field>
      <Field label="Número" required error={errors[`${prefix}.nro`]}>
        <TextInput value={end.nro} maxLength={60} onChange={(v) => onField('nro', v)} error={!!errors[`${prefix}.nro`]} />
      </Field>
      <Field label="Complemento">
        <TextInput value={end.xCpl} maxLength={156} onChange={(v) => onField('xCpl', v)} />
      </Field>
      <Field label="Bairro" required error={errors[`${prefix}.xBairro`]}>
        <TextInput value={end.xBairro} maxLength={60} onChange={(v) => onField('xBairro', v)} error={!!errors[`${prefix}.xBairro`]} />
      </Field>
      <Field label="Município" required error={errors[`${prefix}.cMun`]} className="col-span-full">
        <Select value={end.cMun} options={municipios} onChange={(v) => onField('cMun', v)} error={!!errors[`${prefix}.cMun`]} />
      </Field>
    </div>
  );
}

interface ExtProps {
  end: EndExt;
  onField: (field: keyof EndExt, value: string) => void;
  errors: Errors;
  prefix: string;
}

export function EndExtFields({ end, onField, errors, prefix }: ExtProps) {
  const paises = useOptions(searchPaises);
  return (
    <div className="grid grid-2" style={{ marginTop: 'var(--space-3)' }}>
      <Field label="País" required error={errors[`${prefix}.cPais`]}>
        <Select value={end.cPais} options={paises} onChange={(v) => onField('cPais', v)} error={!!errors[`${prefix}.cPais`]} />
      </Field>
      <Field label="Código postal" required error={errors[`${prefix}.cEndPost`]}>
        <TextInput value={end.cEndPost} onChange={(v) => onField('cEndPost', v)} error={!!errors[`${prefix}.cEndPost`]} />
      </Field>
      <Field label="Cidade" required error={errors[`${prefix}.xCidade`]}>
        <TextInput value={end.xCidade} maxLength={60} onChange={(v) => onField('xCidade', v)} error={!!errors[`${prefix}.xCidade`]} />
      </Field>
      <Field label="Estado/Província/Região" required error={errors[`${prefix}.xEstProvReg`]}>
        <TextInput value={end.xEstProvReg} maxLength={60} onChange={(v) => onField('xEstProvReg', v)} error={!!errors[`${prefix}.xEstProvReg`]} />
      </Field>
      <Field label="Logradouro" required error={errors[`${prefix}.xLgr`]} className="col-span-2">
        <TextInput value={end.xLgr} maxLength={255} onChange={(v) => onField('xLgr', v)} error={!!errors[`${prefix}.xLgr`]} />
      </Field>
      <Field label="Número" required error={errors[`${prefix}.nro`]}>
        <TextInput value={end.nro} maxLength={60} onChange={(v) => onField('nro', v)} error={!!errors[`${prefix}.nro`]} />
      </Field>
      <Field label="Complemento">
        <TextInput value={end.xCpl} maxLength={156} onChange={(v) => onField('xCpl', v)} />
      </Field>
      <Field label="Bairro" required error={errors[`${prefix}.xBairro`]}>
        <TextInput value={end.xBairro} maxLength={60} onChange={(v) => onField('xBairro', v)} error={!!errors[`${prefix}.xBairro`]} />
      </Field>
    </div>
  );
}

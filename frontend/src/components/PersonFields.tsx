/** Bloco "Dados do Tomador/Intermediário do Serviço" — radio Não informado /
 *  Brasil / Exterior, com os campos de identificação e endereço de cada caso. */

import type { Pessoa } from '../types/dps';
import type { Errors } from '../state/DpsContext';
import { Field, TextInput, Select, RadioGroup, Checkbox } from './primitives';
import { EndNacFields, EndExtFields } from './AddressFields';

interface PersonFieldsProps {
  title: string;
  naoInformadoLabel: string;
  pessoa: Pessoa;
  update: (mutator: (p: Pessoa) => void) => void;
  errors: Errors;
  prefix: string;
}

const CNAONIF_OPTS = [
  { value: '0', label: '0 - Não informado' },
  { value: '1', label: '1 - Dispensado do NIF' },
  { value: '2', label: '2 - Não exigência do NIF' },
];

export function PersonFields({ title, naoInformadoLabel, pessoa, update, errors, prefix }: PersonFieldsProps) {
  return (
    <div className="card">
      <h2 className="card__title">{title}</h2>

      <RadioGroup
        name={prefix}
        value={pessoa.tipo}
        onChange={(v) => update((p) => { p.tipo = v as Pessoa['tipo']; })}
        options={[
          { value: 'naoInformado', label: naoInformadoLabel },
          { value: 'brasil', label: 'Brasil' },
          { value: 'exterior', label: 'Exterior' },
        ]}
        inline
      />

      {pessoa.tipo === 'brasil' && (
        <div className="grid grid-2" style={{ marginTop: 'var(--space-4)' }}>
          <Field label="Tipo de documento">
            <RadioGroup
              name={`${prefix}-docType`}
              value={pessoa.brasil.docType}
              onChange={(v) => update((p) => { p.brasil.docType = v as 'CPF' | 'CNPJ'; })}
              options={[{ value: 'CNPJ', label: 'CNPJ' }, { value: 'CPF', label: 'CPF' }]}
              inline
            />
          </Field>
          <Field label={pessoa.brasil.docType} required error={errors[`${prefix}.doc`]}>
            <TextInput
              value={pessoa.brasil.doc}
              maxLength={pessoa.brasil.docType === 'CPF' ? 11 : 14}
              onChange={(v) => update((p) => { p.brasil.doc = v; })}
              error={!!errors[`${prefix}.doc`]}
            />
          </Field>
          <Field label="Nome/Razão Social" required error={errors[`${prefix}.xNome`]} className="col-span-2">
            <TextInput value={pessoa.brasil.xNome} maxLength={150} onChange={(v) => update((p) => { p.brasil.xNome = v; })} error={!!errors[`${prefix}.xNome`]} />
          </Field>
          <Field label="Inscrição Municipal">
            <TextInput value={pessoa.brasil.IM} maxLength={15} onChange={(v) => update((p) => { p.brasil.IM = v; })} />
          </Field>
          <Field label="CAEPF (pessoa física)">
            <TextInput value={pessoa.brasil.CAEPF} maxLength={14} onChange={(v) => update((p) => { p.brasil.CAEPF = v; })} />
          </Field>
          <Field label="Telefone">
            <TextInput value={pessoa.brasil.fone} maxLength={20} onChange={(v) => update((p) => { p.brasil.fone = v; })} />
          </Field>
          <Field label="E-mail">
            <TextInput type="email" value={pessoa.brasil.email} maxLength={80} onChange={(v) => update((p) => { p.brasil.email = v; })} />
          </Field>
          <div className="col-span-full">
            <Checkbox
              checked={pessoa.brasil.informarEndereco}
              onChange={(v) => update((p) => { p.brasil.informarEndereco = v; })}
              label="Informar endereço"
            />
            {pessoa.brasil.informarEndereco && (
              <EndNacFields
                end={pessoa.brasil.end}
                onField={(f, v) => update((p) => { p.brasil.end[f] = v; })}
                errors={errors}
                prefix={`${prefix}.end`}
              />
            )}
          </div>
        </div>
      )}

      {pessoa.tipo === 'exterior' && (
        <div className="grid grid-2" style={{ marginTop: 'var(--space-4)' }}>
          <Field label="Identificação no exterior">
            <RadioGroup
              name={`${prefix}-nifMode`}
              value={pessoa.exterior.nifMode}
              onChange={(v) => update((p) => { p.exterior.nifMode = v as 'NIF' | 'cNaoNIF'; })}
              options={[{ value: 'NIF', label: 'Informar NIF' }, { value: 'cNaoNIF', label: 'Motivo de não informar' }]}
              inline
            />
          </Field>
          {pessoa.exterior.nifMode === 'NIF' ? (
            <Field label="NIF (nº fiscal no exterior)" required error={errors[`${prefix}.NIF`]}>
              <TextInput value={pessoa.exterior.NIF} maxLength={40} onChange={(v) => update((p) => { p.exterior.NIF = v; })} error={!!errors[`${prefix}.NIF`]} />
            </Field>
          ) : (
            <Field label="Motivo de não informar NIF" required error={errors[`${prefix}.cNaoNIF`]}>
              <Select value={pessoa.exterior.cNaoNIF} options={CNAONIF_OPTS} onChange={(v) => update((p) => { p.exterior.cNaoNIF = v; })} error={!!errors[`${prefix}.cNaoNIF`]} />
            </Field>
          )}
          <Field label="Nome/Razão Social" required error={errors[`${prefix}.xNome`]} className="col-span-2">
            <TextInput value={pessoa.exterior.xNome} maxLength={150} onChange={(v) => update((p) => { p.exterior.xNome = v; })} error={!!errors[`${prefix}.xNome`]} />
          </Field>
          <Field label="Telefone">
            <TextInput value={pessoa.exterior.fone} maxLength={20} onChange={(v) => update((p) => { p.exterior.fone = v; })} />
          </Field>
          <Field label="E-mail">
            <TextInput type="email" value={pessoa.exterior.email} maxLength={80} onChange={(v) => update((p) => { p.exterior.email = v; })} />
          </Field>
          <div className="col-span-full">
            <Checkbox
              checked={pessoa.exterior.informarEndereco}
              onChange={(v) => update((p) => { p.exterior.informarEndereco = v; })}
              label="Informar endereço"
            />
            {pessoa.exterior.informarEndereco && (
              <EndExtFields
                end={pessoa.exterior.end}
                onField={(f, v) => update((p) => { p.exterior.end[f] = v; })}
                errors={errors}
                prefix={`${prefix}.end`}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

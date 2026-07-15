/** Formulário reutilizável de cliente (criar/editar) com validação client-side
 * que espelha as regras do backend (documento, endereço tudo-ou-nada, email). */

import { useEffect, useState, type FormEvent } from 'react';
import { Card, Field, Section, TextInput } from '../../components/primitives';
import { MunicipioSelect } from '../../components/lookups/MunicipioSelect';
import type { Client, ClientCreate } from './types';
import { useCnpjData } from './hooks';

interface Props {
  initial?: Client;
  onSubmit: (data: ClientCreate) => void;
  submitting?: boolean;
  serverError?: string | null;
  submitLabel?: string;
}

type FormState = {
  document: string;
  name: string;
  municipal_registration: string;
  phone: string;
  email: string;
  zip_code: string;
  street: string;
  number: string;
  complement: string;
  neighborhood: string;
  ibge_city_code: string;
};

const ADDRESS_KEYS = ['zip_code', 'street', 'number', 'neighborhood', 'ibge_city_code'] as const;

function fromClient(c?: Client): FormState {
  return {
    document: c?.document ?? '',
    name: c?.name ?? '',
    municipal_registration: c?.municipal_registration ?? '',
    phone: c?.phone ?? '',
    email: c?.email ?? '',
    zip_code: c?.zip_code ?? '',
    street: c?.street ?? '',
    number: c?.number ?? '',
    complement: c?.complement ?? '',
    neighborhood: c?.neighborhood ?? '',
    ibge_city_code: c?.ibge_city_code ?? '',
  };
}

const onlyDigits = (s: string) => s.replace(/\D/g, '');
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validate(f: FormState): Record<string, string> {
  const errors: Record<string, string> = {};

  const doc = onlyDigits(f.document);
  if (!doc) errors.document = 'Documento é obrigatório.';
  else if (doc.length !== 11 && doc.length !== 14)
    errors.document = 'Documento deve ter 11 dígitos (CPF) ou 14 (CNPJ).';

  const name = f.name.trim();
  if (!name) errors.name = 'Nome é obrigatório.';
  else if (name.length > 150) errors.name = 'Nome deve ter no máximo 150 caracteres.';

  if (f.email.trim() && !EMAIL_RE.test(f.email.trim()))
    errors.email = 'E-mail inválido.';

  // Endereço tudo-ou-nada.
  const anyAddress = ADDRESS_KEYS.some((k) => f[k].trim());
  if (anyAddress) {
    for (const k of ADDRESS_KEYS) {
      if (!f[k].trim()) errors[k] = 'Obrigatório quando há endereço.';
    }
    const cep = onlyDigits(f.zip_code);
    if (f.zip_code.trim() && cep.length !== 8) errors.zip_code = 'CEP deve ter 8 dígitos.';
    if (f.ibge_city_code.trim() && f.ibge_city_code.trim().length !== 7)
      errors.ibge_city_code = 'Código IBGE deve ter 7 dígitos.';
  }

  return errors;
}

function toPayload(f: FormState): ClientCreate {
  const trimOrNull = (s: string) => (s.trim() ? s.trim() : null);
  const anyAddress = ADDRESS_KEYS.some((k) => f[k].trim());
  return {
    document: onlyDigits(f.document),
    name: f.name.trim(),
    municipal_registration: trimOrNull(f.municipal_registration),
    phone: trimOrNull(f.phone),
    email: trimOrNull(f.email),
    zip_code: anyAddress ? onlyDigits(f.zip_code) : null,
    street: anyAddress ? trimOrNull(f.street) : null,
    number: anyAddress ? trimOrNull(f.number) : null,
    complement: trimOrNull(f.complement),
    neighborhood: anyAddress ? trimOrNull(f.neighborhood) : null,
    ibge_city_code: anyAddress ? trimOrNull(f.ibge_city_code) : null,
  };
}

export function ClientForm({ initial, onSubmit, submitting, serverError, submitLabel }: Props) {
  const [form, setForm] = useState<FormState>(() => fromClient(initial));
  const [errors, setErrors] = useState<Record<string, string>>({});

  const cnpjDigits = onlyDigits(form.document);
  const shouldLookup = !initial && cnpjDigits.length === 14;
  const { data: cnpjData, isFetching: cnpjFetching, isError: cnpjNotFound } = useCnpjData(
    shouldLookup ? cnpjDigits : '',
  );

  useEffect(() => {
    if (!cnpjData) return;
    setForm((prev) => ({
      ...prev,
      name: cnpjData.name,
      phone: cnpjData.phone ?? '',
      email: cnpjData.email ?? '',
      zip_code: cnpjData.zip_code ?? '',
      street: cnpjData.street ?? '',
      number: cnpjData.number ?? '',
      complement: cnpjData.complement ?? '',
      neighborhood: cnpjData.neighborhood ?? '',
      ibge_city_code: cnpjData.ibge_city_code ?? '',
    }));
  }, [cnpjData]);

  const docHint = cnpjFetching
    ? 'Buscando dados na Receita Federal...'
    : cnpjNotFound && shouldLookup
    ? 'CNPJ não encontrado na Receita Federal.'
    : undefined;

  function set<K extends keyof FormState>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const errs = validate(form);
    setErrors(errs);
    if (Object.keys(errs).length > 0) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    onSubmit(toPayload(form));
  }

  return (
    <form onSubmit={handleSubmit}>
      {serverError && <div className="banner banner--warn">{serverError}</div>}

      <Card title="Dados do cliente">
        <div className="grid grid-2">
          <Field label="Documento (CPF/CNPJ)" required error={errors.document} hint={docHint}>
            <TextInput
              value={form.document}
              onChange={(v) => set('document', v)}
              error={!!errors.document}
              placeholder="Somente números"
              disabled={cnpjFetching}
            />
          </Field>
          <Field label="Nome / Razão social" required error={errors.name}>
            <TextInput value={form.name} maxLength={150} onChange={(v) => set('name', v)} error={!!errors.name} />
          </Field>
          <Field label="Inscrição municipal">
            <TextInput value={form.municipal_registration} onChange={(v) => set('municipal_registration', v)} />
          </Field>
          <Field label="Telefone">
            <TextInput type="tel" value={form.phone} onChange={(v) => set('phone', v)} />
          </Field>
          <Field label="E-mail" error={errors.email} className="col-span-2">
            <TextInput type="email" value={form.email} onChange={(v) => set('email', v)} error={!!errors.email} />
          </Field>
        </div>

        <Section title="Endereço (opcional — preencha tudo ou nada)">
          <div className="grid grid-3">
            <Field label="CEP" error={errors.zip_code}>
              <TextInput value={form.zip_code} maxLength={9} onChange={(v) => set('zip_code', v)} error={!!errors.zip_code} />
            </Field>
            <Field label="Logradouro" error={errors.street} className="col-span-2">
              <TextInput value={form.street} maxLength={255} onChange={(v) => set('street', v)} error={!!errors.street} />
            </Field>
            <Field label="Número" error={errors.number}>
              <TextInput value={form.number} maxLength={60} onChange={(v) => set('number', v)} error={!!errors.number} />
            </Field>
            <Field label="Complemento">
              <TextInput value={form.complement} maxLength={156} onChange={(v) => set('complement', v)} />
            </Field>
            <Field label="Bairro" error={errors.neighborhood}>
              <TextInput value={form.neighborhood} maxLength={60} onChange={(v) => set('neighborhood', v)} error={!!errors.neighborhood} />
            </Field>
            <Field label="Município" error={errors.ibge_city_code} className="col-span-full">
              <MunicipioSelect
                value={form.ibge_city_code}
                onChange={(v) => set('ibge_city_code', v)}
                error={!!errors.ibge_city_code}
              />
            </Field>
          </div>
        </Section>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Salvando...' : (submitLabel ?? 'Salvar')}
          </button>
        </div>
      </Card>
    </form>
  );
}

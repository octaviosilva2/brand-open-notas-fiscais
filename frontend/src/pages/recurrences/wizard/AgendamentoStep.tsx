/** Etapa de Agendamento da recorrência: dia do mês, data de início, data de
 *  fim (opcional) e ativo. Guarda em `WizardExtrasContext`; valida antes de
 *  avançar (espelha as regras do backend: dia 1–31, fim ≥ início). */

import { useState } from 'react';
import { Card, Field, Checkbox } from '../../../components/primitives';
import { useWizardExtras } from './WizardExtrasContext';
import { StepNav } from './StepNav';

const DAYS = Array.from({ length: 31 }, (_, i) => String(i + 1));

export function AgendamentoStep({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const extras = useWizardExtras();
  const [errors, setErrors] = useState<Record<string, string>>({});

  function validate(): boolean {
    const errs: Record<string, string> = {};
    const day = Number(extras.dayOfMonth);
    if (!extras.dayOfMonth || !Number.isInteger(day) || day < 1 || day > 31) {
      errs.dayOfMonth = 'Informe um dia entre 1 e 31.';
    }
    if (!extras.startDate.trim()) {
      errs.startDate = 'Data de início é obrigatória.';
    }
    if (extras.endDate.trim() && extras.startDate.trim() && extras.endDate < extras.startDate) {
      errs.endDate = 'Data de fim deve ser maior ou igual à data de início.';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function handleNext() {
    if (validate()) onNext();
    else window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <>
      <Card title="Agendamento da recorrência">
        <div className="grid grid-2">
          <Field label="Dia do mês" required error={errors.dayOfMonth} hint="Dia em que a nota será emitida (1–31)">
            <select
              className={`input${errors.dayOfMonth ? ' input--error' : ''}`}
              value={extras.dayOfMonth}
              onChange={(e) => extras.patch({ dayOfMonth: e.target.value })}
            >
              <option value="">Selecione...</option>
              {DAYS.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </Field>

          <Field label="Data de início" required error={errors.startDate}>
            <input
              type="date"
              className={`input${errors.startDate ? ' input--error' : ''}`}
              value={extras.startDate}
              onChange={(e) => extras.patch({ startDate: e.target.value })}
            />
          </Field>

          <Field label="Data de fim" error={errors.endDate} hint="Opcional — deixe em branco para recorrência sem fim">
            <input
              type="date"
              className={`input${errors.endDate ? ' input--error' : ''}`}
              value={extras.endDate}
              min={extras.startDate || undefined}
              onChange={(e) => extras.patch({ endDate: e.target.value })}
            />
          </Field>

          <div className="col-span-full">
            <Checkbox
              checked={extras.isActive}
              onChange={(v) => extras.patch({ isActive: v })}
              label="Recorrência ativa"
            />
          </div>
        </div>
      </Card>

      <StepNav onBack={onBack} onNext={handleNext} nextLabel="REVISAR →" />
    </>
  );
}

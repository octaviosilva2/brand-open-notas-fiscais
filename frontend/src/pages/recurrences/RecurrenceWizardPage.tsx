/** Orquestra o wizard de criação/edição de recorrência.
 *  Criação: montado pela rota `/recorrencias/nova`.
 *  Edição: `Wizard` é reutilizado pela `RecurrenceEditPage` via `editId`. */

import { useState } from 'react';
import { DpsProvider, useDps } from '../../state/DpsContext';
import { WizardExtrasProvider } from './wizard/WizardExtrasContext';
import { Stepper } from './wizard/Stepper';
import { PessoasStep } from './wizard/PessoasStep';
import { ServicoStep } from './wizard/ServicoStep';
import { ValoresStep } from './wizard/ValoresStep';
import { AgendamentoStep } from './wizard/AgendamentoStep';
import { RevisarStep } from './wizard/RevisarStep';
import { validatePessoas, validateServico, validateValores } from '../../validation/dpsSchema';
import type { Dps } from '../../types/dps';
import type { Errors } from '../../state/DpsContext';

const VALIDATORS: Array<((dps: Dps) => Errors) | null> = [
  validatePessoas,
  validateServico,
  validateValores,
  null, // Agendamento valida internamente
];
const LAST_STEP = 4;

export function Wizard({ editId }: { editId?: string }) {
  const { dps, setErrors } = useDps();
  const [current, setCurrent] = useState(0);
  const [showErrorBanner, setShowErrorBanner] = useState(false);

  function goNext() {
    const validator = VALIDATORS[current];
    const errs = validator ? validator(dps) : {};
    setErrors(errs);
    if (Object.keys(errs).length === 0) {
      setShowErrorBanner(false);
      setCurrent((c) => Math.min(LAST_STEP, c + 1));
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      setShowErrorBanner(true);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  function goBack() {
    setErrors({});
    setShowErrorBanner(false);
    setCurrent((c) => Math.max(0, c - 1));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function goTo(i: number) {
    if (i <= current) {
      setErrors({});
      setShowErrorBanner(false);
      setCurrent(i);
    }
  }

  const title = editId ? 'Editar recorrência' : 'Nova recorrência';

  return (
    <>
      <div className="page-head">
        <div className="page-title">{title}</div>
        <div className="breadcrumb">Recorrências <span>›</span> {title}</div>
      </div>

      <Stepper current={current} onSelect={goTo} />

      {showErrorBanner && (
        <div className="banner banner--warn">
          Há campos obrigatórios não preenchidos nesta etapa. Verifique os campos destacados.
        </div>
      )}

      {current === 0 && <PessoasStep onNext={goNext} />}
      {current === 1 && <ServicoStep onNext={goNext} onBack={goBack} />}
      {current === 2 && <ValoresStep onNext={goNext} onBack={goBack} />}
      {current === 3 && <AgendamentoStep onNext={goNext} onBack={goBack} />}
      {current === 4 && <RevisarStep onBack={goBack} editId={editId} />}
    </>
  );
}

export function RecurrenceWizardPage() {
  return (
    <DpsProvider>
      <WizardExtrasProvider>
        <Wizard />
      </WizardExtrasProvider>
    </DpsProvider>
  );
}

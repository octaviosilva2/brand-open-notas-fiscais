/** Edição de recorrência: carrega a recorrência, hidrata os contextos do wizard
 *  com os dados existentes e reutiliza o mesmo Wizard com editId. */

import { useParams } from 'react-router-dom';
import { useRecurrence } from '../../features/recurrences/hooks';
import { backendMessage } from '../../features/clients/errors';
import { parseDps } from '../../payload/parseDps';
import { DpsProvider } from '../../state/DpsContext';
import { WizardExtrasProvider } from './wizard/WizardExtrasContext';
import { Wizard } from './RecurrenceWizardPage';
import type { WizardExtras } from './wizard/WizardExtrasContext';

export function RecurrenceEditPage() {
  const { id = '' } = useParams();
  const { data: recurrence, isLoading, isError, error } = useRecurrence(id);

  if (isLoading) return <div className="list-state">Carregando recorrência...</div>;
  if (isError || !recurrence) {
    return (
      <div className="banner banner--warn">
        {backendMessage(error, 'Recorrência não encontrada.')}
      </div>
    );
  }

  const initialDps = parseDps(recurrence.inf_dps);
  const initialExtras: Partial<WizardExtras> = {
    clientId: recurrence.client_id,
    dayOfMonth: String(recurrence.day_of_month),
    startDate: recurrence.start_date,
    endDate: recurrence.end_date ?? '',
    isActive: recurrence.is_active,
  };

  return (
    <DpsProvider initialDps={initialDps}>
      <WizardExtrasProvider initialExtras={initialExtras}>
        <Wizard editId={id} />
      </WizardExtrasProvider>
    </DpsProvider>
  );
}

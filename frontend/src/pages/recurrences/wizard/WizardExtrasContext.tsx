/**
 * Estado extra do wizard de recorrência que NÃO faz parte do `Dps`/`inf_dps`:
 * o `clientId` vinculado (link) e os campos de agendamento da recorrência
 * (`day_of_month`, `start_date`, `end_date`, `is_active`). Mantido em um
 * contexto separado para não poluir o objeto `Dps` (que vira o snapshot
 * `inf_dps`).
 */

import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

export interface WizardExtras {
  clientId: string | null;
  dayOfMonth: string; // string para binding com <input>; convertido no submit
  startDate: string; // AAAA-MM-DD
  endDate: string; // AAAA-MM-DD ou ''
  isActive: boolean;
}

export interface WizardExtrasContextValue extends WizardExtras {
  setClientId: (id: string | null) => void;
  patch: (values: Partial<WizardExtras>) => void;
  reset: () => void;
}

function emptyExtras(): WizardExtras {
  return { clientId: null, dayOfMonth: '', startDate: '', endDate: '', isActive: true };
}

const WizardExtrasContext = createContext<WizardExtrasContextValue | null>(null);

export function WizardExtrasProvider({ children, initialExtras }: { children: ReactNode; initialExtras?: Partial<WizardExtras> }) {
  const [extras, setExtras] = useState<WizardExtras>(() => ({ ...emptyExtras(), ...initialExtras }));

  const value = useMemo<WizardExtrasContextValue>(
    () => ({
      ...extras,
      setClientId: (clientId) => setExtras((e) => ({ ...e, clientId })),
      patch: (values) => setExtras((e) => ({ ...e, ...values })),
      reset: () => setExtras(emptyExtras()),
    }),
    [extras],
  );

  return <WizardExtrasContext.Provider value={value}>{children}</WizardExtrasContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useWizardExtras(): WizardExtrasContextValue {
  const ctx = useContext(WizardExtrasContext);
  if (!ctx) throw new Error('useWizardExtras deve ser usado dentro de <WizardExtrasProvider>');
  return ctx;
}

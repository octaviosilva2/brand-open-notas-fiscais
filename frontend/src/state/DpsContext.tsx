/**
 * Estado global do formulário da DPS: um único objeto `Dps` mutado de forma
 * imutável via `update(draft => ...)` (clone + mutação, sem dependências extras).
 * Também guarda o mapa de erros de validação por campo (chave = caminho do campo).
 */

import { createContext, useCallback, useContext, useMemo, useReducer, type ReactNode } from 'react';
import { type Dps, emptyDps } from '../types/dps';

export type Errors = Record<string, string>;

interface DpsState {
  dps: Dps;
  errors: Errors;
}

type Action =
  | { type: 'update'; mutator: (draft: Dps) => void }
  | { type: 'setErrors'; errors: Errors }
  | { type: 'clearError'; key: string }
  | { type: 'reset' };

function reducer(state: DpsState, action: Action): DpsState {
  switch (action.type) {
    case 'update': {
      const draft = structuredClone(state.dps);
      action.mutator(draft);
      return { ...state, dps: draft };
    }
    case 'setErrors':
      return { ...state, errors: action.errors };
    case 'clearError': {
      if (!state.errors[action.key]) return state;
      const next = { ...state.errors };
      delete next[action.key];
      return { ...state, errors: next };
    }
    case 'reset':
      return { dps: emptyDps(), errors: {} };
    default:
      return state;
  }
}

interface DpsContextValue {
  dps: Dps;
  errors: Errors;
  /** Atualiza o estado mutando um clone do objeto Dps. */
  update: (mutator: (draft: Dps) => void) => void;
  setErrors: (errors: Errors) => void;
  /** Limpa o erro de um campo (chamado ao editar). */
  clearError: (key: string) => void;
  reset: () => void;
}

const DpsContext = createContext<DpsContextValue | null>(null);

export function DpsProvider({ children, initialDps }: { children: ReactNode; initialDps?: Dps }) {
  const [state, dispatch] = useReducer(reducer, undefined, () => ({ dps: initialDps ?? emptyDps(), errors: {} }));

  const update = useCallback((mutator: (draft: Dps) => void) => dispatch({ type: 'update', mutator }), []);
  const setErrors = useCallback((errors: Errors) => dispatch({ type: 'setErrors', errors }), []);
  const clearError = useCallback((key: string) => dispatch({ type: 'clearError', key }), []);
  const reset = useCallback(() => dispatch({ type: 'reset' }), []);

  const value = useMemo<DpsContextValue>(
    () => ({ dps: state.dps, errors: state.errors, update, setErrors, clearError, reset }),
    [state.dps, state.errors, update, setErrors, clearError, reset],
  );

  return <DpsContext.Provider value={value}>{children}</DpsContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useDps(): DpsContextValue {
  const ctx = useContext(DpsContext);
  if (!ctx) throw new Error('useDps deve ser usado dentro de <DpsProvider>');
  return ctx;
}

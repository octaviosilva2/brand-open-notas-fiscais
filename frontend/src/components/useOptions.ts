import { useEffect, useState } from 'react';
import type { Option } from '../api/lookups';

/**
 * Carrega as opções de um lookup (município/país/lista/NBS) uma vez.
 * Hoje os loaders retornam mock; quando virarem chamadas de API, este hook
 * continua funcionando sem alteração.
 */
export function useOptions(loader: (q: string) => Promise<Option[]>): Option[] {
  const [options, setOptions] = useState<Option[]>([]);
  useEffect(() => {
    let active = true;
    loader('').then((opts) => { if (active) setOptions(opts); });
    return () => { active = false; };
  }, [loader]);
  return options;
}

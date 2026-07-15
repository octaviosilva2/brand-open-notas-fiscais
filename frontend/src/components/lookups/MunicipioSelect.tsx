/** Seletor de município com busca debounced contra /lookups/municipios.
 *
 * O valor controlado é o código IBGE (7 dígitos). Exibe um input de busca e
 * uma lista de opções; ao escolher, fixa value/label. */

import { useEffect, useRef, useState } from 'react';
import { searchMunicipiosApi, type Option } from '../../api/lookups';
import { TextInput } from '../primitives';

interface Props {
  /** Código IBGE selecionado. */
  value: string;
  onChange: (value: string) => void;
  error?: boolean;
  /** Rótulo inicial (ex.: ao editar um cliente já com município). */
  initialLabel?: string;
}

export function MunicipioSelect({ value, onChange, error, initialLabel }: Props) {
  // `initialLabel` é lido só na montagem. A página de edição monta o formulário
  // apenas depois de o cliente carregar, então o rótulo já chega correto; quando
  // ele muda (ex.: trocar de cliente), o componente é remontado via `key` no pai.
  const [query, setQuery] = useState(initialLabel ?? '');
  const [options, setOptions] = useState<Option[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounce = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!open) return;
    if (debounce.current) clearTimeout(debounce.current);
    debounce.current = setTimeout(() => {
      const q = query.trim();
      if (q.length < 2) {
        setOptions([]);
        return;
      }
      setLoading(true);
      searchMunicipiosApi(q)
        .then((opts) => setOptions(opts))
        .catch(() => setOptions([]))
        .finally(() => setLoading(false));
    }, 300);
    return () => {
      if (debounce.current) clearTimeout(debounce.current);
    };
  }, [query, open]);

  function select(opt: Option) {
    onChange(opt.value);
    setQuery(opt.label);
    setOpen(false);
  }

  return (
    <div className="municipio-select">
      <TextInput
        value={query}
        error={error}
        placeholder="Digite o nome do município..."
        onChange={(v) => {
          setQuery(v);
          setOpen(true);
          if (value) onChange('');
        }}
      />
      {open && (query.trim().length >= 2 || loading) && (
        <ul className="municipio-select__list">
          {loading && <li className="municipio-select__empty">Buscando...</li>}
          {!loading && options.length === 0 && (
            <li className="municipio-select__empty">Nenhum município encontrado.</li>
          )}
          {!loading &&
            options.map((opt) => (
              <li key={opt.value}>
                <button
                  type="button"
                  className="municipio-select__option"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    select(opt);
                  }}
                >
                  {opt.label}
                </button>
              </li>
            ))}
        </ul>
      )}
    </div>
  );
}

/** Modalidade "Documento" da dedução/redução: lista repetível de documentos
 *  (docDedRed), cada um com choice do tipo de documento. Ver `campos.md`. */

import { type DocDedRed, emptyDocDedRed } from '../types/dps';
import type { Errors } from '../state/DpsContext';
import { Field, TextInput, Select, MoneyInput } from './primitives';

const TP_DEDRED_OPTS = [
  ...['01', '02', '03', '04', '05', '06', '07', '08'].map((v) => ({ value: v, label: v })),
  { value: '99', label: '99 - Outros' },
];

const DOC_TIPO_OPTS = [
  { value: 'NFSe', label: 'NFS-e (chave)' },
  { value: 'NFe', label: 'NF-e (chave)' },
  { value: 'NFSeMun', label: 'NFS-e municipal' },
  { value: 'NFNFS', label: 'NF/NFS não eletrônica' },
  { value: 'docFiscal', label: 'Outro documento fiscal' },
  { value: 'docNaoFiscal', label: 'Outro documento não fiscal' },
];

interface Props {
  documentos: DocDedRed[];
  update: (mutator: (docs: DocDedRed[]) => void) => void;
  errors: Errors;
}

export function DocDedRedList({ documentos, update, errors }: Props) {
  return (
    <div style={{ marginTop: 'var(--space-3)' }}>
      {documentos.map((doc, i) => {
        const k = (field: string) => `valores.documentos.${i}.${field}`;
        return (
          <div key={i} className="card" style={{ background: 'var(--color-bg)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
              <strong>Documento {i + 1}</strong>
              <button type="button" className="btn-danger-link" onClick={() => update((docs) => { docs.splice(i, 1); })}>
                Remover
              </button>
            </div>
            <div className="grid grid-3">
              <Field label="Tipo da dedução/redução" required error={errors[k('tpDedRed')]}>
                <Select value={doc.tpDedRed} options={TP_DEDRED_OPTS} error={!!errors[k('tpDedRed')]} onChange={(v) => update((docs) => { docs[i].tpDedRed = v; })} />
              </Field>
              {doc.tpDedRed === '99' && (
                <Field label="Descrição (tipo 99)" className="col-span-2">
                  <TextInput value={doc.xDescOutDed} maxLength={150} onChange={(v) => update((docs) => { docs[i].xDescOutDed = v; })} />
                </Field>
              )}
              <Field label="Data de emissão" required error={errors[k('dtEmiDoc')]}>
                <TextInput type="date" value={doc.dtEmiDoc} error={!!errors[k('dtEmiDoc')]} onChange={(v) => update((docs) => { docs[i].dtEmiDoc = v; })} />
              </Field>
              <Field label="Valor total dedutível" required error={errors[k('vDedutivelRedutivel')]}>
                <MoneyInput value={doc.vDedutivelRedutivel} error={!!errors[k('vDedutivelRedutivel')]} onChange={(v) => update((docs) => { docs[i].vDedutivelRedutivel = v; })} />
              </Field>
              <Field label="Valor usado nesta NFS-e" required error={errors[k('vDeducaoReducao')]}>
                <MoneyInput value={doc.vDeducaoReducao} error={!!errors[k('vDeducaoReducao')]} onChange={(v) => update((docs) => { docs[i].vDeducaoReducao = v; })} />
              </Field>

              <Field label="Tipo de documento" required className="col-span-full">
                <Select value={doc.docTipo} options={DOC_TIPO_OPTS} onChange={(v) => update((docs) => { docs[i].docTipo = v as DocDedRed['docTipo']; })} />
              </Field>

              {doc.docTipo === 'NFSe' && (
                <Field label="Chave NFS-e" className="col-span-full">
                  <TextInput value={doc.chNFSe} maxLength={50} onChange={(v) => update((docs) => { docs[i].chNFSe = v; })} />
                </Field>
              )}
              {doc.docTipo === 'NFe' && (
                <Field label="Chave NF-e" className="col-span-full">
                  <TextInput value={doc.chNFe} maxLength={44} onChange={(v) => update((docs) => { docs[i].chNFe = v; })} />
                </Field>
              )}
              {doc.docTipo === 'NFSeMun' && (
                <>
                  <Field label="Cód. município">
                    <TextInput value={doc.cMunNFSeMun} maxLength={7} onChange={(v) => update((docs) => { docs[i].cMunNFSeMun = v; })} />
                  </Field>
                  <Field label="Número">
                    <TextInput value={doc.nNFSeMun} maxLength={15} onChange={(v) => update((docs) => { docs[i].nNFSeMun = v; })} />
                  </Field>
                  <Field label="Cód. verificação">
                    <TextInput value={doc.cVerifNFSeMun} maxLength={9} onChange={(v) => update((docs) => { docs[i].cVerifNFSeMun = v; })} />
                  </Field>
                </>
              )}
              {doc.docTipo === 'NFNFS' && (
                <>
                  <Field label="Número">
                    <TextInput value={doc.nNFS} onChange={(v) => update((docs) => { docs[i].nNFS = v; })} />
                  </Field>
                  <Field label="Modelo">
                    <TextInput value={doc.modNFS} onChange={(v) => update((docs) => { docs[i].modNFS = v; })} />
                  </Field>
                  <Field label="Série">
                    <TextInput value={doc.serieNFS} onChange={(v) => update((docs) => { docs[i].serieNFS = v; })} />
                  </Field>
                </>
              )}
              {doc.docTipo === 'docFiscal' && (
                <Field label="Nº do documento fiscal" className="col-span-full">
                  <TextInput value={doc.nDocFisc} maxLength={255} onChange={(v) => update((docs) => { docs[i].nDocFisc = v; })} />
                </Field>
              )}
              {doc.docTipo === 'docNaoFiscal' && (
                <Field label="Nº do documento não fiscal" className="col-span-full">
                  <TextInput value={doc.nDoc} maxLength={255} onChange={(v) => update((docs) => { docs[i].nDoc = v; })} />
                </Field>
              )}
            </div>
          </div>
        );
      })}

      {errors['valores.documentos'] && <span className="field__error">{errors['valores.documentos']}</span>}

      <button type="button" className="btn btn-outline" onClick={() => update((docs) => { docs.push(emptyDocDedRed()); })}>
        + Adicionar documento
      </button>
    </div>
  );
}

import { useDps } from '../../../state/DpsContext';
import { searchMunicipios, searchPaises, searchListaServico, searchNBS } from '../../../api/lookups';
import { Card, Field, TextInput, TextArea, Select, RadioGroup, ReadOnlyField } from '../../../components/primitives';
import { EndNacFields } from '../../../components/AddressFields';
import { StepNav } from './StepNav';
import { useOptions } from '../../../components/useOptions';

const NATUREZA_OPTS = [
  { value: '1', label: '1 - Operação tributável' },
  { value: '2', label: '2 - Imunidade' },
  { value: '3', label: '3 - Exportação de serviço' },
  { value: '4', label: '4 - Não incidência' },
];

const RETENCAO_OPTS = [
  { value: '1', label: '1 - Não retido' },
  { value: '2', label: '2 - Retido pelo tomador' },
  { value: '3', label: '3 - Retido pelo intermediário' },
];

const DETALHE_OPTS = [
  { value: 'naoInformar', label: 'Não informar' },
  { value: 'obra', label: 'Informar dados de Obra de Construção Civil' },
  { value: 'imovel', label: 'Informar dados do Imóvel' },
  { value: 'evento', label: 'Informar dados de Atividade de Evento' },
];

export function ServicoStep({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { dps, update, errors, clearError } = useDps();
  const s = dps.serv;

  const paises = useOptions(searchPaises);
  const municipios = useOptions(searchMunicipios);
  const listaServico = useOptions(searchListaServico);
  const nbs = useOptions(searchNBS);

  const isBrasil = s.cPaisPrestacao === 'BRA' || s.cPaisPrestacao === '';
  const municipioLabel = municipios.find((m) => m.value === s.cLocPrestacao)?.label ?? '';

  return (
    <>
      <Card title="Serviço">
        <div className="grid grid-2">
          <Field label="País da prestação" required error={errors['serv.cPaisPrestacao']}>
            <Select
              value={s.cPaisPrestacao || 'BRA'}
              options={paises}
              error={!!errors['serv.cPaisPrestacao']}
              onChange={(v) => {
                update((d) => {
                  d.serv.cPaisPrestacao = v;
                  d.serv.locPrestTipo = v === 'BRA' ? 'municipio' : 'pais';
                });
                clearError('serv.cPaisPrestacao');
              }}
            />
          </Field>

          {isBrasil && (
            <Field label="Município da prestação" required error={errors['serv.cLocPrestacao']}>
              <Select
                value={s.cLocPrestacao}
                options={municipios}
                error={!!errors['serv.cLocPrestacao']}
                onChange={(v) => { update((d) => { d.serv.cLocPrestacao = v; }); clearError('serv.cLocPrestacao'); }}
              />
            </Field>
          )}

          <Field label="Natureza da operação" required error={errors['serv.tribISSQN']}>
            <Select
              value={s.tribISSQN}
              options={NATUREZA_OPTS}
              error={!!errors['serv.tribISSQN']}
              onChange={(v) => { update((d) => { d.serv.tribISSQN = v; }); clearError('serv.tribISSQN'); }}
            />
          </Field>

          <Field label="Tipo de retenção ISSQN" required error={errors['serv.tpRetISSQN']}>
            <Select
              value={s.tpRetISSQN}
              options={RETENCAO_OPTS}
              error={!!errors['serv.tpRetISSQN']}
              onChange={(v) => { update((d) => { d.serv.tpRetISSQN = v; }); clearError('serv.tpRetISSQN'); }}
            />
          </Field>

          <Field label="Lista de Serviço" required error={errors['serv.cTribNac']} className="col-span-full">
            <Select
              value={s.cTribNac}
              options={listaServico}
              error={!!errors['serv.cTribNac']}
              onChange={(v) => { update((d) => { d.serv.cTribNac = v; }); clearError('serv.cTribNac'); }}
            />
          </Field>

          <Field label="Tributação municipal">
            <TextInput value={s.cTribMun} maxLength={3} onChange={(v) => update((d) => { d.serv.cTribMun = v; })} />
          </Field>

          <Field label="NBS" required error={errors['serv.cNBS']}>
            <Select
              value={s.cNBS}
              options={nbs}
              error={!!errors['serv.cNBS']}
              onChange={(v) => { update((d) => { d.serv.cNBS = v; }); clearError('serv.cNBS'); }}
            />
          </Field>

          <div className="col-span-full">
            <ReadOnlyField
              label="Município de incidência ISSQN"
              value={municipioLabel}
              hint="Preenchido automaticamente a partir do local de prestação"
            />
          </div>

          <Field label="Descrição detalhada do serviço" required error={errors['serv.xDescServ']} className="col-span-full">
            <TextArea
              value={s.xDescServ}
              maxLength={1000}
              rows={5}
              placeholder="Descreva detalhadamente o serviço prestado..."
              error={!!errors['serv.xDescServ']}
              onChange={(v) => { update((d) => { d.serv.xDescServ = v; }); clearError('serv.xDescServ'); }}
            />
          </Field>
        </div>
      </Card>

      <Card title="Detalhes adicionais do serviço">
        <RadioGroup
          name="detalheAdicional"
          value={s.detalheAdicional}
          onChange={(v) => update((d) => { d.serv.detalheAdicional = v as typeof d.serv.detalheAdicional; })}
          options={DETALHE_OPTS}
        />

        {(s.detalheAdicional === 'obra' || s.detalheAdicional === 'imovel') && (
          <div className="grid grid-2" style={{ marginTop: 'var(--space-4)' }}>
            <Field label="Código da obra (CNO/CIB)" required error={errors['serv.obra.cobr']} className="col-span-full">
              <TextInput value={s.obra.cobr} onChange={(v) => { update((d) => { d.serv.obra.cobr = v; }); clearError('serv.obra.cobr'); }} error={!!errors['serv.obra.cobr']} />
            </Field>
            <div className="col-span-full">
              <EndNacFields
                end={s.obra.end}
                onField={(f, v) => update((d) => { d.serv.obra.end[f] = v; })}
                errors={errors}
                prefix="serv.obra.end"
              />
            </div>
          </div>
        )}

        {s.detalheAdicional === 'evento' && (
          <div className="grid grid-3" style={{ marginTop: 'var(--space-4)' }}>
            <Field label="Nome do evento" required error={errors['serv.evento.xNome']} className="col-span-full">
              <TextInput value={s.evento.xNome} onChange={(v) => { update((d) => { d.serv.evento.xNome = v; }); clearError('serv.evento.xNome'); }} error={!!errors['serv.evento.xNome']} />
            </Field>
            <Field label="Data de início" required error={errors['serv.evento.dataIni']}>
              <TextInput type="date" value={s.evento.dataIni} onChange={(v) => { update((d) => { d.serv.evento.dataIni = v; }); clearError('serv.evento.dataIni'); }} error={!!errors['serv.evento.dataIni']} />
            </Field>
            <Field label="Data de fim" required error={errors['serv.evento.dataFim']}>
              <TextInput type="date" value={s.evento.dataFim} onChange={(v) => { update((d) => { d.serv.evento.dataFim = v; }); clearError('serv.evento.dataFim'); }} error={!!errors['serv.evento.dataFim']} />
            </Field>
            <div className="col-span-full">
              <EndNacFields
                end={s.evento.end}
                onField={(f, v) => update((d) => { d.serv.evento.end[f] = v; })}
                errors={errors}
                prefix="serv.evento.end"
              />
            </div>
          </div>
        )}
      </Card>

      <Card title="Descrição e Informações Complementares">
        <div className="grid grid-2">
          <Field label="Número do documento de responsabilidade técnica">
            <TextInput value={s.idDocTec} maxLength={40} onChange={(v) => update((d) => { d.serv.idDocTec = v; })} />
          </Field>
          <Field label="Documento de referência">
            <TextInput value={s.docRef} maxLength={255} onChange={(v) => update((d) => { d.serv.docRef = v; })} />
          </Field>
          <Field label="Nº do pedido / ordem de compra / OS">
            <TextInput value={s.xPed} maxLength={60} onChange={(v) => update((d) => { d.serv.xPed = v; })} />
          </Field>
          <Field label="Item do pedido">
            <TextInput value={s.xItemPed} maxLength={60} onChange={(v) => update((d) => { d.serv.xItemPed = v; })} />
          </Field>
          <Field label="Informações complementares" className="col-span-full">
            <TextArea value={s.xInfComp} maxLength={2000} placeholder="Adicione informações extras relevantes..." onChange={(v) => update((d) => { d.serv.xInfComp = v; })} />
          </Field>
        </div>
      </Card>

      <StepNav onBack={onBack} onNext={onNext} />
    </>
  );
}

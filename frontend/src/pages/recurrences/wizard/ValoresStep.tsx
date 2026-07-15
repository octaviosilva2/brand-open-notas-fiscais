import { useDps } from '../../../state/DpsContext';
import { TABELA_ALIQUOTAS_SN } from '../../../api/lookups';
import { computeDerived, formatMoney } from '../../../calc/derived';
import { Card, Field, TextInput, Select, MoneyInput, ReadOnlyField } from '../../../components/primitives';
import { DocDedRedList } from '../../../components/DocDedRedList';
import { StepNav } from './StepNav';

const REGIME_ESP_OPTS = [
  { value: '0', label: 'Nenhum' },
  { value: '1', label: 'Ato Cooperado' },
  { value: '2', label: 'Estimativa' },
  { value: '3', label: 'Microempresa Municipal' },
  { value: '4', label: 'Notário ou Registrador' },
  { value: '5', label: 'Profissional Autônomo' },
  { value: '6', label: 'Sociedade de Profissionais' },
];

const DEDRED_OPTS = [
  { value: 'nenhuma', label: 'Não há dedução/redução' },
  { value: 'percentual', label: 'Percentual' },
  { value: 'valor', label: 'Valor' },
  { value: 'documento', label: 'Documento' },
];

const PISCOFINS_OPTS = [
  { value: 'nenhum', label: 'Nenhum' },
  { value: 'basica', label: 'Operação Tributável com Alíquota Básica' },
  { value: 'diferenciada', label: 'Operação Tributável com Alíquota Diferenciada' },
  { value: 'unidade', label: 'Operação Tributável com Alíquota por Unidade de Medida de Produto' },
];

export function ValoresStep({ onNext, onBack }: { onNext: () => void; onBack: () => void }) {
  const { dps, update, errors, clearError } = useDps();
  const v = dps.valores;
  const d = computeDerived(dps);

  return (
    <>
      <Card title="Valores">
        <div className="grid grid-2">
          <Field label="Valor total do serviço" required error={errors['valores.vServ']}>
            <MoneyInput value={v.vServ} error={!!errors['valores.vServ']} onChange={(val) => { update((x) => { x.valores.vServ = val; }); clearError('valores.vServ'); }} />
          </Field>
<Field label="Desconto incondicionado">
            <MoneyInput value={v.vDescIncond} onChange={(val) => update((x) => { x.valores.vDescIncond = val; })} />
          </Field>
          <Field label="Desconto condicionado">
            <MoneyInput value={v.vDescCond} onChange={(val) => update((x) => { x.valores.vDescCond = val; })} />
          </Field>
        </div>
      </Card>

      <Card title="Dedução/Redução à base de cálculo do ISSQN">
        <div className="grid grid-2">
          <Field label="Regime especial de tributação" required error={errors['prest.regEspTrib']}>
            <Select
              value={dps.prest.regEspTrib}
              options={REGIME_ESP_OPTS}
              error={!!errors['prest.regEspTrib']}
              onChange={(val) => { update((x) => { x.prest.regEspTrib = val; }); clearError('prest.regEspTrib'); }}
            />
          </Field>
          <Field label="Tipo de dedução/redução">
            <Select
              value={v.dedRedTipo}
              options={DEDRED_OPTS}
              placeholder="Selecione o tipo"
              onChange={(val) => update((x) => { x.valores.dedRedTipo = val as typeof x.valores.dedRedTipo; })}
            />
          </Field>
        </div>

        {v.dedRedTipo === 'percentual' && (
          <div className="grid grid-2" style={{ marginTop: 'var(--space-3)' }}>
            <Field label="Percentual de dedução/redução (%)" required error={errors['valores.pDR']}>
              <TextInput value={v.pDR} error={!!errors['valores.pDR']} onChange={(val) => { update((x) => { x.valores.pDR = val; }); clearError('valores.pDR'); }} />
            </Field>
          </div>
        )}
        {v.dedRedTipo === 'valor' && (
          <div className="grid grid-2" style={{ marginTop: 'var(--space-3)' }}>
            <Field label="Valor de dedução/redução" required error={errors['valores.vDR']}>
              <MoneyInput value={v.vDR} error={!!errors['valores.vDR']} onChange={(val) => { update((x) => { x.valores.vDR = val; }); clearError('valores.vDR'); }} />
            </Field>
          </div>
        )}
        {v.dedRedTipo === 'documento' && (
          <DocDedRedList
            documentos={v.documentos}
            update={(mutator) => update((x) => mutator(x.valores.documentos))}
            errors={errors}
          />
        )}
      </Card>

      <Card title="Cálculo do ISSQN">
        <Field label="Alíquota" hint="Optante do Simples: selecione a faixa/anexo do faturamento">
          <table className="table">
            <thead>
              <tr><th></th><th>Alíquota</th><th>Anexo</th><th>Faixa</th><th>RBT12</th></tr>
            </thead>
            <tbody>
              {TABELA_ALIQUOTAS_SN.map((row) => (
                <tr key={row.anexo} className={v.pAliq === row.pAliq ? 'selected' : ''}>
                  <td>
                    <input
                      type="radio"
                      name="aliquota"
                      checked={v.pAliq === row.pAliq}
                      onChange={() => update((x) => { x.valores.pAliq = row.pAliq; })}
                    />
                  </td>
                  <td>{row.pAliq} %</td>
                  <td>{row.anexo}</td>
                  <td>{row.faixa}</td>
                  <td>{row.rbt12}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Field>

        {dps.serv.tribISSQN === '3' && (
          <Field label="País do resultado (exportação)" className="col-span-2" required>
            <TextInput value={v.cPaisResult} maxLength={2} onChange={(val) => update((x) => { x.valores.cPaisResult = val; })} />
          </Field>
        )}
        {dps.serv.tribISSQN === '2' && (
          <Field label="Tipo de imunidade" className="col-span-2" required>
            <TextInput value={v.tpImunidade} maxLength={1} onChange={(val) => update((x) => { x.valores.tpImunidade = val; })} />
          </Field>
        )}

        <div className="grid grid-2" style={{ marginTop: 'var(--space-4)' }}>
          <ReadOnlyField label="Base de cálculo ISSQN" value={formatMoney(d.baseCalculo)} money />
          <ReadOnlyField label="Valor ISSQN" value={formatMoney(d.valorISSQN)} money />
        </div>
      </Card>

      <Card title="Tributação Federal">
        <Field label="Situação Tributária PIS/COFINS" required error={errors['valores.piscofins.situacao']}>
          <Select
            value={v.piscofins.situacao}
            options={PISCOFINS_OPTS}
            onChange={(val) => update((x) => { x.valores.piscofins.situacao = val as typeof x.valores.piscofins.situacao; })}
          />
        </Field>

        {v.piscofins.situacao !== 'nenhum' && (
          <div className="grid grid-3" style={{ marginTop: 'var(--space-3)' }}>
            <Field label="CST (00–09)" required error={errors['valores.piscofins.CST']}>
              <TextInput value={v.piscofins.CST} maxLength={2} error={!!errors['valores.piscofins.CST']} onChange={(val) => { update((x) => { x.valores.piscofins.CST = val; }); clearError('valores.piscofins.CST'); }} />
            </Field>
            <Field label="Base de cálculo PIS/COFINS">
              <MoneyInput value={v.piscofins.vBCPisCofins} onChange={(val) => update((x) => { x.valores.piscofins.vBCPisCofins = val; })} />
            </Field>
            <Field label="Tipo retenção PIS/COFINS">
              <TextInput value={v.piscofins.tpRetPisCofins} maxLength={1} onChange={(val) => update((x) => { x.valores.piscofins.tpRetPisCofins = val; })} />
            </Field>
            <Field label="Alíquota PIS (%)">
              <TextInput value={v.piscofins.pAliqPis} onChange={(val) => update((x) => { x.valores.piscofins.pAliqPis = val; })} />
            </Field>
            <Field label="Alíquota COFINS (%)">
              <TextInput value={v.piscofins.pAliqCofins} onChange={(val) => update((x) => { x.valores.piscofins.pAliqCofins = val; })} />
            </Field>
            <span />
            <Field label="Valor PIS">
              <MoneyInput value={v.piscofins.vPis} onChange={(val) => update((x) => { x.valores.piscofins.vPis = val; })} />
            </Field>
            <Field label="Valor COFINS">
              <MoneyInput value={v.piscofins.vCofins} onChange={(val) => update((x) => { x.valores.piscofins.vCofins = val; })} />
            </Field>
          </div>
        )}

        <div className="section">
          <h3 className="section__title">Outras Retenções</h3>
          <div className="grid grid-3">
            <Field label="Valor retido IRRF">
              <MoneyInput value={v.vRetIRRF} onChange={(val) => update((x) => { x.valores.vRetIRRF = val; })} />
            </Field>
            <Field label="Valor retido CSLL">
              <MoneyInput value={v.vRetCSLL} onChange={(val) => update((x) => { x.valores.vRetCSLL = val; })} />
            </Field>
            <Field label="Valor retido CP (INSS)">
              <MoneyInput value={v.vRetCP} onChange={(val) => update((x) => { x.valores.vRetCP = val; })} />
            </Field>
          </div>
        </div>

        <div className="grid grid-2" style={{ marginTop: 'var(--space-4)' }}>
          <ReadOnlyField label="Total de retenções" value={formatMoney(d.totalRetencoes)} money />
          <ReadOnlyField label="Valor líquido da DPS" value={formatMoney(d.valorLiquido)} money />
        </div>
      </Card>

      <StepNav onBack={onBack} onNext={onNext} nextLabel="REVISAR →" />
    </>
  );
}

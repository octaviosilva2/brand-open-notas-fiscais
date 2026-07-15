import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDps } from '../../../state/DpsContext';
import { searchMunicipios, searchPaises, searchListaServico } from '../../../api/lookups';
import { computeDerived, formatMoney, parseMoney } from '../../../calc/derived';
import { buildInfDps } from '../../../payload/buildInfDps';
import { useCreateRecurrence, useUpdateRecurrence } from '../../../features/recurrences/hooks';
import { backendMessage } from '../../../features/clients/errors';
import { Card } from '../../../components/primitives';
import { useOptions } from '../../../components/useOptions';
import { useWizardExtras } from './WizardExtrasContext';

const NATUREZA: Record<string, string> = { '1': 'Operação tributável', '2': 'Imunidade', '3': 'Exportação de serviço', '4': 'Não incidência' };
const RETENCAO: Record<string, string> = { '1': 'Não retido', '2': 'Retido pelo tomador', '3': 'Retido pelo intermediário' };
const REGIME: Record<string, string> = { '0': 'Nenhum', '1': 'Ato Cooperado', '2': 'Estimativa', '3': 'Microempresa Municipal', '4': 'Notário ou Registrador', '5': 'Profissional Autônomo', '6': 'Sociedade de Profissionais' };

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="kv__row">
      <span className="kv__k">{k}</span>
      <span className="kv__v">{v || '—'}</span>
    </div>
  );
}

function money(v: string) { return `R$ ${formatMoney(parseMoney(v))}`; }

export function RevisarStep({ onBack, editId }: { onBack: () => void; editId?: string }) {
  const navigate = useNavigate();
  const { dps, reset } = useDps();
  const extras = useWizardExtras();
  const der = computeDerived(dps);
  const create = useCreateRecurrence();
  const update = useUpdateRecurrence(editId ?? '');
  const [serverError, setServerError] = useState<string | null>(null);

  const municipios = useOptions(searchMunicipios);
  const paises = useOptions(searchPaises);
  const lista = useOptions(searchListaServico);

  const municipioLabel = municipios.find((m) => m.value === dps.serv.cLocPrestacao)?.label ?? '—';
  const paisLabel = paises.find((p) => p.value === (dps.serv.cPaisPrestacao || 'BRA'))?.label ?? '—';
  const listaLabel = lista.find((l) => l.value === dps.serv.cTribNac)?.label ?? dps.serv.cTribNac;

  const tomadorNome = dps.toma.tipo === 'brasil' ? dps.toma.brasil.xNome
    : dps.toma.tipo === 'exterior' ? dps.toma.exterior.xNome
    : 'Não informado';

  const isPending = editId ? update.isPending : create.isPending;

  async function salvar() {
    setServerError(null);
    try {
      const infDPS = buildInfDps(dps);
      const payload = {
        description: dps.serv.xDescServ,
        amount: parseMoney(dps.valores.vServ).toFixed(2),
        day_of_month: Number(extras.dayOfMonth),
        start_date: extras.startDate,
        end_date: extras.endDate.trim() || null,
        is_active: extras.isActive,
        inf_dps: infDPS,
      };

      if (editId) {
        await update.mutateAsync(payload);
        reset();
        extras.reset();
        navigate('/recorrencias', { state: { updated: true } });
      } else {
        await create.mutateAsync({ client_id: extras.clientId!, ...payload });
        reset();
        extras.reset();
        navigate('/recorrencias', { state: { created: true } });
      }
    } catch (err) {
      const msg = editId
        ? 'Não foi possível salvar as alterações.'
        : 'Não foi possível criar a recorrência.';
      setServerError(backendMessage(err, msg));
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  return (
    <>
      {serverError && <div className="banner banner--warn">{serverError}</div>}

      <div className="banner banner--info">
        Revise os dados antes de {editId ? 'salvar as alterações' : 'criar a recorrência'}. Ao confirmar, é criada uma recorrência
        que servirá de molde para a emissão de cada nota. Os campos calculados (base, ISSQN,
        retenções, líquido) não entram no XML — são calculados pelo sistema na emissão.
      </div>

      <Card title="Snapshot da DPS (molde da recorrência)">
        <div className="kv">
          <Row k="Tomador" v={tomadorNome} />
          <Row k="Natureza da operação" v={NATUREZA[dps.serv.tribISSQN] ?? '—'} />
          <Row k="CTN" v={dps.serv.cTribNac} />
          <Row k="Lista de Serviço" v={listaLabel} />
          <Row k="País" v={paisLabel} />
          <Row k="Município da prestação" v={municipioLabel} />
          <Row k="Município de incidência" v={municipioLabel} />
          <Row k="Regime especial de tributação" v={REGIME[dps.prest.regEspTrib] ?? '—'} />
          <Row k="Tipo de retenção" v={RETENCAO[dps.serv.tpRetISSQN] ?? '—'} />
        </div>
      </Card>

      <Card title="Valores">
        <div className="kv">
          <Row k="Valor total do serviço" v={money(dps.valores.vServ)} />
          <Row k="Desconto incondicionado" v={money(dps.valores.vDescIncond)} />
          <Row k="Desconto condicionado" v={money(dps.valores.vDescCond)} />
          <Row k="Total deduções/reduções" v={`R$ ${formatMoney(der.totalDeducoes)}`} />
          <Row k="Base de cálculo ISSQN" v={`R$ ${formatMoney(der.baseCalculo)}`} />
          <Row k="Alíquota ISSQN" v={dps.valores.pAliq ? `${dps.valores.pAliq} %` : '—'} />
          <Row k="Valor ISSQN" v={`R$ ${formatMoney(der.valorISSQN)}`} />
          <Row k="Valor PIS" v={money(dps.valores.piscofins.vPis)} />
          <Row k="Valor COFINS" v={money(dps.valores.piscofins.vCofins)} />
          <Row k="Total retenções" v={`R$ ${formatMoney(der.totalRetencoes)}`} />
          <Row k="Valor líquido" v={`R$ ${formatMoney(der.valorLiquido)}`} />
        </div>
      </Card>

      <Card title="Agendamento">
        <div className="kv">
          <Row k="Dia do mês" v={extras.dayOfMonth} />
          <Row k="Data de início" v={extras.startDate} />
          <Row k="Data de fim" v={extras.endDate || 'Sem fim'} />
          <Row k="Ativa" v={extras.isActive ? 'Sim' : 'Não'} />
        </div>
      </Card>

      <div className="step-nav">
        <button type="button" className="btn btn-outline" onClick={onBack}>← VOLTAR</button>
        <button type="button" className="btn btn-primary" onClick={salvar} disabled={isPending}>
          {isPending
            ? (editId ? 'Salvando...' : 'Criando...')
            : (editId ? 'Salvar alterações' : 'Criar recorrência')}
        </button>
      </div>
    </>
  );
}

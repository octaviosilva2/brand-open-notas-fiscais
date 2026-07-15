import { useState } from 'react';
import { useDps } from '../../../state/DpsContext';
import { PersonFields } from '../../../components/PersonFields';
import { ClientPicker } from '../../../components/clients/ClientPicker';
import type { Client } from '../../../features/clients/types';
import { useWizardExtras } from './WizardExtrasContext';
import { StepNav } from './StepNav';

/** Pré-preenche o snapshot do tomador (`dps.toma.brasil`) a partir de um Client.
 *  O documento do cliente já vem só com dígitos; o tipo é dado por `document_type`. */
function fillTomadorFromClient(toma: import('../../../types/dps').Pessoa, c: Client) {
  toma.tipo = 'brasil';
  const b = toma.brasil;
  b.docType = c.document_type;
  b.doc = c.document;
  b.xNome = c.name;
  b.IM = c.municipal_registration ?? '';
  b.fone = c.phone ?? '';
  b.email = c.email ?? '';
  const hasAddress = !!(c.zip_code || c.street || c.number || c.neighborhood || c.ibge_city_code);
  b.informarEndereco = hasAddress;
  b.end.CEP = c.zip_code ?? '';
  b.end.cMun = c.ibge_city_code ?? '';
  b.end.xLgr = c.street ?? '';
  b.end.nro = c.number ?? '';
  b.end.xCpl = c.complement ?? '';
  b.end.xBairro = c.neighborhood ?? '';
}

export function PessoasStep({ onNext }: { onNext: () => void }) {
  const { dps, update, errors } = useDps();
  const extras = useWizardExtras();
  const [clientError, setClientError] = useState<string | undefined>(undefined);

  function handlePick(c: Client) {
    extras.setClientId(c.id);
    setClientError(undefined);
    update((d) => fillTomadorFromClient(d.toma, c));
  }

  function handleNext() {
    if (!extras.clientId) {
      setClientError('Selecione ou crie um cliente para continuar.');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    onNext();
  }

  return (
    <>
      <ClientPicker selectedClientId={extras.clientId} onPick={handlePick} error={clientError} />

      <PersonFields
        title="Dados do Tomador do Serviço"
        naoInformadoLabel="Tomador não informado"
        pessoa={dps.toma}
        update={(mutator) => update((d) => mutator(d.toma))}
        errors={errors}
        prefix="toma"
      />

      <PersonFields
        title="Dados do Intermediário do Serviço"
        naoInformadoLabel="Intermediário não informado"
        pessoa={dps.interm}
        update={(mutator) => update((d) => mutator(d.interm))}
        errors={errors}
        prefix="interm"
      />

      <StepNav onNext={handleNext} />
    </>
  );
}

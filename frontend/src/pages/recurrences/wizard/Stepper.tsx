const STEPS = ['Pessoas', 'Serviço', 'Valores', 'Agendamento', 'Revisar'] as const;

interface StepperProps {
  current: number;
  onSelect: (index: number) => void;
}

export function Stepper({ current, onSelect }: StepperProps) {
  return (
    <nav className="stepper" aria-label="Etapas">
      {STEPS.map((label, i) => {
        const state = i === current ? 'step--active' : i < current ? 'step--done' : '';
        return (
          <button key={label} type="button" className={`step ${state}`} onClick={() => onSelect(i)}>
            <span className="step__num">{i < current ? '✓' : i + 1}</span>
            {label}
          </button>
        );
      })}
    </nav>
  );
}

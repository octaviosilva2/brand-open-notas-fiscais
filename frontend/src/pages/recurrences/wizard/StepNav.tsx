interface StepNavProps {
  onBack?: () => void;
  onNext?: () => void;
  nextLabel?: string;
  backLabel?: string;
  nextDisabled?: boolean;
}

export function StepNav({ onBack, onNext, nextLabel = 'AVANÇAR →', backLabel = '← VOLTAR', nextDisabled }: StepNavProps) {
  return (
    <div className="step-nav">
      {onBack ? (
        <button type="button" className="btn btn-outline" onClick={onBack}>{backLabel}</button>
      ) : (
        <span />
      )}
      {onNext && (
        <button type="button" className="btn btn-primary" onClick={onNext} disabled={nextDisabled}>
          {nextLabel}
        </button>
      )}
    </div>
  );
}

class PipelineError(Exception):
    """Errore funzionale della pipeline."""


class ApprovalRequiredError(PipelineError):
    """Lo stage richiede intervento utente."""


class ProviderError(PipelineError):
    """Errore da provider esterno."""

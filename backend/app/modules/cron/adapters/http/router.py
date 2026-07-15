# app/modules/cron/adapters/http/router.py
from datetime import date

from fastapi import APIRouter, Depends

from app.modules.cron.adapters.http.dependencies import validate_cron_auth
from app.modules.cron.adapters.http.schemas import CronResultSchema
from app.modules.cron.application.use_cases.cron_runner import CronRunner

router = APIRouter(dependencies=[Depends(validate_cron_auth)])


@router.post("/run", response_model=CronResultSchema)
async def run_cron() -> CronResultSchema:
    """Dispara o processamento de todas as recorrências devidas na data de hoje."""
    runner = CronRunner()
    result = await runner.run(date.today())
    return CronResultSchema(
        date=result.date,
        total=result.total,
        success=result.success,
        error=result.error,
        results=[
            {
                "recurrence_id": r.recurrence_id,
                "client_name": r.client_name,
                "invoice_id": r.invoice_id,
                "ok": r.ok,
                "nf_number": r.nf_number,
                "pdf_url": r.pdf_url,
                "error_message": r.error_message,
            }
            for r in result.results
        ],
    )

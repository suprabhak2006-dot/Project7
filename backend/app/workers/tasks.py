import asyncio
from backend.app.workers.celery_app import celery_app
from backend.app.db.session import AsyncSessionLocal
from backend.app.services.pipeline import ForensicPipeline

@celery_app.task(bind=True, name="tasks.process_forensic_evidence")
def process_forensic_evidence_task(self, analysis_id: int):
    """
    Celery background worker task for executing heavy forensic pipeline.
    """
    print(f"[*] Celery Worker starting analysis ID: {analysis_id}")
    
    async def _run():
        async with AsyncSessionLocal() as session:
            pipeline = ForensicPipeline(session)
            return await pipeline.execute_analysis(analysis_id)

    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    result = loop.run_until_complete(_run())
    print(f"[+] Celery Worker completed analysis ID: {analysis_id}")
    return {"status": "SUCCESS", "analysis_id": analysis_id, "score": result.final_score}

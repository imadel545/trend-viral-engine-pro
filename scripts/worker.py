"""
Worker process to execute Prefect flows.
"""

import asyncio

from loguru import logger
from prefect.deployments import run_deployment

from scripts.flows.main_flows import ingestion_flow


async def run_worker():
    """Run Prefect worker."""
    logger.info("Starting Prefect worker...")

    # In production, would use proper Prefect agent
    # For development, run flows directly
    try:
        while True:
            logger.info("Running ingestion flow...")
            await ingestion_flow()

            # Wait 10 minutes
            await asyncio.sleep(600)

    except KeyboardInterrupt:
        logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(run_worker())

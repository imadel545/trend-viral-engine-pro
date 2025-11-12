"""
Prefect deployment configuration.
"""

from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

from scripts.flows.main_flows import (
    content_generation_flow,
    feedback_processing_flow,
    ingestion_flow,
    training_flow,
)

# Ingestion deployment - runs every 10 minutes
ingestion_deployment = Deployment.build_from_flow(
    flow=ingestion_flow,
    name="ingestion-every-10min",
    schedule=CronSchedule(cron="*/10 * * * *"),
    work_queue_name="default",
    tags=["ingestion", "data-collection"],
)

# Content generation deployment - runs 3 times daily
content_generation_deployment = Deployment.build_from_flow(
    flow=content_generation_flow,
    name="content-generation-daily",
    schedule=CronSchedule(cron="0 6,12,18 * * *"),  # 6am, 12pm, 6pm
    work_queue_name="default",
    tags=["generation", "content"],
)

# Feedback processing deployment - runs nightly
feedback_deployment = Deployment.build_from_flow(
    flow=feedback_processing_flow,
    name="feedback-processing-nightly",
    schedule=CronSchedule(cron="0 2 * * *"),  # 2am
    work_queue_name="default",
    tags=["feedback", "training"],
)

# Training deployment (optional - triggered by feedback or manual)
training_deployment = Deployment.build_from_flow(
    flow=training_flow,
    name="training-on-demand",
    schedule=None,  # Triggered by feedback_processing_flow or manually
    work_queue_name="default",
    tags=["training", "ml"],
)


if __name__ == "__main__":
    # Apply deployments
    ingestion_deployment.apply()
    content_generation_deployment.apply()
    feedback_deployment.apply()
    training_deployment.apply()

    print("✅ Deployments created successfully!")
    print("\nDeployments:")
    print("  - ingestion-every-10min: Every 10 minutes")
    print("  - content-generation-daily: 3x daily (6am, 12pm, 6pm)")
    print("  - feedback-processing-nightly: Daily at 2am (auto-triggers training)")
    print("  - training-on-demand: Manual/automatic trigger only")

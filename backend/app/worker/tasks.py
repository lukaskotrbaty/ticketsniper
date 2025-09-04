import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from celery import shared_task
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

import smtplib
from app.db.session import SyncSessionLocal
from app.db.models.route import MonitoredRoute, RouteStatusEnum
from app.db.models.user import User
from app.services.regiojet_checker_service import check_route_availability_sync
from app.services.email_service import _send_email_sync
from app.services.regiojet_data_service import _get_locations_from_cache_sync
from app.db.crud.crud_route import deactivate_route_sync, expire_route_sync, get_verified_route_subscribers
from typing import Dict, Any, List


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PRAGUE_TZ = ZoneInfo("Europe/Prague")

# --- schedule_route_checks changed to synchronous ---
@shared_task # Removed bind=True as it's not needed for sync task without self usage
def schedule_route_checks(): # Changed to sync def
    """
    Periodically fetches active routes and schedules individual checks.
    Updates last_checked_at for informational purposes.
    Uses SYNCHRONOUS DB session.
    """
    logger.info("Task schedule_route_checks starting...") # More specific log
    routes_to_check_ids = []
    db: Session | None = None
    try:
        db = SyncSessionLocal() # Create sync session
        # Select active routes using sync session
        stmt = select(MonitoredRoute).where(MonitoredRoute.status == RouteStatusEnum.MONITORING)
        active_routes = db.execute(stmt).scalars().all() # Sync execution

        if not active_routes:
            logger.info("Task schedule_route_checks: No routes in MONITORING state found.")
            return # Return here, finally block will close session

        logger.info(f"Task schedule_route_checks: Found {len(active_routes)} routes in MONITORING state.")

        # Update last_checked_at and collect IDs
        now = datetime.now()
        for route in active_routes:
            route.last_checked_at = now
            db.add(route)
            routes_to_check_ids.append(route.id)

        db.commit() # Sync commit

        # Schedule individual ASYNC checks after successful commit
        for route_id in routes_to_check_ids:
            # Still call the check_single_route task
            check_single_route.delay(route_id)

        logger.info(f"Task schedule_route_checks: Scheduled checks for {len(routes_to_check_ids)} routes.")

    except Exception as e:
        logger.exception(f"Error in schedule_route_checks: {e}")
        if db:
             db.rollback() # Rollback on error
        # Consider adding retry logic or specific error handling if needed
    finally:
        if db:
            db.close() # Ensure session is closed


# --- check_single_route changed to synchronous ---
@shared_task # Removed bind=True and max_retries for sync version (retry needs different handling)
def check_single_route(route_id: int): # Changed to sync def, removed self
    """
    Checks availability for a single route using RegiojetCheckerService.
    Converts UTC times to local time (Europe/Prague) for notifications.
    (Task 13 will add notification logic here)
    """
    logger.info(f"Task check_single_route starting for route_id: {route_id}")
    db: Session | None = None
    status = "ERROR" # Default status
    result_details: Dict[str, Any] | None = None
    error_message: str | None = None

    try:
        db = SyncSessionLocal() # Use sync session
        # Fetch the route details
        db_route = db.get(MonitoredRoute, route_id) # Sync get
        if not db_route:
            logger.warning(f"Task check_single_route: MonitoredRoute with id {route_id} not found. Skipping check.")
            status = "NOT_FOUND_DB"
            return {"status": status} # Return status
        if db_route.status != RouteStatusEnum.MONITORING:
            logger.info(f"Task check_single_route: Route {route_id} is not in MONITORING state (current state: {db_route.status.value if db_route.status else 'None'}). Skipping check.")
            status = "NOT_MONITORING"
            return {"status": status} # Return status

        # Perform the availability check using the SYNCHRONOUS function
        is_available, details = check_route_availability_sync(route=db_route)

        if is_available:
            status = "FOUND"
            result_details = details # Keep details for return value
            logger.info(f"Task check_single_route: Tickets FOUND for route {route_id} ({db_route.regiojet_route_id}). Details: {details}")

            # --- Task 13 Logic ---
            logger.info(f"Task check_single_route: Preparing notifications for route {route_id}")

            # 1. Fetch verified subscribers
            subscribers: List[User] = get_verified_route_subscribers(db=db, route_id=route_id)

            if not subscribers:
                logger.warning(f"Task check_single_route: No verified subscribers found for route {route_id}, but tickets are available.")
            else:
                logger.info(f"Task check_single_route: Found {len(subscribers)} verified subscribers for route {route_id}.")

                # --- Get station names from sync cache ---
                location_map = {}
                cached_locations = _get_locations_from_cache_sync()
                if cached_locations:
                    location_map = {loc.id: loc.name for loc in cached_locations}
                    logger.debug(f"Task check_single_route: Loaded {len(location_map)} locations from sync cache.")
                else:
                    logger.warning(f"Task check_single_route: Could not load locations from sync cache for route {route_id}. Using IDs in email.")

                # Use map to get names, fallback to ID if not found in cache
                from_station_name = location_map.get(db_route.from_location_id, f"ID {db_route.from_location_id}")
                to_station_name = location_map.get(db_route.to_location_id, f"ID {db_route.to_location_id}")
                # --- End Get station names ---

                # --- Převod a formátování časů ---
                departure_dt_utc = db_route.departure_datetime
                arrival_dt_utc = db_route.arrival_datetime
                departure_local_str = "(čas neznámý)"
                arrival_local_str = "(čas neznámý)"

                if departure_dt_utc:
                    if departure_dt_utc.tzinfo is None:
                        departure_dt_utc = departure_dt_utc.replace(tzinfo=timezone.utc)
                    departure_dt_local = departure_dt_utc.astimezone(PRAGUE_TZ)
                    departure_local_str = departure_dt_local.strftime('%d.%m.%Y %H:%M')

                if arrival_dt_utc:
                    if arrival_dt_utc.tzinfo is None:
                        arrival_dt_utc = arrival_dt_utc.replace(tzinfo=timezone.utc)
                    arrival_dt_local = arrival_dt_utc.astimezone(PRAGUE_TZ)
                    arrival_local_str = arrival_dt_local.strftime('%d.%m.%Y %H:%M')

                # 2. Dispatch email tasks
                for user in subscribers:
                    subject = f"Volné lístky nalezeny: {from_station_name} -> {to_station_name} ({departure_local_str})"
                    body = f"""Dobrý den,

na Vámi sledovaném spoji byly nalezeny volné lístky!

Trasa: {from_station_name} -> {to_station_name}
Datum a čas odjezdu: {departure_local_str}
Datum a čas příjezdu: {arrival_local_str}

Počet volných míst: {details.get('freeSeatsCount', 'N/A')}
Cena od: {details.get('priceFrom', 'N/A')} CZK

Odkaz pro rezervaci: {details.get('booking_link', 'Odkaz není dostupný')}

S pozdravem,
Tým Ticket Sniper

"""
                    logger.info(f"Task check_single_route: Scheduling email notification for {user.email} for route {route_id}")
                    send_notification_email.delay(
                        email_to=user.email,
                        subject=subject,
                        body=body
                    )

            # 3. Deactivate route (Do this AFTER dispatching emails, regardless of whether subscribers were found)
            logger.info(f"Task check_single_route: Deactivating route {route_id}")
            deactivated_route = deactivate_route_sync(db=db, route_id=route_id)
            if not deactivated_route:
                # Log error but don't change status, as tickets were found and emails dispatched (if any)
                logger.error(f"Task check_single_route: Failed to deactivate route {route_id} after finding tickets.")
            else:
                logger.info(f"Task check_single_route: Route {route_id} successfully deactivated.")
            # --- End Task 13 Logic ---

        else:
            status = "NOT_FOUND"
            logger.info(f"Task check_single_route: Tickets NOT found for route {route_id} ({db_route.regiojet_route_id}).")

    except HTTPException as e:
        status = "HTTP_ERROR"
        error_message = f"{e.status_code}: {e.detail}"
        logger.error(f"Task check_single_route: HTTPException checking route {route_id}: {error_message}")
        # No retry for sync task in this simple version
    except Exception as e:
        status = "UNEXPECTED_ERROR"
        error_message = str(e)
        logger.exception(f"Task check_single_route: Unexpected error checking route {route_id}: {e}")
        if db:
             db.rollback() # Rollback on error
    finally:
        if db:
            db.close() # Ensure session is closed

    # Return a serializable dictionary
    final_result = {"status": status}
    if result_details:
        final_result["details"] = result_details
    if error_message:
        final_result["error_message"] = error_message
    logger.info(f"Task check_single_route finished for route_id: {route_id} with status: {status}")
    return final_result



# --- Task 13: Send Notification Email ---
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def send_notification_email(self, email_to: str, subject: str, body: str): # Changed to sync def
    """
    Sends a notification email using the synchronous email service function.
    Configured to automatically retry on failure with exponential backoff.
    """
    logger.info(f"Task send_notification_email: Attempting to send to {email_to} (Attempt {self.request.retries + 1}/{self.request.retries + 1 + (self.request.kwargs.get('max_retries', 3) - self.request.retries)})")
    try:
        success = _send_email_sync(
            email_to=email_to,
            subject=subject,
            plain_text_content=body
        )
        if not success:
            # Raise an exception to trigger Celery's retry mechanism
            raise smtplib.SMTPException(f"Failed to send email to {email_to} using _send_email_sync")
        logger.info(f"Task send_notification_email: Successfully sent to {email_to}")
        return {"status": "SENT", "email_to": email_to}
    except Exception as exc:
        logger.exception(f"Task send_notification_email: Error sending to {email_to}. Triggering retry.")
        # Re-raise the exception to let Celery handle the retry based on autoretry_for
        raise exc


# --- Task: Expire Past Routes ---
@shared_task
def expire_past_routes():
    """
    Periodically checks for active routes whose departure time has passed
    and marks them as inactive.
    Uses SYNCHRONOUS DB session.
    """
    logger.info("Task expire_past_routes starting...")
    expired_count = 0
    db: Session | None = None
    try:
        db = SyncSessionLocal()
        # Correct way to get timezone-aware UTC time
        now_utc = datetime.now(timezone.utc)

        # Find non expired routes where departure time is in the past
        stmt = select(MonitoredRoute).where(
            MonitoredRoute.status != RouteStatusEnum.EXPIRED,
            MonitoredRoute.departure_datetime < now_utc
        )
        routes_to_expire = db.execute(stmt).scalars().all()

        if not routes_to_expire:
            logger.info("Task expire_past_routes: No routes found to expire.")
            return # Exit early

        logger.info(f"Task expire_past_routes: Found {len(routes_to_expire)} routes to expire.")

        for route in routes_to_expire:
            # Use the dedicated expire function
            expired_route = expire_route_sync(db=db, route_id=route.id)
            if expired_route:
                expired_count += 1
                logger.info(f"Task expire_past_routes: Expired route {route.id} ({route.regiojet_route_id}).")
            else:
                # Log if expiration failed, but continue with others
                 logger.error(f"Task expire_past_routes: Failed to expire route {route.id}.")

        logger.info(f"Task expire_past_routes: Successfully expired {expired_count} routes.")

    except Exception as e:
        logger.exception(f"Error in expire_past_routes: {e}")
        if db:
             db.rollback()
    finally:
        if db:
            db.close()

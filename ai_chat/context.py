import logging
import re
from typing import List


logger = logging.getLogger(__name__)


def generate_basic_context(message: str) -> str:
    from .services import FlightContextGenerator  # reuse existing simple generator
    return FlightContextGenerator.generate(message)


def generate_db_context(message: str, user=None) -> str:
    try:
        from django.db.models import Q
        from django.utils import timezone as _tz
        from airport.models import Airport, Flight
        from bookings.models import Order

        parts: List[str] = []

        tokens = [t for t in re.findall(r"[a-zA-Z]{2,}", message or "")][:5]
        if tokens:
            q = Q()
            for t in tokens:
                q |= Q(code__iexact=t) | Q(city__icontains=t) | Q(name__icontains=t)
            airports = list(Airport.objects.filter(q).select_related("country").order_by("name")[:3])
            if airports:
                parts.append("Known airports:")
                for ap in airports:
                    parts.append(f"- {ap.name} ({ap.code}) in {ap.city}, {ap.country.code}")

        codes = [t.upper() for t in tokens if len(t) == 3]
        if len(codes) >= 2:
            dep_code, arr_code = codes[0], codes[1]
            now = _tz.now()
            upcoming = (
                Flight.objects.select_related("airline", "departure_airport", "arrival_airport")
                .filter(
                    departure_airport__code__iexact=dep_code,
                    arrival_airport__code__iexact=arr_code,
                    departure_time__gte=now,
                )
                .order_by("departure_time")[:3]
            )
            upcoming = list(upcoming)
            if upcoming:
                parts.append("Upcoming flights:")
                for f in upcoming:
                    parts.append(
                        f"- {f.airline.code} {f.flight_number} {f.departure_airport.code}->{f.arrival_airport.code} at {f.departure_time:%Y-%m-%d %H:%M}"
                    )

        if user and getattr(user, 'is_authenticated', False):
            last_order = (
                Order.objects.select_related("flight__airline", "flight__departure_airport", "flight__arrival_airport")
                .filter(user=user)
                .order_by("-created_at")
                .first()
            )
            if last_order and getattr(last_order, 'flight', None):
                f = last_order.flight
                parts.append(
                    f"Your last booking: {f.airline.code} {f.flight_number} {f.departure_airport.code}->{f.arrival_airport.code} on {f.departure_date} (status: {last_order.get_status_display()})."
                )

        return "\n".join(parts)
    except Exception as e:
        logger.debug(f"DB context enrichment error: {e}")
        return ""



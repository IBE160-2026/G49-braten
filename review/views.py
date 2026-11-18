"""P09 «Repetisjon» (FR-15, AD-11, AD-13, AD-18).

`start` is a GET (the entry points are links): it reuses today's open Review of the same scope and
redirects to it, or, with nothing due, shows «Ingen kort i dag» and creates nothing. The session
page shows the current card; `?vis=svar` is the flip without JavaScript. A rating POSTs with its
`step`: under HTMX the `card` partial for #review-card comes back with the session-bar out of band,
otherwise a redirect to the session page (POST/redirect/GET). Every lookup is owned, or 404 (AD-7).
"""

from django.shortcuts import redirect, render, resolve_url
from django.views.decorators.http import require_POST, require_safe

from core import time
from core.http import htmx_target, safe_next, vary_on_htmx
from core.messages import MESSAGES
from core.ownership import get_owned_or_404
from courses.models import Course, Topic
from courses.scope import Scope
from review import rules, services
from review.models import Review
from studymat.models import Flashcard

CARD_TARGET = "review-card"
# Hjem lives in `web`; review names it by URL name only (AD-1 governs imports).
HOME = "web:home"
# The query that shows the back of the card without JavaScript.
FLIP_PARAM, FLIP_VALUE = "vis", "svar"
# Keys 1–4, in the order of the rating-buttons.
RATING_ORDER = (rules.RatingValue.AGAIN, rules.RatingValue.HARD, rules.RatingValue.GOOD, rules.RatingValue.EASY)


def _id(raw) -> int | None:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _context_label(scope: Scope, name: str) -> str:
    if scope.is_all:
        return MESSAGES["review_context_all"]
    return MESSAGES["review_context_scoped"].format(name=name)


def _scope_name(review: Review) -> str:
    if review.topic_id:
        return review.topic.name
    if review.course_id:
        return review.course.name
    return ""


@require_safe
def start(request):
    """«I dag · N» and «Repeter dagens kort (N)»: optional `course` or `topic`, and a safe `next`."""
    return_url = safe_next(request) or resolve_url(HOME)
    name = ""
    if "topic" in request.GET:
        topic = get_owned_or_404(Topic, request.user, pk=_id(request.GET["topic"]))
        scope, name = Scope(topic_id=topic.id), topic.name
    elif "course" in request.GET:
        course = get_owned_or_404(Course, request.user, pk=_id(request.GET["course"]))
        scope, name = Scope(course_id=course.id), course.name
    else:
        scope = Scope.all()
    if not services.due_cards(request.user, scope).exists():
        return render(
            request,
            "review/session.html",
            {
                "state": "empty",
                "exit_url": return_url,
                "context_label": _context_label(scope, name),
                "next_date": services.next_due_date(request.user, scope),
            },
        )
    review = services.start(request.user, scope, return_url)
    return redirect("review:session", review.id)


def _owned_review(request, review_id) -> Review:
    return get_owned_or_404(Review.objects.select_related("course", "topic"), request.user, pk=review_id)


@require_safe
@vary_on_htmx
def session(request, review_id):
    """P09: the current card (its back with `?vis=svar`), or the end once nothing is due."""
    review = _owned_review(request, review_id)
    return _respond(request, review, flipped=request.GET.get(FLIP_PARAM) == FLIP_VALUE)


@require_POST
@vary_on_htmx
def rate(request, review_id):
    """Rate a Due card at `step`. A repeated step, a card no longer due or an ended Review changes nothing."""
    review = _owned_review(request, review_id)
    flashcard = get_owned_or_404(Flashcard, request.user, pk=_id(request.POST.get("flashcard")))
    rating = request.POST.get("rating", "")
    step = _id(request.POST.get("step"))
    if (
        review.ended_at is None
        and step is not None
        and rating in rules.RatingValue.values
        and services.due_cards(request.user, review.scope).filter(flashcard=flashcard).exists()
    ):
        services.rate(review, flashcard, rating, step)
    if htmx_target(request) == CARD_TARGET:
        return _respond(request, review, flipped=False)
    return redirect("review:session", review.id)


def _respond(request, review: Review, *, flipped: bool):
    context = _context(review, flipped=flipped)
    if htmx_target(request) == CARD_TARGET:
        context["oob"] = True
        return render(request, "review/session.html#card", context)
    return render(request, "review/session.html", context)


def _context(review: Review, *, flipped: bool) -> dict:
    scope = review.scope
    context = {
        "review": review,
        "exit_url": review.return_url,
        "context_label": _context_label(scope, _scope_name(review)),
    }
    progress = services.progress(review) if review.ended_at is None else None
    if progress is None or progress.current is None:
        services.finish(review)
        rated = review.ratings.values("flashcard_id").distinct().count()
        next_date = services.next_due_date(review.student, scope)
        context.update(
            {
                "state": "end",
                "rated": rated,
                "next_label": rules.return_label((next_date - time.today()).days) if next_date else "",
            }
        )
        return context
    state = progress.current
    card = state.flashcard
    topic = card.source.topic
    today = time.today()
    buttons = []
    for key, value in enumerate(RATING_ORDER, start=1):
        _, due = rules.next_due(state.box, value, today)
        buttons.append(
            {"value": value, "label": rules.RatingValue(value).label, "when": rules.return_label((due - today).days), "key": key}
        )
    context.update(
        {
            "state": "card",
            "card": card,
            "lang": card.source.language,
            "course_name": topic.course.name,
            "topic_name": topic.name,
            "flipped": flipped,
            "flip_url": f"{resolve_url('review:session', review.id)}?{FLIP_PARAM}={FLIP_VALUE}",
            "rate_url": resolve_url("review:rate", review.id),
            "step": progress.next_step,
            "buttons": buttons,
            # session-bar: «N av M» over a progress bar.
            "index": progress.number,
            "total": progress.total,
            "bar": True,
            "done": progress.done,
        }
    )
    return context

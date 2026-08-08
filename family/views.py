import json

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from .models import (
    ParentChildRelation,
    Person,
    SiblingRelation,
    SpouseRelation,
    WelcomeScreen,
)


from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def index(request):
    welcome = WelcomeScreen.objects.first()
    context = {
        'welcome': welcome,
        'can_save_layout': request.user.is_authenticated and request.user.is_superuser,
    }
    return render(request, 'family/index.html', context)


def person_detail(request, pk):
    person = get_object_or_404(Person, pk=pk)
    parents = Person.objects.filter(children_relations__child=person)
    children = Person.objects.filter(parent_relations__parent=person)
    siblings = Person.objects.filter(
        sibling_relations_a__person_b=person
    ) | Person.objects.filter(
        sibling_relations_b__person_a=person
    )
    spouses = Person.objects.filter(
        spouse_relations_a__person_b=person
    ) | Person.objects.filter(
        spouse_relations_b__person_a=person
    )
    context = {
        'person': person,
        'parents': parents.distinct(),
        'children': children.distinct(),
        'siblings': siblings.distinct(),
        'spouses': spouses.distinct(),
    }
    return render(request, 'family/person_detail.html', context)


@require_GET
def graph_api(request):
    nodes = []
    for person in Person.objects.all():
        nodes.append({
            'id': person.pk,
            'first_name': person.first_name,
            'last_name': person.last_name,
            'middle_name': person.middle_name,
            'full_name': person.full_name,
            'node_label': person.node_label,
            'initials': person.initials,
            'photo_url': person.photo.url if person.photo else None,
            'short_bio': person.short_bio,
            'lifespan': person.lifespan_display,
            'detail_url': f'/person/{person.pk}/',
            'x': person.graph_x,
            'y': person.graph_y,
        })

    edges = []
    for rel in ParentChildRelation.objects.select_related('parent', 'child'):
        edges.append({
            'source': rel.parent_id,
            'target': rel.child_id,
            'type': 'parent-child',
        })

    for rel in SiblingRelation.objects.select_related('person_a', 'person_b'):
        edges.append({
            'source': rel.person_a_id,
            'target': rel.person_b_id,
            'type': 'sibling',
            'subtype': rel.relation_type,
        })

    for rel in SpouseRelation.objects.select_related('person_a', 'person_b'):
        edges.append({
            'source': rel.person_a_id,
            'target': rel.person_b_id,
            'type': 'spouse',
        })

    return JsonResponse({
        'nodes': nodes,
        'edges': edges,
        'can_save_layout': request.user.is_authenticated and request.user.is_superuser,
    })


@require_POST
@login_required
@user_passes_test(lambda u: u.is_superuser)
def save_positions(request):
    """Сохранить позиции узлов. Только суперюзер; видно всем после обновления."""
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'Некорректный JSON'}, status=400)

    positions = payload.get('positions')
    if not isinstance(positions, list) or not positions:
        return JsonResponse({'ok': False, 'error': 'Нужен список positions'}, status=400)

    updated = 0
    for item in positions:
        try:
            person_id = int(item['id'])
            x = float(item['x'])
            y = float(item['y'])
        except (KeyError, TypeError, ValueError):
            continue
        updated += Person.objects.filter(pk=person_id).update(graph_x=x, graph_y=y)

    return JsonResponse({'ok': True, 'updated': updated})

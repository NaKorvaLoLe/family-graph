from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .models import (
    ParentChildRelation,
    Person,
    SiblingRelation,
    SpouseRelation,
    WelcomeScreen,
)


def index(request):
    welcome = WelcomeScreen.objects.first()
    context = {
        'welcome': welcome,
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
            'full_name': person.full_name,
            'initials': person.initials,
            'photo_url': person.photo.url if person.photo else None,
            'short_bio': person.short_bio,
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

    return JsonResponse({'nodes': nodes, 'edges': edges})

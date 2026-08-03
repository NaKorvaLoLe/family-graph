from django.core.management.base import BaseCommand

from family.models import (
    ParentChildRelation,
    Person,
    SiblingRelation,
    SpouseRelation,
    WelcomeScreen,
)


class Command(BaseCommand):
    help = 'Загрузить демонстрационные данные семейного графа'

    def handle(self, *args, **options):
        if Person.objects.exists():
            self.stdout.write('Данные уже существуют, пропуск.')
            return

        WelcomeScreen.objects.get_or_create(
            pk=1,
            defaults={
                'title': 'Наши корни',
                'text': (
                    'Семья — это не просто слово. Это связь поколений, '
                    'история, которую мы несём в себе, и корни, которые '
                    'дают нам силу двигаться вперёд. Каждый человек в этом '
                    'графе — часть нашей общей истории.'
                ),
                'button_text': 'Открыть граф',
            },
        )

        grandfather = Person.objects.create(
            first_name='Иван',
            last_name='Петров',
            birth_date='1940-05-15',
            short_bio='Основатель рода, работал инженером.',
            full_bio='Иван Петров родился в 1940 году. Всю жизнь посвятил семье и работе.',
            graph_x=-4,
            graph_y=2,
        )
        grandmother = Person.objects.create(
            first_name='Мария',
            last_name='Петрова',
            birth_date='1942-08-20',
            short_bio='Душа семьи, учительница.',
            full_bio='Мария Петрова — учительница начальных классов, воспитала троих детей.',
            graph_x=4,
            graph_y=2,
        )
        father = Person.objects.create(
            first_name='Алексей',
            last_name='Петров',
            birth_date='1965-03-10',
            short_bio='Старший сын, архитектор.',
            full_bio='Алексей Петров — архитектор, проектировал здания в родном городе.',
            graph_x=-3,
            graph_y=-2,
        )
        uncle = Person.objects.create(
            first_name='Дмитрий',
            last_name='Петров',
            birth_date='1968-11-25',
            short_bio='Младший брат, врач.',
            full_bio='Дмитрий Петров — хирург, работает в городской больнице.',
            graph_x=0,
            graph_y=-2,
        )
        aunt = Person.objects.create(
            first_name='Елена',
            last_name='Петрова',
            birth_date='1972-07-08',
            short_bio='Младшая сестра, художница.',
            full_bio='Елена Петрова — художница, её работы выставлялись в галереях.',
            graph_x=3,
            graph_y=-2,
        )
        child = Person.objects.create(
            first_name='Николай',
            last_name='Петров',
            birth_date='1990-01-30',
            short_bio='Продолжатель рода.',
            full_bio='Николай Петров — программист, создал этот семейный граф.',
            graph_x=-3,
            graph_y=-6,
        )

        ParentChildRelation.objects.create(parent=grandfather, child=father)
        ParentChildRelation.objects.create(parent=grandmother, child=father)
        ParentChildRelation.objects.create(parent=grandfather, child=uncle)
        ParentChildRelation.objects.create(parent=grandmother, child=uncle)
        ParentChildRelation.objects.create(parent=grandfather, child=aunt)
        ParentChildRelation.objects.create(parent=grandmother, child=aunt)
        ParentChildRelation.objects.create(parent=father, child=child)

        SpouseRelation.objects.create(person_a=grandfather, person_b=grandmother)

        SiblingRelation.objects.create(
            person_a=father, person_b=uncle, relation_type='brother_brother',
        )
        SiblingRelation.objects.create(
            person_a=father, person_b=aunt, relation_type='brother_sister',
        )
        SiblingRelation.objects.create(
            person_a=uncle, person_b=aunt, relation_type='brother_sister',
        )

        self.stdout.write(self.style.SUCCESS('Демо-данные успешно загружены.'))

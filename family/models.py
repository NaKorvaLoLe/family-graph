from django.core.exceptions import ValidationError
from django.db import models


class Person(models.Model):
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    photo = models.ImageField('Фото', upload_to='photos/', blank=True, null=True)
    birth_date = models.DateField('Дата рождения', blank=True, null=True)
    death_date = models.DateField('Дата смерти', blank=True, null=True)
    short_bio = models.TextField(
        'Краткая информация',
        max_length=500,
        blank=True,
        help_text='Отображается во всплывающем окне на графе',
    )
    full_bio = models.TextField('Полное описание', blank=True)
    graph_x = models.FloatField('Позиция X на графе', default=0)
    graph_y = models.FloatField('Позиция Y на графе', default=0)

    class Meta:
        verbose_name = 'Человек'
        verbose_name_plural = 'Люди'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    @property
    def initials(self):
        first = self.first_name[0].upper() if self.first_name else ''
        last = self.last_name[0].upper() if self.last_name else ''
        return f'{first}{last}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'


class ParentChildRelation(models.Model):
    parent = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='children_relations',
        verbose_name='Родитель',
    )
    child = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='parent_relations',
        verbose_name='Ребёнок',
    )

    class Meta:
        verbose_name = 'Связь родитель — ребёнок'
        verbose_name_plural = 'Связи родитель — ребёнок'
        unique_together = ('parent', 'child')

    def __str__(self):
        return f'{self.parent} → {self.child}'

    def clean(self):
        if self.parent_id and self.child_id:
            if self.parent_id == self.child_id:
                raise ValidationError('Родитель и ребёнок не могут быть одним человеком.')
            if ParentChildRelation.objects.filter(
                parent_id=self.parent_id,
                child_id=self.child_id,
            ).exclude(pk=self.pk).exists():
                raise ValidationError('Такая связь уже существует.')
            if ParentChildRelation.objects.filter(
                parent_id=self.child_id,
                child_id=self.parent_id,
            ).exclude(pk=self.pk).exists():
                raise ValidationError(
                    'Обратная связь уже есть: эти люди уже связаны как родитель — ребёнок. '
                    'Повторно добавлять связь в обратном порядке нельзя.'
                )


class SiblingRelation(models.Model):
    SIBLING_TYPES = [
        ('brother_brother', 'Брат — брат'),
        ('sister_sister', 'Сестра — сестра'),
        ('brother_sister', 'Брат — сестра'),
    ]

    person_a = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='sibling_relations_a',
        verbose_name='Человек A',
    )
    person_b = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='sibling_relations_b',
        verbose_name='Человек B',
    )
    relation_type = models.CharField(
        'Тип связи',
        max_length=20,
        choices=SIBLING_TYPES,
        default='brother_sister',
    )

    class Meta:
        verbose_name = 'Связь братьев/сестёр'
        verbose_name_plural = 'Связи братьев/сестёр'
        unique_together = ('person_a', 'person_b')

    def __str__(self):
        return f'{self.person_a} ↔ {self.person_b} ({self.get_relation_type_display()})'

    def _ordered_ids(self):
        a, b = self.person_a_id, self.person_b_id
        if a and b and a > b:
            return b, a
        return a, b

    def clean(self):
        a, b = self._ordered_ids()
        if a and b:
            if a == b:
                raise ValidationError('Нельзя связать человека с самим собой.')
            if SiblingRelation.objects.filter(
                person_a_id=a,
                person_b_id=b,
            ).exclude(pk=self.pk).exists():
                raise ValidationError(
                    'Связь между этими людьми уже существует '
                    '(порядок A и B не важен).'
                )

    def save(self, *args, **kwargs):
        if self.person_a_id and self.person_b_id and self.person_a_id > self.person_b_id:
            self.person_a, self.person_b = self.person_b, self.person_a
        super().save(*args, **kwargs)


class SpouseRelation(models.Model):
    person_a = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='spouse_relations_a',
        verbose_name='Супруг(а) A',
    )
    person_b = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='spouse_relations_b',
        verbose_name='Супруг(а) B',
    )

    class Meta:
        verbose_name = 'Связь супругов'
        verbose_name_plural = 'Связи супругов'
        unique_together = ('person_a', 'person_b')

    def __str__(self):
        return f'{self.person_a} ♥ {self.person_b}'

    def _ordered_ids(self):
        a, b = self.person_a_id, self.person_b_id
        if a and b and a > b:
            return b, a
        return a, b

    def clean(self):
        a, b = self._ordered_ids()
        if a and b:
            if a == b:
                raise ValidationError('Нельзя связать человека с самим собой.')
            if SpouseRelation.objects.filter(
                person_a_id=a,
                person_b_id=b,
            ).exclude(pk=self.pk).exists():
                raise ValidationError(
                    'Связь супругов между этими людьми уже существует '
                    '(порядок A и B не важен).'
                )

    def save(self, *args, **kwargs):
        if self.person_a_id and self.person_b_id and self.person_a_id > self.person_b_id:
            self.person_a, self.person_b = self.person_b, self.person_a
        super().save(*args, **kwargs)


class WelcomeScreen(models.Model):
    title = models.CharField('Заголовок', max_length=200, default='Наши корни')
    text = models.TextField(
        'Текст',
        default=(
            'Семья — это не просто слово. Это связь поколений, '
            'история, которую мы несём в себе, и корни, которые '
            'дают нам силу двигаться вперёд. Каждый человек в этом '
            'графе — часть нашей общей истории.'
        ),
    )
    button_text = models.CharField('Текст кнопки', max_length=50, default='Открыть граф')

    class Meta:
        verbose_name = 'Приветственный экран'
        verbose_name_plural = 'Приветственный экран'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk and WelcomeScreen.objects.exists():
            raise ValueError('Может существовать только один приветственный экран')
        return super().save(*args, **kwargs)

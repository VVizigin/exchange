from django.utils import timezone


def year(request):
    dt = timezone.now().year
    """Добавляет переменную с текущим годом."""
    return {
        'year': dt
    }

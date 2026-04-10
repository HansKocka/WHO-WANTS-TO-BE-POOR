import random
from .models import GameSession

def generate_pin():
    while True:
        pin = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        if not GameSession.objects.filter(pin=pin).exists():
            return pin
from datetime import date, timedelta


class SpacedRepetitionEngine:
    @staticmethod
    def sm2(interval: int, ease_factor: float, quality: int) -> tuple[int, float]:
        quality = max(0, min(5, quality))
        if quality < 3:
            return 1, max(1.3, ease_factor - 0.2)

        if interval == 0:
            next_interval = 1
        elif interval == 1:
            next_interval = 6
        else:
            next_interval = round(interval * ease_factor)

        new_ease = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        return max(1, next_interval), max(1.3, new_ease)

    @staticmethod
    def next_review_date(today: date, interval: int) -> date:
        return today + timedelta(days=max(1, interval))

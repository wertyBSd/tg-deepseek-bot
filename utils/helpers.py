def format_time(seconds: float) -> str:
    """
    Форматирует время в удобочитаемый вид
    Если меньше 60 секунд - показывает в секундах
    Если больше - в минутах и секундах
    """
    if seconds < 60:
        return f"{seconds:.1f}с"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}м {secs:.1f}с"

def format_time_detailed(seconds: float) -> str:
    """
    Детальное форматирование с указанием единиц измерения
    """
    if seconds < 60:
        return f"{seconds:.2f} секунд"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes} минут {secs:.1f} секунд"
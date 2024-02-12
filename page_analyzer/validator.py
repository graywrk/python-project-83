import validators

def validate(name):
    errors = ''
    if len(name) == 0:
        errors = "URL обязателен"
    if len(name) > 255:
        errors = "URL превышает 255 символов"
    if not validators.url(name):
        errors = "Некорректный URL"
    return errors
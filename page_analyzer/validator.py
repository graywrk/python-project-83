def validate(name):
    errors = ''
    if not name:
        errors = "URL обязателен"
    return errors
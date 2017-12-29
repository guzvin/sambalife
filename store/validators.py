def validate_file_extension(value):
    import os
    from django.core.exceptions import ValidationError
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.gif', '.jpg', '.png']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Extensão de arquivo inválida (.gif, .jpg ou .png).')

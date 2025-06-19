from functools import wraps
from ninja.errors import HttpError
from http import HTTPStatus

def role_required(roles):
    """
    Décorateur pour restreindre l'accès à certains rôles.
    Usage : @role_required(["ADMIN", "MODERATEUR"])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if not user or not user.is_authenticated:
                raise HttpError(HTTPStatus.UNAUTHORIZED, "Authentification requise.")
            if user.role not in roles:
                raise HttpError(HTTPStatus.FORBIDDEN, "Permission refusée.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator 
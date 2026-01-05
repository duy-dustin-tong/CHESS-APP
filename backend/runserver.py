import os
from api import create_app
from api.utils import socketio

try:
    from decouple import config as _decouple_config
except Exception:
    def _decouple_config(key, default=None, cast=None):
        value = os.environ.get(key, default)
        if cast and value is not None:
            try:
                value = cast(value)
            except Exception:
                pass
        return value

app = create_app()

if __name__ == '__main__':
    port = int(_decouple_config('PORT', 5000, cast=int))
    debug = str(_decouple_config('DEBUG', 'True')).lower() in ('1', 'true', 'yes')
    host = _decouple_config('HOST', '0.0.0.0')
    socketio.run(app, host=host, port=port, debug=debug)
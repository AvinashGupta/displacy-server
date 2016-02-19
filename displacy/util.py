import os


def hide(value):
    return '*' * len(value)


def set_config(app, key, value=None, cast=str):
    env_value = os.environ.get(key, value)
    if value is None and env_value is None:
        raise Exception('environment variable missing: %s' % key)

    if isinstance(value, bool) or cast == bool:
        cast = lambda x: x == True or x.lower() == 'true'

    env_value = cast(env_value)
    app.config[key] = env_value

    if 'secret' in key.lower():
        out_value = hide(env_value)
    else:
        out_value = env_value

    print('%s: %s (%s)' % (key, out_value, env_value.__class__.__name__))

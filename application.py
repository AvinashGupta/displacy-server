from displacy.server import app as application


if __name__ == '__main__':
    application.run(use_reloader=False, host='0.0.0.0', port=5000)

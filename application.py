from news import app

api = app

if __name__ == '__main__':
    api.run(host='0.0.0.0', port=80)

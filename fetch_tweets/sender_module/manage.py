#Author : Malvika Mohan
#Date : 3rd April, 2021

import os
import werkzeug

werkzeug.cached_property = werkzeug.utils.cached_property
from flask_script import Manager
from app.main import create_app
from app import blueprint

app = create_app(os.getenv('BOILERPLATE_ENV') or 'dev')
app.register_blueprint(blueprint)
app.app_context().push()

manager = Manager(app)


@manager.command
def run():
    app.run(host="0.0.0.0",port=8889)


if __name__ == '__main__':
    manager.run()

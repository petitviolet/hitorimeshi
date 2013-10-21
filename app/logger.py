# -*- encoding:utf-8 -*-
'''flaskのapp用logger'''

import logging
from logging.handlers import RotatingFileHandler  # ,SMTPHandler
import os

def config_logger(app):
    app.logger.setLevel(logging.INFO)
    app.config['DEBUG'] = True
    if app.debug or app.testing:
        return

    # mail_handler = \
    #     SMTPHandler(app.config['MAIL_SERVER'],
    #                 'error@newsmeme.com',
    #                 app.config['ADMINS'],
    #                 'application error',
    #                 (
    #                     app.config['MAIL_USERNAME'],
    #                     app.config['MAIL_PASSWORD'],
    #                 ))

    # mail_handler.setLevel(logging.ERROR)
    # app.logger.addHandler(mail_handler)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')

    debug_log = os.path.join(app.root_path,
                             'log/debug.log')

    debug_file_handler = \
        RotatingFileHandler(debug_log,
                            maxBytes=100000,
                            backupCount=10)

    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.setFormatter(formatter)
    app.logger.addHandler(debug_file_handler)

    error_log = os.path.join(app.root_path,
                             'log/error.log')

    error_file_handler = \
        RotatingFileHandler(error_log,
                            maxBytes=100000,
                            backupCount=10)

    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    app.logger.addHandler(error_file_handler)

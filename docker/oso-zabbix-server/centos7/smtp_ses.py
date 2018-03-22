#!/usr/bin/env python
'''
Email script for zabbix notifications
'''

import smtplib
import sys
import yaml
import tempfile
import os
import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger()
logFormatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logFile = '/var/log/zabbix/email_send.log'

logRFH = RotatingFileHandler(logFile, mode='a', maxBytes=2*1024*1024, backupCount=5, delay=0)
logRFH.setFormatter(logFormatter)
logRFH.setLevel(logging.INFO)
logger.addHandler(logRFH)
logger.setLevel(logging.INFO)


def get_config():
    '''Fetch the zabbix config credentials
    '''
    return yaml.load(open('/etc/openshift_tools/zabbix_actions.yml'))

def email():
    '''send email for zabbix
    '''

    config = get_config()

    mailfrom = config.get('ses_mail_from', None)
    smtpdomain = config.get('ses_smtp_domain', None)
    smtpserver = config.get('ses_smtp_server', None)
    username = config.get('ses_user', None)
    password = config.get('ses_password', None)
    if any([var == None for var in  [mailfrom, smtpserver, smtpdomain, username, password]]):
        print 'Please provide the necessary variables.'
        sys.exit(1)

    try:
        to_addr = sys.argv[1]
        subject = sys.argv[2]
        body = sys.argv[3]

        msg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (mailfrom, ", ".join(to_addr.split(',')), subject))

        msg += body

        server = smtplib.SMTP_SSL(smtpserver, 465, smtpdomain)
        server.set_debuglevel(1)
        try:
            server.login(username, password)
            server.sendmail(mailfrom, to_addr, msg)
        except Exception as ex:
            logger.info('Error sending message: %s', ex)
    finally:
        server.quit()

if __name__ == '__main__':
    # Find an available file descriptor
    t = tempfile.TemporaryFile(dir='/tmp')
    available_fd = t.fileno()
    t.close()

    # now make a copy of stderr
    os.dup2(2,available_fd)

    # Now create a new tempfile and make Python's stderr go to that file
    t = tempfile.TemporaryFile(dir='/tmp')
    os.dup2(t.fileno(),2)

    email()

    # Grab the stderr from the temp file
    sys.stderr.flush()
    t.flush()
    t.seek(0)
    stderr_output = t.read()
    logger.info('Sending email:\n%s', stderr_output)
    t.close()

    # Put back stderr
    os.dup2(available_fd,2)
    os.close(available_fd)

## Credits:
## SMTP-part is based on https://stackoverflow.com/a/44498100/1560436
## Dot-Dict is taken from https://stackoverflow.com/a/23689767/1560436

import argparse
import asyncore
import logging
import smtpd
import email
import datetime
from database import first, select, execute, commit


class SmtpServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        logging.info(f"""SMTP process_message( {peer}, {mailfrom}, {rcpttos} )\n""")
        msg  = email.message_from_string(data)

        execute("""
            INSERT INTO mails (
                recieved_at,
                sender,
                reciever,
                subject,
                read,
                content
            ) VALUES (?, ?, ?, ?, ?, ?)""", [
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                msg.get('From', None),
                msg.get('To', None),
                msg.get('Subject', None),
                0,
                msg.as_string(),
            ]
        )
        commit()


def run( host, port ):
    smtpd = SmtpServer(localaddr=(host, port), remoteaddr=None, decode_data=True)

    try:
        asyncore.loop()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Catch mails and make them accessible on a web page.')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='the smtp host')
    parser.add_argument('--port', type=int, default=2525, help='the smtp port')

    args = parser.parse_args()

    run( host=args.host, port=args.port )

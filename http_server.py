## Dot-Dict is taken from https://stackoverflow.com/a/23689767/1560436

import argparse
import email
import re
import smtplib
from datetime import datetime
from database import first, select, execute, commit

from bottle import route, template, run, static_file, abort, redirect, request, response


########################################################################
# Routes
#

@route('/static/<filepath:path>')
def server_static(filepath):
    """serve a static file"""
    return static_file(filepath, root='./static/')


@route('/')
def index():
    """list the mails"""

    mails = select("SELECT * FROM mails ORDER BY id DESC")

    # no message selected
    selected_message = 0
    message = None

    try:
        return template('common', locals(), error=None)
    except Exception as error:
        return template('common', locals())



@route('/view/message/<id>/')
def view(id):
    """show a message"""

    mails = select("SELECT * FROM mails ORDER BY id DESC")

    selected_message = int(id)

    # mark it "read"
    execute("UPDATE mails SET read=1 WHERE id=:id", {'id': selected_message})

    # load the message
    message = first("SELECT * FROM mails WHERE id=:id", { 'id': selected_message })
    message.object = email.message_from_string(message.content)

    # display it
    try:
        return template('common', locals(), error=None)
    except Exception as error:
        return template('common', locals())



@route('/view/html/<id>/')
def view_as_html(id):
    """display the message as html for use in an iframe"""

    selected_message = int(id)
    message = first("SELECT * FROM mails WHERE id=:id", { 'id': selected_message })
    message.object = email.message_from_string(message.content)
    
    # find it...
    text = 'ERROR: NOT FOUND'
    for part in message.object.walk():
        if part.get_content_type() == 'text/html':
            text = part.get_payload(decode=True).decode()

            # replace the <img src="cid:..." /> with a matching url
            text = re.sub('cid:', f'/view/cid/{id}/', text)

    return text



@route('/view/cid/<id>/<cid>')
def view_cid(id, cid):
    """returns a content element by it's id. mostly images?"""
    selected_message = int(id)
    message = first("SELECT * FROM mails WHERE id=:id", { 'id': selected_message })
    message.object = email.message_from_string(message.content)

    # iterate over the parts of the message
    for part in message.object.walk():

        # if the part has a Content-ID header and it matches the requested cid...
        headers = dict(part.items())
        if 'Content-ID' in headers and headers['Content-ID'].strip('<>') == cid:

            # get the content-type
            content_type = headers.get('Content-Type', 'binary')
            content_type = content_type.split(';')[0]
            
            # set the response content type and return the payload
            response.content_type = content_type
            return part.get_payload(decode=True)
    abort()


@route('/purge/')
def purge():
    """clears the database"""
    execute("DELETE FROM mails")
    return redirect('/')


@route('/send-test/')
def send_test():
    """sends a test mail"""
    host = request.forms.get('host', '127.0.0.1')
    port = request.forms.get('port', '2525')
    
    sender = 'test@localhost'
    receiver = 'you@localhost'
    now = datetime.now()

    message = f"""From: Test <{sender}>
    To: You <{receiver}>
    Subject: Test {now}

    This is a test mail.
    It's been sent to {host}:{port} on {now}.
    Bye!
    """

    message = re.sub("\n[ \t]+", "\n", message)

    mail = smtplib.SMTP(host, port, 'localhost')
    mail.sendmail(sender, [receiver], message)         

    return redirect('/')




########################################################################
# main
# 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Catch mails and make them accessible on a web page.')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='the http host')
    parser.add_argument('--port', type=int, default=8080, help='the http port')

    args = parser.parse_args()

    run(host=args.host, port=args.port, debug=True)

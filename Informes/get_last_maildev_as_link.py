#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import dbconfig

maildev_host = dbconfig.maildev_host

def main():
    url = maildev_host + '/email'
    response = requests.get(url)
    emails = response.json()
    if emails:
        last_email = emails[-1]
        email_id = last_email['id']
        link = u"{}/#/email/{}".format(maildev_host, email_id)
        print(link)
    else:
        print('No emails found in MailDev.')


if __name__ == '__main__':
    main()


# vim: et ts=4 sw=4

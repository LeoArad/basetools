"""
Import Common python packages; Define general tools for internal usage at delivery package
"""
import platform
if platform.platform()[:int(platform.platform().find('-'))] == 'Windows':
    from os import path, startfile
    import win32clipboard
else:
    from os import path
import os
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from fnmatch import fnmatch
from glob import glob
import re
from pyperclip import copy as cp
import logging
import sys
import argparse
import json
import atexit
import datetime
from functools import wraps
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from os.path import *





# SQL_REPOSITORY_DIR = path.expanduser(r'~\Documents\Delivery Audit\SQL_Repository')
DEFAULT_EXPORT_DIR = path.expanduser(r'~\Downloads')
DEFAULT_ENCODING = "utf-8"
MAX_PD_CHUNK_SIZE = 10000
DEFAULT_EXPORT_DIR_LINUX = "/mnt/delivery/OUTPUT"
DEFAULT_IMPORT_DIR_LINUX = "/mnt/delivery/INPUT"
main_path = os.path.abspath(os.path.dirname(__file__))
_conf = {
  "alert_job" : {
    "send_to" : ["lirona@evercompliant.com", "yanivd@evercompliant.com ", "carry-findings@evercompliant.com"]
  }

}



class email_sender(object):
    def __init__(self, to, body=None, subject=None, sender=None, password=None, df=None, file_name=None,
                 from_file=None):
        self.to = to
        self.body = body
        self.subject = subject
        self.sender = sender
        self.df = df
        self.password = 'ever_Delivery1!' if password is None else password
        self.file_name = 'MailTester.csv' if file_name is None else file_name
        self.from_file = from_file

    def crate_mail(self):
        msg = MIMEMultipart()

        self.sender = 'auto.delivery@yahoo.com' if self.sender is None else self.sender
        msg['From'] = self.sender
        msg['To'] = self.to
        msg['Subject'] = "Automated process" if self.subject is None else self.subject
        msg.attach(MIMEText("The sender didn't difne a massege" if self.body is None else self.body))

        if self.from_file is not None:
            self.df = open(self.from_file, 'rb').read()

        if self.df is not None:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(self.df)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= {}".format(basename(self.from_file)))
            msg.attach(part)

        self.text = msg.as_string()

    def send_mail(self):
        print("In send mail")
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        server = smtplib.SMTP('smtp.mail.yahoo.com', 587, timeout=10)
        server.starttls()
        server.login(self.sender, 'ever_Delivery1!')
        server.sendmail(self.sender, self.to, self.text)
        server.quit()
        print("the mail has sent to {}".format(self.to))

    def run(self):
        self.crate_mail()
        self.send_mail()


def define_logger(name="Delivery Audit Tools", file_handler=None, mode='a'):
    """
    :param mode: file mode for file_handler; default "append"
    :param file_handler: if supplied, writes results into a file in addition to writing to stdout
    :param name: If no name is specified, pick the root errors_logger.
    :return: Delivery-format errors_logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.name = name
    if not file_handler:
        ch = logging.StreamHandler(sys.stdout)
    else:
        ch = logging.FileHandler(file_handler, mode=mode)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def manual_argv(*args):
    argv = []
    for arg in args:
        if isinstance(arg, list) or isinstance(arg, tuple):
            argv += arg
        else:
            argv.append(arg)
    return [obj.replace('"', '') for obj in argv if obj != None]

def run_on_all_servers(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


root_logger = define_logger()
parse = argparse.ArgumentParser()
get_last_month_date = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)

def copy_to_clip(str):
    os.system("echo {} | clip".format(str))

def column_to_list(df, column, type=int):
    return df[column].values.astype(type).tolist()

def get_writer(name, folder= 'Desktop',last_month=False):
    add = get_last_month_date.strftime("%B") if last_month else ''
    return pd.ExcelWriter(os.path.expanduser(r"~\{0}\{1}{2}.xlsx".format(folder,name,add)), options={'strings_to_urls': False})

def df_float_to_int(df, type=np.float64, to_type=np.int64):
    for column in df.columns:
        if df[column].dtype == type:
            df[column] = df[column].fillna(0).astype(to_type)
    return df

def win_to_linux(win_param, linux_param):
    if platform.platform()[:int(platform.platform().find('-'))] == 'Windows':
        return win_param
    else:
        return linux_param

def win_or_linux():
    if platform.platform()[:int(platform.platform().find('-'))] == 'Windows':
        return True
    else:
        return False

def get_params_from_str(str):
    if str.find("{") > 0:
        params = []
        cont = str
        while cont.find("{") > 0:
            params.append(cont[cont.find('{')+1: cont.find('}')])
            cont = cont[cont.find('}')+1:]
        return params
    else:
        return None

def empty_df():
    return pd.DataFrame()

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0', ''):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def defualtval(val, defualt):
    if val:
        return val
    else:
        return defualt

def get_drive():
    main_path = os.path.abspath(os.path.dirname(__file__))
    print(os.path.join(main_path, "delivery_files\client_secrets.json"))
    gauth = GoogleAuth()
    gauth.LoadClientConfigFile(os.path.join(os.path.abspath(os.path.dirname(__file__)),r"delivery_files\client_secrets.json"))
    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()
    # Save the current credentials to a file
    gauth.SaveCredentialsFile(r"..\delivery\delivery_files\client_secrets.json")
    drive = GoogleDrive(gauth)
    return drive

def alert_job(func):
    def wrapper(self=None,*args, **kwargs):
        func(self, *args, **kwargs)
        alert_conf = _conf['alert_job']
        message = "The script: {name} \nexecute by {user} \non the site: {server} \non {time}"
        if self and not isinstance(self, (int, long, float, complex, tuple, list, dict, set)):
            name = self.__class__.__name__ if func.__name__ == 'run' else func.__name__
            if self.server:
                server = self.server
            elif self.server_name:
                server = self.server_name
        else:
            name = func.__name__
            server = [v for k,v in kwargs.items() if 'server' in k.lower()]
            server = ','.join(server)
        message = message.format(name=name, user=os.getenv('username'),server=server, time=datetime.datetime.now().strftime("%c"))
        try:
            for k,v in vars(self).iteritems():
                if type(vars(self)[k]) in (int, long, float, complex, tuple, list, dict, set):
                    message += "\nparam: {k} values: {v}".format(k=k,v=v)
                elif k == 'bank':
                    message += "\nBank: {bank}".format(bank=vars(self)[k].bank_obj.name)
        except TypeError as e:
            pass



        for i in alert_conf['send_to']:
            e = email_sender(i, body=message, subject= "Execute script {script} on {server}".format(script=name\
                                                                                                    ,server=server)).run()

    return wrapper

def save_to_local_storage(df, name, type='excel', get_path=False):
    os.chdir(DEFAULT_EXPORT_DIR_LINUX)
    user = os.getenv('username')
    user_path = "{}/{}".format(DEFAULT_EXPORT_DIR_LINUX, user)
    if get_path:
        return user_path
    if not os.path.exists(user_path):
        os.mkdir(user_path)
        os.system("chmod 777 {}".format(user))
    os.chdir(user_path)
    if type == 'excel':
        writer = pd.ExcelWriter("{}/{}.xlsx".format(user_path, name),  options={'strings_to_urls': False})
        df.to_excel(writer, index=False)
        writer.close()
    else:
        df.to_csv("{}/{}.csv".format(user_path, name), index=False)

def list_from_clipboard(type_return=int):
    win32clipboard.OpenClipboard()
    temp = win32clipboard.GetClipboardData().split()
    win32clipboard.CloseClipboard()
    return [type_return(x) for x in temp]

def split_if_list(val,delimiter=','):
    if val.count(delimiter) > 0:
        return val.split(delimiter)
    else:
        return val



__all__ = ['root_logger',
           'parse',
           'DEFAULT_ENCODING',
           'DEFAULT_EXPORT_DIR',
           'DEFAULT_IMPORT_DIR_LINUX',
           'define_logger',
           'os',
           'path',
           'pd',
           're',
           'glob',
           'fnmatch',
           'DataFrame',
           'Series',
           'np',
           'argparse',
           'cp',
           'sys',
           'logging',
           'json',
           'manual_argv',
           'atexit',
           'get_last_month_date',
           'copy_to_clip',
           'get_writer',
           'column_to_list',
           'df_float_to_int',
           'win_to_linux',
           'get_params_from_str',
           'empty_df',
           'str2bool',
           'defualtval',
           'get_drive',
           'alert_job',
           'email_sender',
           'win_or_linux',
           'save_to_local_storage',
           'list_from_clipboard',
           'split_if_list']



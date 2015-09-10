#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from xml.dom import minidom
from xmlrpclib import *
import logging
import urllib2
import traceback
import ConfigParser
from Crypto.Cipher import AES
import base64


# Logs
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename='usuarios.log',level=logging.DEBUG)

def excep(type, value, tb):
  logging.error("Excepción: {0} {1}.".format(str(value), traceback.format_tb(tb)))

sys.excepthook = excep


# Datos de configuración
config = ConfigParser.RawConfigParser()
config.read('usuarios.config')

host=config.get('config', 'host')
port = config.get('config', 'port')
server=ServerProxy ("https://" + host + ":" + port)
className = config.get('config', 'className')
user = config.get('config', 'user')
password = config.get('config', 'password')
url = config.get('config', 'url')
clave = config.get('config', 'clave')


def busca(uid):
  """ Comprueba si existe el uid del usuario """
  method='get_user_list'
  param_list=[]
  param_list.append((user,password))
  param_list.append(className)
  param_list.append(uid)

  ret=getattr(server,method)(*param_list)

  if len(ret) == 0:
    return False
  else:
    return True

  
def cambia_pass(uid, group, newpass):
  """ Cambia el pass del usuario """
  LDAP_BASE_DN = "dc=ma5,dc=lliurex,dc=net"
  path = "uid=" + uid + ",ou=" + group + ",ou=People," + LDAP_BASE_DN
  method='change_password'
  param_list=[]
  param_list.append((user,password))
  param_list.append(className)
  param_list.append(path)
  param_list.append(newpass)

  ret=getattr(server,method)(*param_list)

  return ret


def process_xml(url):
  """ Procesa la lista de usuarios en XML y devuelve una lista con los datos de los usuarios. """
  xmldoc = minidom.parseString(urllib2.urlopen(url).read())
  # xmldoc = minidom.parse('itaca.xml')
  res = []

  # group puede ser: Students, Teachers, Admins
  
  # Alumnos
  itemlist = xmldoc.getElementsByTagName('alumne')
  for i in itemlist:
    el = {}
    el['group'] = 'Students'
    params = {}
    for node in i.childNodes:
      if node.nodeType != node.TEXT_NODE:
        prop = node.tagName

        if node.firstChild:
          valor = node.firstChild.nodeValue
        else:
          valor = ''

        params[prop] = valor
          
    el['data'] = params
    
    res.append(el)

  # Profesores
  itemlist = xmldoc.getElementsByTagName('professor')
  for i in itemlist:
    el = {}
    el['group'] = 'Teachers'
    params = {}
    for node in i.childNodes:
      if node.nodeType != node.TEXT_NODE:
        prop = node.tagName
        if node.firstChild:
          valor = node.firstChild.nodeValue
        else:
          valor = ''

        params[prop] = valor
          
    el['data'] = params
    
    res.append(el)

  return res


def add_user(data,group):
  """ Añade un usuario a LDAP en el grupo indicado. """

  method='add_user'
  param_list=[]
  param_list.append((user,password))
  param_list.append(className)
  param_list.append(group)
  param_list.append(data)

  ret=getattr(server,method)(*param_list)

  return ret

def decodepass(encoded):
  # TODO
  decoded = 'abc'
  return decoded

def main():
  usuarios = process_xml(url)
  for a in usuarios:
    uid = a['data']['uid']
    group = a['group']
    
    # Modificamos campo userPassword
    a['data']['userPassword'] = decodepass(a['data']['userPasswordAlt'])
    del a['data']['userPasswordAlt']
    
    if busca(uid):
      # Si el usuario existe, se cambia su password

      newpass = a['data']['userPassword']

      res  = cambia_pass(uid,group,newpass)
        
      if res == 'true':
        logging.info(u"Se cambia la contraseña para el usuario " + uid + ".\n")
      else:
        logging.error(u"Error al cambiar la contraseña del usuario " + uid + ". Stack: " + res + ".\n")
          
    else:
      # Si el usuario no existe, se crea
      
      res = add_user(a['data'], group)
      
      if "true" in res:
        logging.info(u"Se crea el usuario " + uid + " en el grupo " + group + ".\n")
      else:
        logging.error(u"Error al crear el usuario {0}. Stack: {1}.".format(uid, str(res)))

        
if __name__ == "__main__":
  main()



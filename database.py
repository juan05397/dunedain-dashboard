import sqlite3


def conectar_bd():
    return sqlite3.connect('clan_dunedain.db')

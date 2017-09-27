#!/usr/bin/env python
#-*- coding: utf-8 -*-

import tormysql.pool
from tornado import gen
from tormysql.cursor import DictCursor

class MySqlDB(object):
    def __init__(self, dsn, ioloop):
        self.dbpool = tormysql.pool.ConnectionPool(
            max_connections=20,  # max open connections
            idle_seconds=7200,  # conntion idle timeout time, 0 is not timeout
            wait_connection_timeout=3,  # wait connection timeout
            host="127.0.0.1",
            user="root",
            passwd="123qwe",
            db="chanzai_dev",
            charset="utf8"
        )
        # this is a one way to run ioloop in sync
        future = self.dbpool.connect()
        ioloop.add_future(future, lambda f: ioloop.stop())
        ioloop.start()

    @gen.coroutine
    def execute(self, sqlstr, *parm):
        """
        执行插入或者更新，返回true或者false
        :param sqlstr:
        :param parm:
        :return:
        """
        self.__print_sql(sqlstr, parm)
        rv = True
        try:
            cursor = yield self.dbpool.execute(sqlstr, parm)
            if not cursor:
                rv = False
            else:
                rv = True

        except Exception as e:
            #self.PrintSqlStr(sqlstr, parm)
            errormsg = '[sql error]' + repr(e)
            print errormsg
            rv = False

        finally:
            raise gen.Return(rv)

    @gen.coroutine
    def execute_return(self, sqlstr, *parm):
        """
        执行插入或者更新，返回插入或更新的行信息
        :param sqlstr:
        :param parm:
        :return:
        """
        self.__print_sql(sqlstr, parm)
        try:
            cursor = yield self.dbpool.execute(sqlstr, parm)
            if not cursor:
                rv = False
            else:
                rv = Row(cursor.fetchone())

        except Exception as e:
            #self.PrintSqlStr(sqlstr, parm)
            errormsg = '[sql error]' + repr(e)
            print errormsg
            rv = False

        finally:
            raise gen.Return(rv)

    def trans_exec(self, sqlstr, parm):
        """
        进行事务
        :param sqlstr:
        :param parm:
        :return:
        """
        self.__print_sql(sqlstr, parm)
        if not self.adb_trans:
            self.adb_trans = []

        sqltask = [sqlstr, parm]
        self.adb_trans.append(sqltask)

    @gen.coroutine
    def trans_commit(self):
        """
        提交事务
        :return:
        """
        rv = True
        try:
            cursors = yield self.dbpool.transaction(self.adb_trans)
            if not cursors:
                rv = False

        except Exception as e:
            errormsg = '[sql error]' + repr(e)
            print errormsg
            rv = False

        finally:
            self.adb_trans = []
            raise gen.Return(rv)

    @gen.coroutine
    def query(self, sqlstr, *parm):
        """
        执行查询，返回多条结果
        :param sqlstr:
        :param parm:
        :return:
        """
        rv = []
        self.__print_sql(sqlstr, parm)
        try:
            cursor = yield self.dbpool.execute(sqlstr, parm)
            _fetch = cursor.fetchall()
            if _fetch:
                rv = [Row(row) for row in _fetch]

        except Exception as e:
            errormsg = '[sql error]' + repr(e)
            print errormsg
            raise errormsg

        finally:
            raise gen.Return(rv)

    @gen.coroutine
    def get(self, sqlstr, *parm):
        """
        执行查询，返回一条结果
        :param sqlstr:
        :param parm:
        :return:
        """
        rv = None
        self.__print_sql(sqlstr, parm)
        try:
            cursor = yield self.dbpool.execute(sqlstr, parm)
            _fetch = cursor.fetchone()
            if _fetch:
                rv = Row(_fetch)


        except Exception as e:
            errormsg = '[sql error]' + repr(e)
            print errormsg
            raise errormsg

        finally:
            raise gen.Return(rv)

    def __print_sql(self, sqlstr, parm):
        _parm = []
        if parm:
            for p in parm:
                _parm.append("'%s'" % p)
            outstr = sqlstr % tuple(_parm)
        else:
            outstr = sqlstr
        # print outstr, type(outstr)
        print '[SQL execute]', outstr


class Row(dict):
    """A dict that allows for object-like property access syntax."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

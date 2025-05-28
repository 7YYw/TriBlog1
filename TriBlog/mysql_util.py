import pymysql   # 引入pymysql模块
import traceback # 引入python中的traceback模块，跟踪错误
import sys       # 引入sys模块

class MysqlUtil():
    def __init__(self):
        host = '127.0.0.1'  # 主机名
        user = 'root'  # 数据库用户名
        password = '20050309syw'  # 数据库密码,此处改成自己的mysql密码
        database = 'triblog'  # 数据库名称
        self.db = pymysql.connect(host=host, user=user, password=password, db=database)  # 建立连接
        self.cursor = self.db.cursor(cursor=pymysql.cursors.DictCursor)  # 设置游标，并将游标设置为字典类型


    def insert(self, sql):
        try:
            # 执行sql语句
            print(sql)

            self.cursor.execute(sql)
            # 提交到数据库执行
            self.db.commit()
        except Exception as e:  # 方法一：捕获所有异常
            # 如果发生异常，则回滚
            print("发生异常", e)
            self.db.rollback()
        finally:
            # 最终关闭数据库连接
            self.db.close()

    def fetchone(self, sql):
        '''
            查询数据库：单个结果集
            fetchone(): 该方法获取下一个查询结果集。结果集是一个对象
        '''
        try:
            # 执行sql语句
            self.cursor.execute(sql)
            result = self.cursor.fetchone()
        except:  # 方法二：采用traceback模块查看异常
            # 输出异常信息
            traceback.print_exc()
            # 如果发生异常，则回滚
            self.db.rollback()
        finally:
            # 最终关闭数据库连接
            self.db.close()
        return result

    def fetchall(self, sql):
        '''
            查询数据库：多个结果集
            fetchall(): 接收全部的返回结果行.
        '''
        try:
            # 执行sql语句
            self.cursor.execute(sql)
            results = self.cursor.fetchall()
        except:  # 方法三：采用sys模块回溯最后的异常
            # 输出异常信息
            info = sys.exc_info()
            print(info[0], ":", info[1])
            # 如果发生异常，则回滚
            self.db.rollback()
        finally:
            # 最终关闭数据库连接
            self.db.close()
        return results

    def update(self, sql):
        '''
            更新结果集
        '''
        try:
            # 执行sql语句
            self.cursor.execute(sql)
            self.db.commit()
        except:
            # 如果发生异常，则回滚
            self.db.rollback()
        finally:
            # 最终关闭数据库连接
            self.db.close()

    def delete(self, sql):
        '''
            删除结果集
        '''
        try:
            # 执行sql语句
            self.cursor.execute(sql)
            self.db.commit()
        except:  # 把这些异常保存到一个日志文件中，来分析这些异常
            # 将错误日志输入到目录文件中
            f = open("log.txt", 'a')
            traceback.print_exc(file=f)
            f.flush()
            f.close()
            # 如果发生异常，则回滚
            self.db.rollback()
        finally:
            # 最终关闭数据库连接
            self.db.close()

if __name__ == '__main__':
    username = "guo7"
    password = "123456789"
    isadmin = 1

    db = MysqlUtil()  # 实例化数据库操作类
    sql = "INSERT INTO usermodel(username,password,is_admin) \
          VALUES ('%s', '%s', '%d')" % (username, password,isadmin)  # user表中插入记录
    db.insert(sql)

    # update_sql = "UPDATE usermodel SET username='%s', password='%s' WHERE id='%d'" % ("new name", "8888", 1)
    # db = MysqlUtil()  # 实例化数据库操作类
    # db.update(update_sql)  # 更新数据的SQL语句
    #
    # db = MysqlUtil()  # 实例化数据库操作类
    # sql = "DELETE FROM usermodel WHERE id = '%s'" % (4)  # 执行删除笔记的SQL语句
    # db.delete(sql)  # 删除数据库
    #
    # # db = MysqlUtil()  # 实例化数据库操作类
    # # sql = 'SELECT * FROM usermodel'  # 从article表中筛选5条数据，并根据日期降序排序
    # # articles = db.fetchall(sql)  # 获取多条记录
    # #
    # sql = "SELECT * FROM usermodel  WHERE username = '%s'" % ("guo")  # 根据用户名查找user表中记录
    # db = MysqlUtil()  # 实例化数据库操作类
    # result = db.fetchone(sql)  # 获取一条记录
    # print(result)
    #
    # print("{:<11} {:<11} {:<11} {:<11}".format('id', 'username', 'email', 'password'))
    # # 打印数据
    # for row in articles:
    #     print("{:<11} {:<11} {:<11} {:<11}".format(row['id'], row['username'], row['email'], row['password']))

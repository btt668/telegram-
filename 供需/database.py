import sqlite3
import logging
import random
import time
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_file='bot_data.db'):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # 用户表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_banned BOOLEAN DEFAULT FALSE,
                        post_count INTEGER DEFAULT 0,
                        balance REAL DEFAULT 0.0
                    )
                ''')
                
                # 投稿表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS submissions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        content TEXT NOT NULL,
                        submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        admin_comment TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                # 每日发布限制表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS daily_posts (
                        user_id INTEGER,
                        post_date DATE,
                        post_count INTEGER DEFAULT 0,
                        PRIMARY KEY (user_id, post_date),
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                # 充值订单表 - 新增，用于TRC20监听
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recharge_orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        order_id TEXT UNIQUE NOT NULL,
                        base_amount REAL NOT NULL,
                        exact_amount REAL NOT NULL,
                        wallet_address TEXT NOT NULL,
                        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expire_time TIMESTAMP NOT NULL,
                        status TEXT DEFAULT 'pending',  -- pending, paid, expired, cancelled
                        transaction_hash TEXT,
                        paid_time TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                # 系统设置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_settings (
                        setting_key TEXT PRIMARY KEY,
                        setting_value TEXT NOT NULL,
                        description TEXT,
                        updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                
                # 初始化默认系统设置
                self._init_default_settings(cursor)
                conn.commit()
                
                logging.info("数据库初始化成功")
                
        except Exception as e:
            logging.error(f"数据库初始化失败: {e}")
    
    def _init_default_settings(self, cursor):
        """初始化默认系统设置"""
        from config import DEFAULT_POST_FEE, DEFAULT_RECHARGE_ADDRESS
        
        # 初始化发布费用设置
        cursor.execute('''
            INSERT OR IGNORE INTO system_settings 
            (setting_key, setting_value, description) 
            VALUES (?, ?, ?)
        ''', ('post_fee', str(DEFAULT_POST_FEE), '每条供需信息发布费用'))
        
        # 初始化充值地址设置
        cursor.execute('''
            INSERT OR IGNORE INTO system_settings 
            (setting_key, setting_value, description) 
            VALUES (?, ?, ?)
        ''', ('recharge_address', DEFAULT_RECHARGE_ADDRESS, '充值钱包地址'))
        
        logging.info(f"初始化默认发布费用: {DEFAULT_POST_FEE}U")
        logging.info(f"初始化默认充值地址: {DEFAULT_RECHARGE_ADDRESS}")
    
    def get_system_setting(self, setting_key, default_value="0"):
        """获取系统设置"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT setting_value FROM system_settings WHERE setting_key = ?', (setting_key,))
                result = cursor.fetchone()
                return result[0] if result else default_value
        except Exception as e:
            logging.error(f"获取系统设置失败: {e}")
            return default_value
    
    def set_system_setting(self, setting_key, setting_value, description=None):
        """设置系统设置"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO system_settings 
                    (setting_key, setting_value, description, updated_time) 
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (setting_key, str(setting_value), description))
                conn.commit()
                logging.info(f"系统设置已更新: {setting_key} = {setting_value}")
                return True
        except Exception as e:
            logging.error(f"设置系统设置失败: {e}")
            return False
    
    def get_post_fee(self):
        """获取发布费用"""
        try:
            fee_str = self.get_system_setting('post_fee', '1.0')
            return float(fee_str)
        except ValueError:
            logging.error("发布费用设置格式错误，使用默认值1.0")
            return 1.0
    
    def get_recharge_address(self):
        """获取充值地址"""
        from config import DEFAULT_RECHARGE_ADDRESS
        return self.get_system_setting('recharge_address', DEFAULT_RECHARGE_ADDRESS)
    
    def add_user(self, user_id, username=None, first_name=None, last_name=None):
        """添加用户"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # 先尝试插入新用户，如果用户已存在则忽略
                cursor.execute('''
                    INSERT OR IGNORE INTO users 
                    (user_id, username, first_name, last_name, balance) 
                    VALUES (?, ?, ?, ?, 0.0)
                ''', (user_id, username, first_name, last_name))
                
                # 如果用户已存在，只更新用户名和姓名，保留余额
                cursor.execute('''
                    UPDATE users 
                    SET username = ?, first_name = ?, last_name = ?
                    WHERE user_id = ?
                ''', (username, first_name, last_name, user_id))
                
                conn.commit()
                logging.info(f"用户 {user_id} 信息更新完成，余额已保留")
        except Exception as e:
            logging.error(f"添加用户失败: {e}")
    
    def is_user_banned(self, user_id):
        """检查用户是否被封禁"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                return result[0] if result else False
        except Exception as e:
            logging.error(f"检查用户封禁状态失败: {e}")
            return False
    
    def can_post_today(self, user_id, max_posts=5):
        """检查用户今天是否还能发布"""
        try:
            today = datetime.now().date()
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT post_count FROM daily_posts 
                    WHERE user_id = ? AND post_date = ?
                ''', (user_id, today))
                result = cursor.fetchone()
                current_count = result[0] if result else 0
                return current_count < max_posts
        except Exception as e:
            logging.error(f"检查发布限制失败: {e}")
            return True
    
    def add_submission(self, user_id, content):
        """添加投稿"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO submissions (user_id, content) 
                    VALUES (?, ?)
                ''', (user_id, content))
                submission_id = cursor.lastrowid
                conn.commit()
                return submission_id
        except Exception as e:
            logging.error(f"添加投稿失败: {e}")
            return None
    
    def update_daily_post_count(self, user_id):
        """更新每日发布计数"""
        try:
            today = datetime.now().date()
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_posts (user_id, post_date, post_count)
                    VALUES (?, ?, COALESCE((SELECT post_count FROM daily_posts 
                                          WHERE user_id = ? AND post_date = ?), 0) + 1)
                ''', (user_id, today, user_id, today))
                conn.commit()
        except Exception as e:
            logging.error(f"更新发布计数失败: {e}")
    
    def get_pending_submissions(self):
        """获取待审核的投稿"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s.id, s.user_id, s.content, s.submit_time, u.username, u.first_name
                    FROM submissions s
                    LEFT JOIN users u ON s.user_id = u.user_id
                    WHERE s.status = 'pending'
                    ORDER BY s.submit_time ASC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"获取待审核投稿失败: {e}")
            return []
    
    def approve_submission(self, submission_id, admin_comment=None):
        """通过投稿"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE submissions 
                    SET status = 'approved', admin_comment = ?
                    WHERE id = ?
                ''', (admin_comment, submission_id))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"通过投稿失败: {e}")
            return False
    
    def reject_submission(self, submission_id, admin_comment=None):
        """拒绝投稿"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE submissions 
                    SET status = 'rejected', admin_comment = ?
                    WHERE id = ?
                ''', (admin_comment, submission_id))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"拒绝投稿失败: {e}")
            return False
            
    def get_user_balance(self, user_id):
        """获取用户余额"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file, timeout=30.0)
            # 设置WAL模式和同步模式，确保数据一致性
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=FULL')
            cursor = conn.cursor()
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                balance = result[0] if result[0] is not None else 0.0
                logging.info(f"获取用户 {user_id} 余额: {balance}")
            else:
                balance = 0.0
                logging.warning(f"用户 {user_id} 不存在于数据库中，返回余额 0.0")
            return balance
        except Exception as e:
            logging.error(f"获取用户余额失败: {e}")
            return 0.0
        finally:
            if conn:
                conn.close()
            
    def add_user_balance(self, user_id, amount):
        """增加用户余额"""
        conn = None
        try:
            logging.info(f"开始为用户 {user_id} 增加余额 {amount}")
            conn = sqlite3.connect(self.db_file, timeout=30.0)
            # 设置WAL模式和同步模式，确保数据一致性
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=FULL')
            conn.execute('PRAGMA cache_size=10000')
            conn.execute('PRAGMA temp_store=memory')
            cursor = conn.cursor()
            
            # 确保用户存在
            cursor.execute('SELECT user_id, balance FROM users WHERE user_id = ?', (user_id,))
            user_data = cursor.fetchone()
            if not user_data:
                logging.info(f"用户 {user_id} 不存在，创建新用户")
                cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0.0))
                current_balance = 0.0
            else:
                current_balance = user_data[1] if user_data[1] is not None else 0.0
            
            new_balance = current_balance + float(amount)
            
            logging.info(f"用户 {user_id} 当前余额: {current_balance}, 增加: {amount}, 新余额: {new_balance}")
            
            # 更新余额
            cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
            
            # 显式提交事务
            conn.commit()
            logging.info(f"事务已提交")
            
            # 强制刷新到磁盘
            conn.execute('PRAGMA wal_checkpoint(FULL)')
            logging.info(f"WAL检查点已执行")
            
            # 验证更新结果
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            final_result = cursor.fetchone()
            final_balance = final_result[0] if final_result else 0.0
            logging.info(f"用户 {user_id} 最终余额: {final_balance}")
            
            return True
        except Exception as e:
            logging.error(f"增加用户余额失败: {e}")
            if conn:
                conn.rollback()
                logging.info(f"事务已回滚")
            return False
        finally:
            if conn:
                conn.close()
            
    def deduct_user_balance(self, user_id, amount):
        """扣减用户余额"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # 获取当前余额
                cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                if not result:
                    return False
                    
                current_balance = result[0]
                
                # 检查余额是否足够
                if current_balance < float(amount):
                    return False
                    
                # 扣减余额
                new_balance = current_balance - float(amount)
                cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"扣减用户余额失败: {e}")
            return False

    # ===== TRC20监听充值功能 =====
    
    def create_recharge_order(self, user_id, base_amount):
        """创建充值订单"""
        try:
            # 生成唯一订单ID
            order_id = f"TRX{int(time.time())}{random.randint(1000, 9999)}"
            
            # 生成精确到6位小数的随机金额
            random_decimal = random.randint(1, 999999) / 1000000.0
            exact_amount = base_amount + random_decimal
            
            # 计算过期时间（20分钟后）
            expire_time = datetime.now() + timedelta(minutes=20)
            
            # 获取充值地址
            wallet_address = self.get_recharge_address()
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO recharge_orders 
                    (user_id, order_id, base_amount, exact_amount, wallet_address, expire_time, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')
                ''', (user_id, order_id, base_amount, exact_amount, wallet_address, expire_time))
                conn.commit()
                
                logging.info(f"创建充值订单: 用户 {user_id}, 订单 {order_id}, 金额 {exact_amount:.6f}U")
                
                return {
                    'order_id': order_id,
                    'base_amount': base_amount,
                    'exact_amount': exact_amount,
                    'wallet_address': wallet_address,
                    'expire_time': expire_time
                }
                
        except Exception as e:
            logging.error(f"创建充值订单失败: {e}")
            return None
    
    def get_pending_orders(self):
        """获取所有待处理的订单"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT order_id, user_id, exact_amount, wallet_address, create_time, expire_time
                    FROM recharge_orders 
                    WHERE status = 'pending' AND expire_time > CURRENT_TIMESTAMP
                    ORDER BY create_time ASC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"获取待处理订单失败: {e}")
            return []
    
    def get_order_by_exact_amount(self, exact_amount):
        """根据精确金额查找订单"""
        try:
            # 由于浮点数精度问题，我们使用范围查询
            amount_min = exact_amount - 0.000001
            amount_max = exact_amount + 0.000001
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT order_id, user_id, base_amount, exact_amount, status, expire_time
                    FROM recharge_orders 
                    WHERE exact_amount BETWEEN ? AND ? 
                    AND status = 'pending'
                    AND expire_time > CURRENT_TIMESTAMP
                ''', (amount_min, amount_max))
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"根据金额查找订单失败: {e}")
            return None
    
    def mark_order_as_paid(self, order_id, transaction_hash):
        """标记订单为已支付"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # 获取订单信息
                cursor.execute('''
                    SELECT user_id, base_amount FROM recharge_orders 
                    WHERE order_id = ? AND status = 'pending'
                ''', (order_id,))
                order_data = cursor.fetchone()
                
                if not order_data:
                    return False
                
                user_id, base_amount = order_data
                
                # 更新订单状态
                cursor.execute('''
                    UPDATE recharge_orders 
                    SET status = 'paid', transaction_hash = ?, paid_time = CURRENT_TIMESTAMP
                    WHERE order_id = ?
                ''', (transaction_hash, order_id))
                
                # 增加用户余额
                success = self._add_user_balance_in_transaction(cursor, user_id, base_amount)
                
                if success:
                    conn.commit()
                    logging.info(f"订单 {order_id} 标记为已支付，为用户 {user_id} 增加余额 {base_amount}U")
                    return True
                else:
                    conn.rollback()
                    logging.error(f"订单 {order_id} 支付处理失败：增加余额失败")
                    return False
                    
        except Exception as e:
            logging.error(f"标记订单为已支付失败: {e}")
            return False
    
    def expire_old_orders(self):
        """将过期的订单标记为已过期"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE recharge_orders 
                    SET status = 'expired'
                    WHERE status = 'pending' AND expire_time <= CURRENT_TIMESTAMP
                ''')
                expired_count = cursor.rowcount
                conn.commit()
                
                if expired_count > 0:
                    logging.info(f"已标记 {expired_count} 个过期订单")
                
                return expired_count
        except Exception as e:
            logging.error(f"标记过期订单失败: {e}")
            return 0
    
    def get_user_orders(self, user_id, limit=10):
        """获取用户的充值订单"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT order_id, base_amount, exact_amount, status, create_time, expire_time, paid_time
                    FROM recharge_orders
                    WHERE user_id = ?
                    ORDER BY create_time DESC
                    LIMIT ?
                ''', (user_id, limit))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"获取用户订单失败: {e}")
            return []
    
    def _add_user_balance_in_transaction(self, cursor, user_id, amount):
        """在事务中增加用户余额（内部方法）"""
        try:
            # 确保用户存在
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            user_data = cursor.fetchone()
            if not user_data:
                cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0.0))
                current_balance = 0.0
            else:
                current_balance = user_data[0] if user_data[0] is not None else 0.0
            
            new_balance = current_balance + float(amount)
            
            # 更新余额
            cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
            
            logging.info(f"在事务中为用户 {user_id} 增加余额: 原余额 {current_balance} + {amount} = 新余额 {new_balance}")
            return True
        except Exception as e:
            logging.error(f"在事务中增加用户余额失败: {e}")
            return False
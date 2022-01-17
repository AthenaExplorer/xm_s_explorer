import os
import sys
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(BASE_DIR))
SECRET_KEY = 'm-nu-@adw)zt!z)wrfk$5r*kjmb2@0#bcmr!jv6=64xvid*5ga'

DEBUG = False
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "explorer",
    "exponent",
    "master_overview",
    "detail",
    "fad",
    "pro",
    "admin",
]

MIDDLEWARE = [
    'xm_s_common.middleware.ResponseMiddleware',
]

ROOT_URLCONF = 'xm_s_explorer.urls'
WSGI_APPLICATION = 'xm_s_explorer.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'xm_s_explorer',
        'USER': os.getenv("MYSQL_ROOT"),
        'PASSWORD': os.getenv("MYSQL_PASSWORD"),
        'HOST': os.getenv("MYSQL_HOST"),
        'PORT': os.getenv("MYSQL_PORT"),
        'CONN_MAX_AGE': 300,
        'OPTIONS': {'charset': 'utf8mb4'},
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_general_ci',
        }
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = False
STATIC_URL = '/static/'
logging.basicConfig(format='%(levelname)s:%(asctime)s %(pathname)s--%(funcName)s--line %(lineno)d-----%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.WARNING)

# warn sms

SMS_EXPIRE_HOURS = 24

SMS_CONTENT_FORMAT = {
    'power_inc_gt': '节点监控提醒\n{miner_no}（{label}）新增算力成本高于参考值30%\n实际成本：{cost} FIL/TiB\n参考值：{value} FIL/TiB\n【雅典娜浏览器】',
    'avg_reward_lt': '节点监控提醒\n{miner_no}（{label}）产出效率低于参考值30%\n实际产出效率：{avg_reward} FIL/TiB\n参考值：{value} FIL/TiB\n【雅典娜浏览器】',
    'fil_change_gt': '节点监控提醒\n{wallet_address}（{label}）有一笔1000FIL的资金流动\n账户余额：{fil_balance} FIL\n【雅典娜浏览器】',
    'fil_balance_lt': '节点监控提醒\n{wallet_address}（{label}）余额不足\n账户余额：{fil_balance} FIL\n【雅典娜浏览器】',
}

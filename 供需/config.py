import os
from dotenv import load_dotenv

load_dotenv()

# Bot配置
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))

# TRON API配置（用于监听交易）
TRONGRID_API_KEY = os.getenv('TRONGRID_API_KEY', '')
TRONSCAN_API_KEY = os.getenv('TRONSCAN_API_KEY', '')

# 发布频道ID配置
PUBLISH_CHANNEL_ID = os.getenv('PUBLISH_CHANNEL_ID')
PUBLISH_CHANNEL_2 = os.getenv('PUBLISH_CHANNEL_2')
PUBLISH_CHANNEL_3 = os.getenv('PUBLISH_CHANNEL_3')

def get_publish_channels():
    channels = []
    if PUBLISH_CHANNEL_ID:
        channels.append(PUBLISH_CHANNEL_ID)
    if PUBLISH_CHANNEL_2:
        channels.append(PUBLISH_CHANNEL_2)
    if PUBLISH_CHANNEL_3:
        channels.append(PUBLISH_CHANNEL_3)
    return channels

# 数据库配置
DATABASE_FILE = 'bot_data.db'

# 默认发布费用配置
DEFAULT_POST_FEE = float(os.getenv('DEFAULT_POST_FEE', '1.0'))

# 默认充值地址配置
DEFAULT_RECHARGE_ADDRESS = os.getenv('DEFAULT_RECHARGE_ADDRESS', 'TAK29Td16muq5zDQpHg6McTCXiUXTL3qxa')

# 投稿消息按钮配置
POST_BUTTONS = [
    {
        "text": "上押联系",
        "url": os.getenv('BUTTON_URL_1', 'https://t.me/lindi07133')
    },
    {
        "text": "瑟瑟频道",
        "url": os.getenv('BUTTON_URL_2', 'https://t.me/lindi07133')
    },
    {
        "text": "项目大群",
        "url": os.getenv('BUTTON_URL_3', 'https://t.me/lindi07133')
    },
    {
        "text": "人工发布",
        "url": os.getenv('BUTTON_URL_4', 'https://t.me/lindi07133')
    },
    {
        "text": "在押公群",
        "url": os.getenv('BUTTON_URL_5', 'https://t.me/lindi07133')
    }
]

# 消息模板
WELCOME_MESSAGE = """
🎉 欢迎供需全自动机器人

本机器人可以帮助您发布供需信息到指定频道和群组。
请点击下方按钮开始使用！

在本机器人遇到问题请联系在线客服！
"""
RULES_MESSAGE = """
📋 发布规则

1、不得发布虚假诈骗广告和假押广告，发现马上下架。
2、一条广告只能发布一个商品，行数不能超过16行。
3、推广链接不能是其他担保的公群，广告文案不能带有其他担保的名称
4、上押公群独享半价优惠 供需广告频道 

违规用户将被永久拉黑！
"""
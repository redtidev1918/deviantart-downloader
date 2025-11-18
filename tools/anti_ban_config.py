#!/usr/bin/env python3
"""
防封IP配置和工具 - Anti-Ban Configuration

提供智能速率限制、随机延迟、User-Agent 轮换等防封机制
"""

import random
import time
from typing import Optional
from dataclasses import dataclass


@dataclass
class AntiBanConfig:
    """防封配置"""
    
    # 基础延迟（秒）
    base_delay: float = 2.0
    
    # 随机延迟范围（在基础延迟上加随机值）
    random_delay_min: float = 0.5
    random_delay_max: float = 2.0
    
    # 每批次后的额外休息时间
    batch_rest_delay: float = 10.0
    batch_size: int = 10  # 每 N 个请求休息一次
    
    # 请求失败后的退避时间
    backoff_base: float = 5.0
    backoff_multiplier: float = 2.0
    max_backoff: float = 300.0  # 最多等5分钟
    
    # 429/503 错误特殊处理
    rate_limit_wait: float = 60.0  # 遇到429等1分钟
    
    # 并发控制
    max_concurrent: int = 2  # 最多同时2个请求
    
    # User-Agent 轮换
    rotate_user_agent: bool = True


# User-Agent 池（模拟不同浏览器）
USER_AGENTS = [
    # Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


class RateLimiter:
    """智能速率限制器"""
    
    def __init__(self, config: Optional[AntiBanConfig] = None):
        self.config = config or AntiBanConfig()
        self.request_count = 0
        self.last_request_time = 0
        self.consecutive_errors = 0
        
    def wait_before_request(self):
        """请求前等待（智能延迟）"""
        # 计算延迟时间
        delay = self._calculate_delay()
        
        # 如果距离上次请求时间太短，额外等待
        time_since_last = time.time() - self.last_request_time
        if time_since_last < delay:
            additional_wait = delay - time_since_last
            print(f"⏱️  等待 {additional_wait:.1f} 秒...")
            time.sleep(additional_wait)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
        # 每批次后额外休息
        if self.request_count % self.config.batch_size == 0:
            print(f"📦 已完成 {self.request_count} 个请求，休息 {self.config.batch_rest_delay} 秒...")
            time.sleep(self.config.batch_rest_delay)
    
    def _calculate_delay(self) -> float:
        """计算延迟时间"""
        # 基础延迟 + 随机延迟
        delay = self.config.base_delay
        
        if self.config.random_delay_max > 0:
            random_delay = random.uniform(
                self.config.random_delay_min,
                self.config.random_delay_max
            )
            delay += random_delay
        
        # 如果有连续错误，增加延迟（指数退避）
        if self.consecutive_errors > 0:
            backoff = min(
                self.config.backoff_base * (self.config.backoff_multiplier ** self.consecutive_errors),
                self.config.max_backoff
            )
            delay += backoff
            print(f"⚠️  连续错误 {self.consecutive_errors} 次，额外等待 {backoff:.1f} 秒")
        
        return delay
    
    def on_success(self):
        """请求成功后调用"""
        self.consecutive_errors = 0
    
    def on_error(self, error_code: Optional[int] = None):
        """请求失败后调用"""
        self.consecutive_errors += 1
        
        # 特殊错误码处理
        if error_code == 429:  # Too Many Requests
            print(f"🚫 遇到速率限制 (429)，等待 {self.config.rate_limit_wait} 秒...")
            time.sleep(self.config.rate_limit_wait)
        elif error_code == 503:  # Service Unavailable
            print(f"⚠️  服务不可用 (503)，等待 {self.config.rate_limit_wait / 2} 秒...")
            time.sleep(self.config.rate_limit_wait / 2)
    
    def get_random_user_agent(self) -> str:
        """获取随机 User-Agent"""
        if self.config.rotate_user_agent:
            return random.choice(USER_AGENTS)
        return USER_AGENTS[0]
    
    def reset(self):
        """重置计数器"""
        self.request_count = 0
        self.consecutive_errors = 0
        print("🔄 速率限制器已重置")


# 预设配置
class PresetConfigs:
    """预设的防封配置"""
    
    @staticmethod
    def conservative() -> AntiBanConfig:
        """保守模式 - 最安全但最慢"""
        return AntiBanConfig(
            base_delay=3.0,
            random_delay_min=1.0,
            random_delay_max=3.0,
            batch_rest_delay=30.0,
            batch_size=5,
            max_concurrent=1,
        )
    
    @staticmethod
    def balanced() -> AntiBanConfig:
        """平衡模式 - 推荐使用"""
        return AntiBanConfig(
            base_delay=2.0,
            random_delay_min=0.5,
            random_delay_max=2.0,
            batch_rest_delay=15.0,
            batch_size=10,
            max_concurrent=2,
        )
    
    @staticmethod
    def aggressive() -> AntiBanConfig:
        """激进模式 - 较快但有风险"""
        return AntiBanConfig(
            base_delay=1.0,
            random_delay_min=0.2,
            random_delay_max=1.0,
            batch_rest_delay=10.0,
            batch_size=20,
            max_concurrent=3,
        )
    
    @staticmethod
    def stealth() -> AntiBanConfig:
        """隐身模式 - 模拟真人浏览"""
        return AntiBanConfig(
            base_delay=5.0,
            random_delay_min=2.0,
            random_delay_max=8.0,
            batch_rest_delay=60.0,
            batch_size=3,
            max_concurrent=1,
            rotate_user_agent=True,
        )


def print_anti_ban_guide():
    """打印防封指南"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    防封IP完全指南 - Anti-Ban Guide                    ║
╚══════════════════════════════════════════════════════════════════════╝

🎯 核心原则

1. 降低请求频率
   • 设置合理的延迟（推荐 2-5 秒）
   • 添加随机延迟（避免规律性）
   • 批次间休息（每 10-20 个请求休息）

2. 模拟真实行为
   • 轮换 User-Agent
   • 随机化请求时间
   • 避免深夜大量请求

3. 错误处理
   • 遇到 429/503 立即停止
   • 使用指数退避重试
   • 记录失败请求稍后重试

4. 分散请求
   • 使用代理（可选）
   • 限制并发数量
   • 分多天下载大量内容

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 推荐配置

【保守模式】- 最安全（适合大量下载）
  --delay=3 --limit=10
  特点：慢但稳，几乎不会被封

【平衡模式】- 推荐（日常使用）
  --delay=2 --limit=24
  特点：速度和安全的平衡

【激进模式】- 快速（小量下载）
  --delay=1 --limit=50
  特点：快但有风险，适合少量下载

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ 实用命令示例

# 1. 保守下载（推荐新手）
python main.py gallery username --delay=3 --limit=10 --ask=0

# 2. 使用随机延迟（Python 脚本）
python deviantart_downloader.py gallery username --delay=2

# 3. 分批下载（每次 50 个，分多次）
python main.py gallery username --limit=50 --offset=0
python main.py gallery username --limit=50 --offset=50
python main.py gallery username --limit=50 --offset=100

# 4. 通过代理（避免IP被封）
python main.py gallery username --proxy=http://127.0.0.1:7890

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 警告信号（表示可能被限流）

  🚫 收到 429 错误 (Too Many Requests)
     → 立即停止，等待 1-2 小时后继续
  
  ⚠️  收到 503 错误 (Service Unavailable)
     → 停止 30 分钟后重试
  
  🐢 请求变慢或超时增加
     → 减少并发，增加延迟
  
  🔒 需要验证码
     → 停止至少 24 小时

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ 高级防护策略

1. 使用代理池
   • 轮换多个代理IP
   • 避免单IP过度使用

2. 分时段下载
   • 避开高峰期（北京时间 20:00-24:00）
   • 分散到多天完成

3. 监控请求
   • 记录每次请求时间
   • 发现异常立即停止

4. Cookie 管理
   • 定期更新 Cookie
   • 避免 Cookie 过期导致大量401错误

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 最佳实践

✅ 推荐做法：
  • 延迟设置 >= 2 秒
  • 每 10-20 个请求休息 10-30 秒
  • 下载前先测试几个文件
  • 使用 --ask=0 批量下载时更要小心
  • 大量下载分多天进行

❌ 避免做法：
  • 延迟 < 1 秒（很容易被封）
  • 并发 > 5 个（过于激进）
  • 深夜大批量请求（容易被检测）
  • 遇到错误继续强行请求
  • 短时间内下载数百个文件

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 被封后的恢复

如果IP被封：
  1. 立即停止所有请求
  2. 等待 24-48 小时
  3. 更换IP（重启路由器或使用代理）
  4. 降低请求频率重新开始
  5. 考虑使用移动网络（4G/5G）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

记住：宁可慢一点，也不要被封IP！
""")


if __name__ == "__main__":
    print_anti_ban_guide()
    
    print("\n" + "="*70)
    print("配置示例：")
    print("="*70 + "\n")
    
    configs = {
        "保守模式": PresetConfigs.conservative(),
        "平衡模式": PresetConfigs.balanced(),
        "激进模式": PresetConfigs.aggressive(),
        "隐身模式": PresetConfigs.stealth(),
    }
    
    for name, config in configs.items():
        print(f"【{name}】")
        print(f"  基础延迟: {config.base_delay}s")
        print(f"  随机延迟: {config.random_delay_min}-{config.random_delay_max}s")
        print(f"  批次大小: {config.batch_size}")
        print(f"  批次休息: {config.batch_rest_delay}s")
        print(f"  最大并发: {config.max_concurrent}")
        print()

"""下载进度管理模块 - 支持断点续传"""

import json
import logging
from pathlib import Path
from typing import Dict, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ProgressManager:
    """下载进度管理器"""
    
    def __init__(self, session_name: str, progress_dir: Path = None):
        """
        初始化进度管理器
        
        Args:
            session_name: 会话名称（如用户名）
            progress_dir: 进度文件保存目录
        """
        self.session_name = session_name
        self.progress_dir = progress_dir or Path.home() / '.deviantart_dl' / 'progress'
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        
        self.progress_file = self.progress_dir / f"{session_name}.json"
        self.data = self._load()
    
    def _load(self) -> Dict:
        """加载进度文件"""
        if not self.progress_file.exists():
            return {
                'session_name': self.session_name,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'downloaded': set(),
                'failed': {},
                'skipped': set(),
                'last_offset': 0,
                'last_cursor': ''
            }
        
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 转换列表为集合
                data['downloaded'] = set(data.get('downloaded', []))
                data['skipped'] = set(data.get('skipped', []))
                data['failed'] = data.get('failed', {})
                return data
        except Exception as e:
            logger.warning(f"Failed to load progress file: {e}")
            return self._load()
    
    def save(self):
        """保存进度到文件"""
        try:
            data = {
                'session_name': self.session_name,
                'created_at': self.data.get('created_at'),
                'last_updated': datetime.now().isoformat(),
                'downloaded': list(self.data['downloaded']),
                'failed': self.data['failed'],
                'skipped': list(self.data['skipped']),
                'last_offset': self.data['last_offset'],
                'last_cursor': self.data['last_cursor']
            }
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Progress saved to {self.progress_file}")
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def is_downloaded(self, deviation_id: str) -> bool:
        """检查作品是否已下载"""
        return deviation_id in self.data['downloaded']
    
    def is_failed(self, deviation_id: str) -> bool:
        """检查作品是否下载失败"""
        return deviation_id in self.data['failed']
    
    def get_retry_count(self, deviation_id: str) -> int:
        """获取重试次数"""
        if deviation_id in self.data['failed']:
            return self.data['failed'][deviation_id].get('retry_count', 0)
        return 0
    
    def mark_downloaded(self, deviation_id: str):
        """标记作品已下载"""
        self.data['downloaded'].add(deviation_id)
        # 从失败列表移除
        if deviation_id in self.data['failed']:
            del self.data['failed'][deviation_id]
        self.save()
    
    def mark_failed(self, deviation_id: str, error: str):
        """标记作品下载失败"""
        if deviation_id not in self.data['failed']:
            self.data['failed'][deviation_id] = {
                'retry_count': 1,
                'last_error': error,
                'last_attempt': datetime.now().isoformat()
            }
        else:
            self.data['failed'][deviation_id]['retry_count'] += 1
            self.data['failed'][deviation_id]['last_error'] = error
            self.data['failed'][deviation_id]['last_attempt'] = datetime.now().isoformat()
        
        self.save()
    
    def mark_skipped(self, deviation_id: str):
        """标记作品跳过"""
        self.data['skipped'].add(deviation_id)
        self.save()
    
    def update_position(self, offset: int, cursor: str = ''):
        """更新下载位置"""
        self.data['last_offset'] = offset
        self.data['last_cursor'] = cursor
        self.save()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'downloaded': len(self.data['downloaded']),
            'failed': len(self.data['failed']),
            'skipped': len(self.data['skipped']),
            'total': len(self.data['downloaded']) + len(self.data['failed']) + len(self.data['skipped'])
        }
    
    def clear(self):
        """清除进度"""
        if self.progress_file.exists():
            self.progress_file.unlink()
            logger.info(f"Progress cleared: {self.progress_file}")
    
    def should_retry(self, deviation_id: str, max_retries: int = 3) -> bool:
        """判断是否应该重试"""
        retry_count = self.get_retry_count(deviation_id)
        return retry_count < max_retries

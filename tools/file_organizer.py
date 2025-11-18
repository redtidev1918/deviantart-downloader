#!/usr/bin/env python3
"""
文件组织器 - 智能管理下载的文件
File Organizer - Smart management for downloaded files

支持多种组织模式:
- 按作者分类 (by_author)
- 按日期分类 (by_date)
- 按类型分类 (by_type)
- 按画廊分类 (by_gallery)
- 扁平结构 (flat)
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
from urllib.parse import quote


class FileOrganizer:
    """文件组织器"""
    
    MODES = {
        'by_author': '按作者分类',
        'by_date': '按日期分类',
        'by_type': '按类型分类',
        'by_gallery': '按画廊分类',
        'flat': '扁平结构',
        'mixed': '混合模式'
    }
    
    def __init__(self, base_dir: str = './downloads', mode: str = 'by_author'):
        """
        初始化文件组织器
        
        Args:
            base_dir: 基础下载目录
            mode: 组织模式
        """
        self.base_dir = Path(base_dir)
        self.mode = mode if mode in self.MODES else 'by_author'
        self.metadata_dir = self.base_dir / '.metadata'
        
        # 创建基础目录
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    def get_file_path(
        self,
        filename: str,
        author: Optional[str] = None,
        date: Optional[str] = None,
        category: Optional[str] = None,
        gallery: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> Path:
        """
        根据组织模式获取文件应该保存的路径
        
        Args:
            filename: 原始文件名
            author: 作者名
            date: 日期 (YYYY-MM-DD)
            category: 分类
            gallery: 画廊名
            file_type: 文件类型 (image, video, document, etc.)
        
        Returns:
            完整的文件路径
        """
        # 清理文件名
        safe_filename = self._sanitize_filename(filename)
        
        if self.mode == 'by_author':
            # 按作者: downloads/author_name/filename
            if author:
                safe_author = self._sanitize_filename(author)
                return self.base_dir / safe_author / safe_filename
            else:
                return self.base_dir / 'unknown' / safe_filename
        
        elif self.mode == 'by_date':
            # 按日期: downloads/YYYY/MM/DD/filename
            if date:
                try:
                    dt = datetime.fromisoformat(date)
                    return self.base_dir / str(dt.year) / f"{dt.month:02d}" / f"{dt.day:02d}" / safe_filename
                except:
                    pass
            # 默认使用今天
            today = datetime.now()
            return self.base_dir / str(today.year) / f"{today.month:02d}" / f"{today.day:02d}" / safe_filename
        
        elif self.mode == 'by_type':
            # 按类型: downloads/images/filename, downloads/videos/filename
            if not file_type:
                # 从扩展名推断
                ext = Path(safe_filename).suffix.lower()
                file_type = self._get_type_from_ext(ext)
            
            return self.base_dir / file_type / safe_filename
        
        elif self.mode == 'by_gallery':
            # 按画廊: downloads/author/gallery_name/filename
            if author and gallery:
                safe_author = self._sanitize_filename(author)
                safe_gallery = self._sanitize_filename(gallery)
                return self.base_dir / safe_author / safe_gallery / safe_filename
            elif author:
                safe_author = self._sanitize_filename(author)
                return self.base_dir / safe_author / 'default' / safe_filename
            else:
                return self.base_dir / 'unknown' / safe_filename
        
        elif self.mode == 'mixed':
            # 混合模式: downloads/author/YYYY-MM/filename
            if author and date:
                safe_author = self._sanitize_filename(author)
                try:
                    dt = datetime.fromisoformat(date)
                    date_folder = f"{dt.year}-{dt.month:02d}"
                except:
                    date_folder = datetime.now().strftime("%Y-%m")
                return self.base_dir / safe_author / date_folder / safe_filename
            elif author:
                safe_author = self._sanitize_filename(author)
                return self.base_dir / safe_author / safe_filename
            else:
                return self.base_dir / safe_filename
        
        else:  # flat
            # 扁平结构: downloads/filename
            return self.base_dir / safe_filename
    
    def organize_file(
        self,
        source_path: str,
        filename: str,
        metadata: Optional[Dict] = None,
        move: bool = False
    ) -> Tuple[Path, bool]:
        """
        组织文件到正确的位置
        
        Args:
            source_path: 源文件路径
            filename: 目标文件名
            metadata: 文件元数据
            move: 是否移动（True）还是复制（False）
        
        Returns:
            (目标路径, 是否成功)
        """
        metadata = metadata or {}
        
        # 获取目标路径
        target_path = self.get_file_path(
            filename=filename,
            author=metadata.get('author'),
            date=metadata.get('date'),
            category=metadata.get('category'),
            gallery=metadata.get('gallery'),
            file_type=metadata.get('type')
        )
        
        # 确保目标目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 处理文件名冲突
        if target_path.exists():
            target_path = self._handle_conflict(target_path)
        
        try:
            # 移动或复制文件
            if move:
                shutil.move(source_path, target_path)
            else:
                shutil.copy2(source_path, target_path)
            
            # 保存元数据
            if metadata:
                self._save_metadata(target_path, metadata)
            
            return target_path, True
        except Exception as e:
            print(f"错误: 无法组织文件: {e}")
            return Path(source_path), False
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除不安全字符"""
        # 替换不安全字符
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # 移除首尾空格和点
        filename = filename.strip('. ')
        
        # 限制长度
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        return filename or 'unnamed'
    
    def _get_type_from_ext(self, ext: str) -> str:
        """从扩展名推断文件类型"""
        ext = ext.lower()
        
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff'}
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
        document_exts = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
        archive_exts = {'.zip', '.rar', '.7z', '.tar', '.gz'}
        
        if ext in image_exts:
            return 'images'
        elif ext in video_exts:
            return 'videos'
        elif ext in document_exts:
            return 'documents'
        elif ext in archive_exts:
            return 'archives'
        else:
            return 'others'
    
    def _handle_conflict(self, path: Path) -> Path:
        """处理文件名冲突"""
        name = path.stem
        ext = path.suffix
        parent = path.parent
        
        counter = 1
        new_path = path
        
        while new_path.exists():
            new_name = f"{name}_{counter}{ext}"
            new_path = parent / new_name
            counter += 1
        
        return new_path
    
    def _save_metadata(self, file_path: Path, metadata: Dict):
        """保存文件元数据"""
        # 使用文件名作为元数据文件名
        meta_filename = file_path.stem + '.json'
        meta_path = self.metadata_dir / meta_filename
        
        # 添加文件信息
        metadata['file_path'] = str(file_path)
        metadata['organized_at'] = datetime.now().isoformat()
        metadata['file_size'] = file_path.stat().st_size if file_path.exists() else 0
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def get_metadata(self, filename: str) -> Optional[Dict]:
        """获取文件元数据"""
        meta_filename = Path(filename).stem + '.json'
        meta_path = self.metadata_dir / meta_filename
        
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def create_structure_info(self) -> str:
        """创建目录结构说明"""
        info = f"""
下载目录结构说明 ({self.mode})
{'=' * 70}

基础目录: {self.base_dir}
组织模式: {self.MODES[self.mode]}

"""
        
        if self.mode == 'by_author':
            info += """
结构示例:
downloads/
  ├── artist_name_1/
  │   ├── artwork_1.jpg
  │   ├── artwork_2.png
  │   └── artwork_3.gif
  ├── artist_name_2/
  │   └── artwork_4.jpg
  └── .metadata/
      └── artwork_1.json
"""
        
        elif self.mode == 'by_date':
            info += """
结构示例:
downloads/
  ├── 2025/
  │   ├── 01/
  │   │   ├── 15/
  │   │   │   └── artwork_1.jpg
  │   │   └── 16/
  │   │       └── artwork_2.png
  │   └── 02/
  └── .metadata/
"""
        
        elif self.mode == 'by_type':
            info += """
结构示例:
downloads/
  ├── images/
  │   ├── artwork_1.jpg
  │   └── artwork_2.png
  ├── videos/
  │   └── animation_1.mp4
  └── .metadata/
"""
        
        elif self.mode == 'by_gallery':
            info += """
结构示例:
downloads/
  ├── artist_name/
  │   ├── gallery_name_1/
  │   │   ├── artwork_1.jpg
  │   │   └── artwork_2.png
  │   └── gallery_name_2/
  │       └── artwork_3.jpg
  └── .metadata/
"""
        
        elif self.mode == 'mixed':
            info += """
结构示例:
downloads/
  ├── artist_name_1/
  │   ├── 2025-01/
  │   │   ├── artwork_1.jpg
  │   │   └── artwork_2.png
  │   └── 2025-02/
  │       └── artwork_3.jpg
  └── .metadata/
"""
        
        else:  # flat
            info += """
结构示例:
downloads/
  ├── artwork_1.jpg
  ├── artwork_2.png
  ├── artwork_3.gif
  └── .metadata/
"""
        
        info += f"""
元数据文件:
- 位置: {self.metadata_dir}
- 格式: JSON
- 内容: 作品信息、作者、日期、URL等

{'=' * 70}
"""
        return info


def main():
    """测试和演示"""
    import argparse
    
    parser = argparse.ArgumentParser(description='文件组织器')
    parser.add_argument('--mode', choices=list(FileOrganizer.MODES.keys()),
                        default='by_author', help='组织模式')
    parser.add_argument('--base-dir', default='./downloads', help='基础目录')
    parser.add_argument('--show-structure', action='store_true', help='显示目录结构')
    
    args = parser.parse_args()
    
    organizer = FileOrganizer(base_dir=args.base_dir, mode=args.mode)
    
    if args.show_structure:
        print(organizer.create_structure_info())
    else:
        # 演示不同场景
        print("=" * 70)
        print(f"  文件组织器演示 - 模式: {organizer.MODES[args.mode]}")
        print("=" * 70)
        print()
        
        # 示例1: 按作者
        path1 = organizer.get_file_path(
            filename="sunset_landscape.jpg",
            author="JohnDoe",
            date="2025-01-15"
        )
        print(f"示例1 (作者作品): {path1}")
        
        # 示例2: 视频
        path2 = organizer.get_file_path(
            filename="animation.mp4",
            author="AnimatorX",
            file_type="video"
        )
        print(f"示例2 (视频文件): {path2}")
        
        # 示例3: 画廊
        path3 = organizer.get_file_path(
            filename="character_design.png",
            author="ArtistY",
            gallery="Character Designs 2025"
        )
        print(f"示例3 (画廊作品): {path3}")
        
        print()
        print("=" * 70)
        print()
        print(organizer.create_structure_info())


if __name__ == '__main__':
    main()

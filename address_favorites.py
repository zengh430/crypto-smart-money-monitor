"""
地址收藏管理模块 / Address Favorites Management Module
用于管理用户收藏的智能钱包地址
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class AddressFavorites:
    """地址收藏管理类"""

    def __init__(self, data_file: str = "favorites.json"):
        """
        初始化地址收藏管理器

        Args:
            data_file: JSON数据文件路径
        """
        self.data_file = data_file
        self.favorites: Dict[str, Dict] = {}
        self.load_favorites()

    def load_favorites(self) -> None:
        """从文件加载收藏数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.favorites = json.load(f)
                print(f"已加载 {len(self.favorites)} 个收藏地址")
            except Exception as e:
                print(f"加载收藏数据失败: {e}")
                self.favorites = {}
        else:
            self.favorites = {}

    def save_favorites(self) -> bool:
        """保存收藏数据到文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存收藏数据失败: {e}")
            return False

    def add_favorite(self, address: str, note: str = "",
                    tags: List[str] = None, metadata: Dict = None) -> bool:
        """
        添加收藏地址

        Args:
            address: 钱包地址
            note: 备注信息
            tags: 标签列表
            metadata: 其他元数据（如发现时的持仓信息等）

        Returns:
            bool: 是否添加成功
        """
        if not address:
            return False

        # 如果已存在，则更新
        if address in self.favorites:
            self.favorites[address]['note'] = note
            self.favorites[address]['tags'] = tags or []
            self.favorites[address]['updated_at'] = datetime.now().isoformat()
            if metadata:
                self.favorites[address]['metadata'].update(metadata)
        else:
            # 新增收藏
            self.favorites[address] = {
                'address': address,
                'note': note,
                'tags': tags or [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }

        return self.save_favorites()

    def remove_favorite(self, address: str) -> bool:
        """
        删除收藏地址

        Args:
            address: 钱包地址

        Returns:
            bool: 是否删除成功
        """
        if address in self.favorites:
            del self.favorites[address]
            return self.save_favorites()
        return False

    def get_favorite(self, address: str) -> Optional[Dict]:
        """
        获取单个收藏地址的详细信息

        Args:
            address: 钱包地址

        Returns:
            Dict: 收藏地址信息，如果不存在则返回None
        """
        return self.favorites.get(address)

    def is_favorite(self, address: str) -> bool:
        """
        检查地址是否已收藏

        Args:
            address: 钱包地址

        Returns:
            bool: 是否已收藏
        """
        return address in self.favorites

    def get_all_favorites(self) -> List[Dict]:
        """
        获取所有收藏地址列表

        Returns:
            List[Dict]: 收藏地址列表，按更新时间倒序排列
        """
        favorites_list = list(self.favorites.values())
        # 按更新时间倒序排序
        favorites_list.sort(
            key=lambda x: x.get('updated_at', ''),
            reverse=True
        )
        return favorites_list

    def search_favorites(self, keyword: str = "", tags: List[str] = None) -> List[Dict]:
        """
        搜索收藏地址

        Args:
            keyword: 搜索关键词（在地址和备注中搜索）
            tags: 标签筛选

        Returns:
            List[Dict]: 匹配的收藏地址列表
        """
        results = []

        for fav in self.favorites.values():
            # 关键词匹配
            keyword_match = True
            if keyword:
                keyword_lower = keyword.lower()
                keyword_match = (
                    keyword_lower in fav['address'].lower() or
                    keyword_lower in fav['note'].lower()
                )

            # 标签匹配
            tags_match = True
            if tags:
                tags_match = any(tag in fav['tags'] for tag in tags)

            if keyword_match and tags_match:
                results.append(fav)

        # 按更新时间倒序排序
        results.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return results

    def update_metadata(self, address: str, metadata: Dict) -> bool:
        """
        更新地址的元数据

        Args:
            address: 钱包地址
            metadata: 要更新的元数据

        Returns:
            bool: 是否更新成功
        """
        if address in self.favorites:
            self.favorites[address]['metadata'].update(metadata)
            self.favorites[address]['updated_at'] = datetime.now().isoformat()
            return self.save_favorites()
        return False

    def get_statistics(self) -> Dict:
        """
        获取收藏统计信息

        Returns:
            Dict: 统计信息
        """
        all_tags = []
        for fav in self.favorites.values():
            all_tags.extend(fav.get('tags', []))

        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            'total_count': len(self.favorites),
            'tag_counts': tag_counts,
            'tags': list(set(all_tags))
        }

    def export_to_csv(self, filepath: str) -> bool:
        """
        导出收藏地址到CSV文件

        Args:
            filepath: CSV文件路径

        Returns:
            bool: 是否导出成功
        """
        try:
            import csv

            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow(['地址', '备注', '标签', '创建时间', '更新时间'])

                # 写入数据
                for fav in self.get_all_favorites():
                    writer.writerow([
                        fav['address'],
                        fav['note'],
                        ','.join(fav['tags']),
                        fav['created_at'],
                        fav['updated_at']
                    ])

            return True
        except Exception as e:
            print(f"导出CSV失败: {e}")
            return False

    def import_from_csv(self, filepath: str) -> int:
        """
        从CSV文件导入收藏地址

        Args:
            filepath: CSV文件路径

        Returns:
            int: 成功导入的数量
        """
        try:
            import csv

            count = 0
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    address = row.get('地址', '').strip()
                    if address:
                        tags = row.get('标签', '').strip()
                        tags_list = [t.strip() for t in tags.split(',') if t.strip()]

                        if self.add_favorite(
                            address=address,
                            note=row.get('备注', ''),
                            tags=tags_list
                        ):
                            count += 1

            return count
        except Exception as e:
            print(f"导入CSV失败: {e}")
            return 0

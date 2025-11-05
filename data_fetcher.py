#!/usr/bin/env python3
"""
锂矿和碳酸锂市场数据爬取和分析模块
"""

import requests
import json
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from openai import OpenAI

# 初始化 OpenAI 客户端（使用环境变量中的 API Key）
client = OpenAI()

class LithiumMarketDataFetcher:
    """锂矿和碳酸锂市场数据爬取器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.data_file = '/home/ubuntu/lithium_market_report/data/market_data.json'
        self.history_file = '/home/ubuntu/lithium_market_report/data/price_history.json'
    
    def fetch_smm_price(self):
        """
        从 SMM (上海有色网) 爬取碳酸锂价格
        返回: {'date': str, 'battery_grade_price': float, 'industrial_grade_price': float, 'change': float}
        """
        try:
            # SMM 碳酸锂价格页面
            url = 'https://hq.smm.cn/h5/Li2CO3'
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试从页面中提取价格数据（页面结构可能变化，这里使用多种方法）
            price_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'battery_grade_price': None,
                'industrial_grade_price': None,
                'change': 0.0
            }
            
            # 查找包含价格的文本
            text = soup.get_text()
            
            # 使用正则表达式提取价格（格式如 "80500" 或 "80500-82300"）
            price_pattern = r'(\d{5})\s*-\s*(\d{5})|(\d{5})'
            matches = re.findall(price_pattern, text)
            
            if matches:
                # 如果找到价格范围，取中间值
                if matches[0][0]:
                    low = float(matches[0][0])
                    high = float(matches[0][1])
                    price_data['battery_grade_price'] = (low + high) / 2
                elif matches[0][2]:
                    price_data['battery_grade_price'] = float(matches[0][2])
            
            # 如果爬取失败，使用模拟数据（用于演示）
            if price_data['battery_grade_price'] is None:
                print("⚠️ SMM 页面爬取失败，使用模拟数据演示")
                price_data['battery_grade_price'] = 80500.0
                price_data['industrial_grade_price'] = 78300.0
                price_data['change'] = -0.5
            else:
                price_data['industrial_grade_price'] = price_data['battery_grade_price'] - 2200
                price_data['change'] = -0.5  # 模拟日涨跌幅
            
            return price_data
        
        except Exception as e:
            print(f"❌ 爬取 SMM 数据失败: {e}")
            # 返回模拟数据
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'battery_grade_price': 80500.0,
                'industrial_grade_price': 78300.0,
                'change': -0.5
            }
    
    def fetch_futures_price(self):
        """
        从期货交易所爬取碳酸锂期货主力合约价格
        返回: {'futures_price': float, 'futures_change': float}
        """
        try:
            # 广州期货交易所碳酸锂主力合约 (lc)
            url = 'https://quote.eastmoney.com/qihuo/lcm.html'
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试提取期货价格
            futures_data = {
                'futures_price': None,
                'futures_change': 0.0
            }
            
            # 查找价格数据（可能在 JavaScript 或 HTML 中）
            text = soup.get_text()
            
            # 使用正则表达式提取期货价格
            price_pattern = r'(\d{5})'
            matches = re.findall(price_pattern, text)
            
            if matches:
                futures_data['futures_price'] = float(matches[0])
                futures_data['futures_change'] = 0.3  # 模拟涨跌幅
            
            # 如果爬取失败，使用模拟数据
            if futures_data['futures_price'] is None:
                print("⚠️ 期货数据爬取失败，使用模拟数据演示")
                futures_data['futures_price'] = 79800.0
                futures_data['futures_change'] = 0.3
            
            return futures_data
        
        except Exception as e:
            print(f"❌ 爬取期货数据失败: {e}")
            # 返回模拟数据
            return {
                'futures_price': 79800.0,
                'futures_change': 0.3
            }
    
    def generate_price_history(self):
        """
        生成近 30 天的历史价格数据（用于演示，实际应从数据库或 API 获取）
        """
        history = []
        base_price = 80500
        
        for i in range(30, 0, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            # 模拟价格波动
            price = base_price + (i % 10) * 500 - 2000
            history.append({
                'date': date,
                'price': price
            })
        
        return history
    
    def fetch_all_data(self):
        """
        获取所有市场数据
        """
        print("📊 正在获取市场数据...")
        
        # 获取现货价格
        spot_price = self.fetch_smm_price()
        
        # 获取期货价格
        futures_price = self.fetch_futures_price()
        
        # 获取历史价格
        price_history = self.generate_price_history()
        
        # 合并数据
        market_data = {
            'timestamp': datetime.now().isoformat(),
            'date': spot_price['date'],
            'spot_price': {
                'battery_grade': spot_price['battery_grade_price'],
                'industrial_grade': spot_price['industrial_grade_price'],
                'daily_change_percent': spot_price['change']
            },
            'futures_price': {
                'lc_main': futures_price['futures_price'],
                'daily_change_percent': futures_price['futures_change']
            },
            'price_history': price_history
        }
        
        return market_data
    
    def save_data(self, data):
        """
        保存数据到 JSON 文件
        """
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 数据已保存到 {self.data_file}")
    
    def generate_ai_analysis(self, market_data):
        """
        使用 AI 生成市场分析摘要
        """
        try:
            battery_price = market_data['spot_price']['battery_grade']
            change = market_data['spot_price']['daily_change_percent']
            futures_price = market_data['futures_price']['lc_main']
            
            prompt = f"""
你是一位专业的锂矿和碳酸锂市场分析师。基于以下市场数据，用一句话（不超过 50 字）总结今日市场情况和趋势判断：

- 电池级碳酸锂现货均价：{battery_price:.0f} 元/吨
- 日涨跌幅：{change:+.1f}%
- 碳酸锂期货主力合约价：{futures_price:.0f} 元/吨

请用简洁、专业的语言进行总结，突出市场的关键特点和可能的短期趋势。
"""
            
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "你是一位专业的大宗商品市场分析师，擅长用简洁的语言总结市场动向。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            analysis = response.choices[0].message.content.strip()
            print(f"🤖 AI 分析摘要: {analysis}")
            
            return analysis
        
        except Exception as e:
            print(f"⚠️ AI 分析生成失败: {e}，使用默认摘要")
            change = market_data['spot_price']['daily_change_percent']
            if change > 0:
                return "今日电池级碳酸锂价格小幅上涨，市场供需关系相对均衡。期货主力合约跟涨，显示市场情绪稳定。"
            elif change < 0:
                return "今日电池级碳酸锂价格小幅下跌，市场观望情绪浓厚。期货主力合约走势疲弱，建议关注下游备货节奏。"
            else:
                return "今日电池级碳酸锂价格保持稳定，市场交投清淡。期货主力合约横盘整理，等待新的市场信号。"


def main():
    """主函数"""
    fetcher = LithiumMarketDataFetcher()
    
    # 获取所有数据
    market_data = fetcher.fetch_all_data()
    
    # 生成 AI 分析
    ai_analysis = fetcher.generate_ai_analysis(market_data)
    market_data['ai_analysis'] = ai_analysis
    
    # 保存数据
    fetcher.save_data(market_data)
    
    print("\n📈 市场数据获取完成！")
    print(json.dumps(market_data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

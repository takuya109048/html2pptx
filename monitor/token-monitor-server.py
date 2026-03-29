#!/usr/bin/env python3
"""
Claude Code Token Monitor Server
トークン使用量ログをリアルタイムで提供するバックエンドサーバー
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)

# ログファイルパス
LOG_FILE = os.path.expanduser('~/.claude/token-usage.log')

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """ログファイルの内容を JSON で返す"""
    logs = []

    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        return jsonify({
            'error': str(e),
            'logs': [],
            'timestamp': datetime.now().isoformat()
        }), 500

    return jsonify({
        'logs': logs,
        'total_calls': len(logs),
        'estimated_tokens': len(logs) * 300,
        'timestamp': datetime.now().isoformat(),
        'log_file': LOG_FILE
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """統計情報を返す"""
    logs = []

    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # 時間別統計
    hourly_stats = {}
    for log in logs:
        try:
            # [YYYY-MM-DD HH:MM:SS] から HH を抽出
            time_part = log.split(']')[0].replace('[', '')
            hour = time_part.split(':')[0] if ':' in time_part else 'unknown'
            hourly_stats[hour] = hourly_stats.get(hour, 0) + 1
        except:
            pass

    # 最新ログを取得
    last_log = logs[-1] if logs else None
    last_call_time = None
    if last_log:
        try:
            last_call_time = last_log.split(']')[0].replace('[', '')
        except:
            pass

    # 平均呼び出し間隔を計算
    avg_interval = None
    if len(logs) > 1:
        try:
            intervals = []
            for i in range(1, len(logs)):
                time1_str = logs[i-1].split(']')[0].replace('[', '')
                time2_str = logs[i].split(']')[0].replace('[', '')
                # HH:MM:SS を秒に変換
                def time_to_seconds(t):
                    parts = t.split(':')
                    return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
                try:
                    sec1 = time_to_seconds(time1_str.split()[-1])
                    sec2 = time_to_seconds(time2_str.split()[-1])
                    intervals.append(sec2 - sec1)
                except:
                    pass

            if intervals:
                avg_interval = sum(intervals) / len(intervals)
        except:
            pass

    return jsonify({
        'total_calls': len(logs),
        'estimated_tokens': len(logs) * 300,
        'last_call_time': last_call_time,
        'average_interval_seconds': round(avg_interval, 1) if avg_interval else None,
        'hourly_distribution': hourly_stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/health', methods=['GET'])
def health():
    """ヘルスチェック"""
    return jsonify({
        'status': 'ok',
        'server_time': datetime.now().isoformat(),
        'log_file_exists': os.path.exists(LOG_FILE),
        'log_file_path': LOG_FILE
    })

@app.route('/', methods=['GET'])
def index():
    """サーバー情報を返す"""
    return jsonify({
        'name': 'Claude Code Token Monitor Server',
        'version': '1.0.0',
        'endpoints': {
            '/api/logs': 'Get all logs',
            '/api/stats': 'Get statistics',
            '/api/health': 'Health check'
        },
        'server_time': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════╗
║     Claude Code Token Monitor Server が起動しました       ║
╚════════════════════════════════════════════════════════════╝

📊 エンドポイント:
  - http://localhost:5555/api/logs   : ログ取得
  - http://localhost:5555/api/stats  : 統計情報
  - http://localhost:5555/api/health : ヘルスチェック

📁 ログファイル:
  - {0}

🌐 ダッシュボード:
  - token-monitor.html をブラウザで開く

⏹️  停止: Ctrl+C
    """.format(LOG_FILE))

    app.run(host='127.0.0.1', port=5555, debug=False)

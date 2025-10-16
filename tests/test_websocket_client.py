"""
WebSocket 客戶端測試腳本

模擬設備連接到推送服務並接收命令

使用方法：
1. 確保推送服務正在運行: python app_push_service.py
2. 運行此腳本: python test_websocket_client.py
3. 在另一個終端使用 curl 測試推送命令
"""

import socketio
import time
import sys
from datetime import datetime

# 創建 Socket.IO 客戶端
sio = socketio.Client()

# 設備 ID（可以通過命令行參數指定）
DEVICE_ID = sys.argv[1] if len(sys.argv) > 1 else "taxi-AAB-1234-rooftop"

# ============================================================================
# 事件處理器
# ============================================================================

@sio.event
def connect():
    """連接成功事件"""
    print(f"\n✅ 已連接到服務器")
    print(f"⏰ 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)


@sio.event
def connection_established(data):
    """接收連接建立確認"""
    print(f"\n📡 收到連接確認:")
    print(f"   消息: {data.get('message')}")
    print(f"   SID: {data.get('sid')}")
    print(f"   時間: {data.get('timestamp')}")
    print("-" * 60)
    
    # 立即註冊設備
    print(f"\n📝 正在註冊設備: {DEVICE_ID}")
    sio.emit('register', {'device_id': DEVICE_ID})


@sio.event
def registration_success(data):
    """註冊成功"""
    print(f"\n✅ 設備註冊成功!")
    print(f"   設備 ID: {data.get('device_id')}")
    print(f"   設備類型: {data.get('device_type')}")
    print(f"   時間: {data.get('timestamp')}")
    print("-" * 60)
    print(f"\n🎬 等待接收推送命令...")
    print(f"💡 提示: 使用以下命令測試推送:")
    print(f"""
    curl -X POST http://localhost:5001/api/v1/admin/override \\
      -H "Content-Type: application/json" \\
      -d '{{"target_device_ids": ["{DEVICE_ID}"], "advertisement_id": "adv-002"}}'
    """)
    print("-" * 60)


@sio.event
def registration_error(data):
    """註冊失敗"""
    print(f"\n❌ 設備註冊失敗!")
    print(f"   錯誤: {data.get('error')}")
    print("-" * 60)


@sio.event
def play_override(data):
    """接收播放覆蓋命令 - 這是主要功能！"""
    print(f"\n" + "=" * 60)
    print(f"🚨 收到主動推送命令!")
    print("=" * 60)
    print(f"   命令: {data.get('command')}")
    print(f"   視頻文件: {data.get('video_filename')}")
    print(f"   廣告 ID: {data.get('advertisement_id')}")
    print(f"   廣告名稱: {data.get('advertisement_name')}")
    print(f"   優先級: {data.get('priority')}")
    print(f"   時間戳: {data.get('timestamp')}")
    print("=" * 60)
    print(f"🎥 現在應該播放視頻: {data.get('video_filename')}")
    print("=" * 60 + "\n")


@sio.event
def heartbeat_ack(data):
    """心跳確認"""
    print(f"💓 心跳確認: {data.get('timestamp')}")


@sio.event
def disconnect():
    """斷開連接事件"""
    print(f"\n❌ 已斷開連接")
    print(f"⏰ 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)


@sio.event
def error(data):
    """錯誤事件"""
    print(f"\n⚠️  收到錯誤:")
    print(f"   {data.get('error')}")
    print("-" * 60)


# ============================================================================
# 主程序
# ============================================================================

def main():
    """主函數"""
    server_url = 'http://localhost:5001'
    
    print("\n" + "=" * 60)
    print("WebSocket 客戶端測試程序")
    print("=" * 60)
    print(f"設備 ID: {DEVICE_ID}")
    print(f"服務器: {server_url}")
    print("=" * 60)
    
    try:
        # 連接到服務器
        print(f"\n🔌 正在連接到服務器...")
        sio.connect(server_url)
        
        # 保持連接並定期發送心跳
        while True:
            time.sleep(30)  # 每 30 秒發送一次心跳
            if sio.connected:
                sio.emit('heartbeat', {
                    'device_id': DEVICE_ID,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                print("⚠️  連接已斷開，嘗試重新連接...")
                break
                
    except KeyboardInterrupt:
        print("\n\n👋 收到中斷信號，正在斷開連接...")
        if sio.connected:
            sio.disconnect()
        print("✅ 程序已退出\n")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        if sio.connected:
            sio.disconnect()


if __name__ == '__main__':
    main()


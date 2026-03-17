import discord
import datetime
import os
import asyncio
import logging
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# --- 環境変数から設定を取得 ---

# 1. Discord Botのトークン
BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

# 2. アイコンを変更したいDiscordサーバーのID
_server_id_str = os.environ.get('DISCORD_SERVER_ID')
SERVER_ID = int(_server_id_str) if _server_id_str and _server_id_str.isdigit() else None

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def load_file_data(filepath: str) -> bytes | None:
    """ファイルを読み込んでバイナリデータを返す。存在しない場合はNoneを返す。"""
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            data = f.read()
        logger.info(f"情報: ファイル '{os.path.basename(filepath)}' を読み込みました。")
        return data
    else:
        logger.warning(f"警告: ファイル '{os.path.basename(filepath)}' が見つかりません。スキップします。")
        return None

async def update_server_assets(client: discord.Client, server_id: int, icon_data: bytes | None, banner_data: bytes | None):
    """指定されたサーバーのアイコンとバナーを更新する"""
    try:
        # Botにログイン
        await client.login(BOT_TOKEN)

        # サーバーオブジェクトを取得
        guild = await client.fetch_guild(server_id)

        # サーバーアイコンとバナーを一度に変更
        await guild.edit(icon=icon_data, banner=banner_data)
        
        # 成功メッセージの生成
        changed_items = []
        if icon_data:
            changed_items.append("アイコン")
        if banner_data:
            changed_items.append("バナー")
            
        logger.info(f"成功: サーバー '{guild.name}' の {' と '.join(changed_items)} を変更しました。")

    except discord.LoginFailure:
        logger.error("エラー: Botトークンが不正です。'BOT_TOKEN'の設定を確認してください。")
    except discord.NotFound:
        logger.error(f"エラー: サーバーID '{server_id}' が見つかりません。Botがそのサーバーに参加しているか確認してください。")
    except discord.Forbidden:
        logger.error("エラー: アイコンやバナーを変更する権限がありません。Botのロール設定で「サーバー管理」権限が有効か確認してください。")
    except discord.HTTPException as e:
        if 'SERVER_BANNER' in str(e):
             logger.error("エラー: サーバーバナーの変更に失敗しました。サーバーがブーストレベル2以上であるか確認してください。")
        else:
             logger.error(f"HTTPエラーが発生しました: {e}")
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")
    finally:
        # 処理の成否にかかわらず、必ず接続を閉じる
        if not client.is_closed():
            await client.close()

async def main():
    """サーバーアイコンとバナーを変更するメイン処理"""
    logger.info("処理開始")

    # 必須の設定項目が存在するかチェック
    if not BOT_TOKEN:
        logger.error("エラー: 環境変数 'DISCORD_BOT_TOKEN' が設定されていません。.envファイルを確認してください。")
        logger.info("処理終了")
        return
    if not SERVER_ID:
        logger.error("エラー: 環境変数 'DISCORD_SERVER_ID' が正しく設定されていません。数値で指定されているか確認してください。")
        logger.info("処理終了")
        return
    
    # 今日の日付からファイル名を生成
    today_str = datetime.datetime.now().strftime('%Y%m%d')
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # アイコンとバナーのファイル名とパスを定義
    icon_filename = f"{today_str}.gif"
    banner_filename = f"banner_{today_str}.gif"
    icon_filepath = os.path.join(script_dir, icon_filename)
    banner_filepath = os.path.join(script_dir, banner_filename)
    
    # ファイルの読み込み
    icon_data = load_file_data(icon_filepath)
    banner_data = load_file_data(banner_filepath)

    # 変更するファイルが一つもない場合は処理を終了
    if icon_data is None and banner_data is None:
        logger.error("エラー: 変更対象のアイコンファイルもバナーファイルも見つかりませんでした。処理を終了します。")
        logger.info("処理終了")
        return

    # インテントを設定（サーバー情報を取得するために必要）
    intents = discord.Intents.default()
    intents.guilds = True
    client = discord.Client(intents=intents)

    # アセットの更新
    await update_server_assets(client, SERVER_ID, icon_data, banner_data)
    
    logger.info("処理終了")

if __name__ == "__main__":
    # 非同期関数を実行
    asyncio.run(main())
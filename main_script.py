import os
import base64
import json
import requests
import pytz
import logging  # Thêm thư viện logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# --- Cấu hình logging ---
# Tạo một logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Đặt mức log thấp nhất để bắt tất cả các loại log

# Tạo handler để ghi log ra file
file_handler = logging.FileHandler('script_activity.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)  # Ghi tất cả log vào file

# Tạo handler để in log ra console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Chỉ hiển thị log từ mức INFO trở lên trên console

# Định dạng cho log
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Thêm handler vào logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
# --- Kết thúc cấu hình logging ---


load_dotenv()

EMAIL_SENDER = 'smartpit@smartpit.nttcom.ne.jp'
EMAIL_SUBJECT = '【Ｓｍａｒｔ　Ｐｉｔ】収納情報のお知らせ'

CASPIO_API_URL_BASE = os.getenv('CASPIO_API_URL')
CASPIO_API_CLIENT_ID = os.getenv('CASPIO_CLIENT_ID')
CASPIO_API_CLIENT_SECRET = os.getenv('CASPIO_CLIENT_SECRET')
CASPIO_TABLE_NAME = 'SmartPitDaThanhToan'

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CLIENT_SECRET_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def setup_credentials_from_env():
    creds_json_str = os.getenv('GMAIL_CREDENTIALS_JSON')
    token_json_str = os.getenv('GMAIL_TOKEN_JSON')

    if creds_json_str and not os.path.exists(CLIENT_SECRET_FILE):
        print(f"Creating {CLIENT_SECRET_FILE} from environment variable.")
        with open(CLIENT_SECRET_FILE, 'w') as f:
            f.write(creds_json_str)

    if token_json_str and not os.path.exists(TOKEN_FILE):
        print(f"Creating {TOKEN_FILE} from environment variable.")
        with open(TOKEN_FILE, 'w') as f:
            f.write(token_json_str)

def get_gmail_service():
    """Xác thực với Google và trả về một đối tượng service để tương tác với Gmail."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            logger.warning("Token không hợp lệ hoặc đã hết hạn. Vui lòng chạy script này trên máy local trước để tạo token.json mới.")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build('gmail', 'v1', credentials=creds)

def search_emails(service, user_id='me'):
    """
    Tìm kiếm email theo khoảng thời gian động.
    Từ 00:00:00 của ngày hôm nay đến thời điểm hiện tại (múi giờ +07).
    """
    try:
        target_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now_in_target_tz = datetime.now(target_tz)
        
        start_of_day = now_in_target_tz.replace(hour=0, minute=0, second=0, microsecond=0)
        
        after_timestamp = int(start_of_day.timestamp())
        before_timestamp = int(now_in_target_tz.timestamp())

        query = f"from:({EMAIL_SENDER}) subject:('{EMAIL_SUBJECT}') after:{after_timestamp} before:{before_timestamp}"
        logger.info(f"Đang tìm kiếm với truy vấn động: {query}")
        
        response = service.users().messages().list(userId=user_id, q=query).execute()
        all_messages = []
        
        while 'messages' in response:
            all_messages.extend(response['messages'])
            if 'nextPageToken' in response:
                page_token = response['nextPageToken']
                response = service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
            else:
                break
                
        return all_messages
    except Exception as e:
        logger.error(f"Lỗi khi tìm kiếm email: {e}", exc_info=True)
        return []

def get_email_details(service, msg_id, user_id='me'):
    """Lấy nội dung và ngày tháng của email."""
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id, format='full').execute()
        payload = message.get('payload', {})
        headers = payload.get('headers', [])

        date_str = None
        for header in headers:
            if header.get('name') == 'Date':
                date_str = header.get('value')
                break
        
        content = ""
        data = None
        if 'parts' in payload:
            for part in payload.get('parts', []):
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data')
                    break
        elif 'body' in payload:
            data = payload.get('body', {}).get('data')

        if data:
            content = base64.urlsafe_b64decode(data.encode('ASCII')).decode('iso-2022-jp', errors='ignore')
        
        return content, date_str
    except Exception as e:
        logger.error(f"Không thể lấy chi tiết email ID {msg_id}: {e}", exc_info=True)
        return None, None

def parse_email_content(content):
    """Trích xuất dữ liệu bằng cách phân tích từng dòng."""
    if not content: return None
    card_number, bill_id, detail_link = None, None, None
    lines = content.split('\n')
    for line in lines:
        cleaned_line = line.strip()
        if cleaned_line.startswith("1."): card_number = cleaned_line[2:].strip()
        elif cleaned_line.startswith("2."): bill_id = cleaned_line[2:].strip()
        elif cleaned_line.startswith("3."): detail_link = cleaned_line[2:].strip()
    if not all([card_number, bill_id, detail_link]): return None
    return {'MaThanhToan': card_number.replace('-', ''), 'IDthanhtoan': bill_id, 'Linkcheck': detail_link}

def get_caspio_token():
    """Lấy Access Token từ API của Caspio."""
    if not CASPIO_API_CLIENT_ID or not CASPIO_API_CLIENT_SECRET:
        logger.critical("Lỗi: CASPIO_CLIENT_ID hoặc CASPIO_CLIENT_SECRET chưa được thiết lập trong biến môi trường.")
        return None
    try:
        response = requests.post(f'{CASPIO_API_URL_BASE}/oauth/token', data={'grant_type': 'client_credentials', 'client_id': CASPIO_API_CLIENT_ID, 'client_secret': CASPIO_API_CLIENT_SECRET})
        response.raise_for_status()
        return response.json()['access_token']
    except requests.exceptions.RequestException as e:
        logger.critical(f"Lỗi nghiêm trọng khi lấy Caspio token: {e}", exc_info=True)
        return None

def push_to_caspio(data, token):
    """Đẩy một bản ghi dữ liệu lên bảng Caspio."""
    if not data: return False
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    url = f'{CASPIO_API_URL_BASE}/rest/v2/tables/{CASPIO_TABLE_NAME}/records'
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 201:
            logger.info(f"✅ Thành công: Đã thêm bản ghi IDSMS {data['IDSMS']} vào Caspio.")
            return True
        else:
            logger.error(f"❌ Thất bại: Không thể thêm bản ghi {data['IDSMS']}. Status: {response.status_code}, Lỗi: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi khi đẩy dữ liệu lên Caspio: {e}", exc_info=True)
        return False

def main():
    """Hàm chính điều phối toàn bộ quy trình."""
    setup_credentials_from_env()
    logger.info("🚀 Bắt đầu quá trình đồng bộ hóa Email sang Caspio...")
    gmail_service = get_gmail_service()
    caspio_token = get_caspio_token()
    if not caspio_token:
        logger.critical("Dừng chương trình do không lấy được token Caspio.")
        return
    messages = search_emails(gmail_service)
    if not messages:
        logger.info("Không tìm thấy email nào mới trong khoảng thời gian vừa qua.")
        return
    logger.info(f"🔎 Tìm thấy {len(messages)} email phù hợp. Bắt đầu xử lý...")

    messages.reverse()
    logger.info("ℹ️ Sẽ xử lý email theo thứ tự từ cũ nhất đến mới nhất.")

    success_count, fail_count = 0, 0
    target_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    for msg_info in messages:
        msg_id = msg_info['id']
        email_content, email_date_str = get_email_details(gmail_service, msg_id)
        if email_content:
            parsed_data = parse_email_content(email_content)
            if parsed_data:
                formatted_date = ""
                if email_date_str:
                    try:
                        dt_object_with_tz = parsedate_to_datetime(email_date_str)
                        dt_object_in_target_tz = dt_object_with_tz.astimezone(target_tz)
                        formatted_date = dt_object_in_target_tz.strftime('%m/%d/%Y %H:%M:%S')
                    except Exception as e:
                        logger.error(f"Lỗi khi xử lý ngày tháng cho email {msg_id}: {e}", exc_info=True)
                final_record = {'IDSMS': msg_id, **parsed_data, 'ThoiGianThanhToan': formatted_date}
                if push_to_caspio(final_record, caspio_token): success_count += 1
                else: fail_count += 1
            else:
                logger.warning(f"⚠️ Bỏ qua email ID {msg_id} do không trích xuất được đủ thông tin.")
                fail_count += 1
    
    summary = (
        f"\n--- 🏁 Quá trình hoàn tất! ---\n"
        f"Tổng số email đã xử lý: {len(messages)}\n"
        f"Thành công: {success_count}\n"
        f"Thất bại: {fail_count}"
    )
    logger.info(summary)

if __name__ == '__main__':
    main()

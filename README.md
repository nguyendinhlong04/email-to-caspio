# Đồng bộ Email Smart Pit sang Caspio

Dự án này chứa một kịch bản Python được thiết kế để tự động đọc email thông báo thanh toán từ **Smart Pit**, trích xuất dữ liệu và đẩy chúng vào một bảng trên nền tảng **Caspio**. Kịch bản được tối ưu hóa để chạy tự động theo lịch trình bằng **GitHub Actions**.

---

## 🚀 Tính năng chính

-   **Tự động hóa:** Tự động tìm kiếm và xử lý các email mới theo lịch trình định sẵn (mặc định là 10 phút/lần).
-   **Xử lý theo thời gian thực:** Script tự động xác định khoảng thời gian cần quét, từ `00:00:00` của ngày hiện tại đến thời điểm chạy script (theo múi giờ GMT+7).
-   **Mạnh mẽ & Linh hoạt:** Trích xuất dữ liệu dựa trên cấu trúc dòng của email, giúp giảm thiểu lỗi khi nội dung email thay đổi.
-   **Bảo mật:** Sử dụng GitHub Secrets để quản lý an toàn các thông tin nhạy cảm như API keys, tokens, và credentials.
-   **Không giới hạn:** Tự động lật trang (pagination) để lấy toàn bộ email phù hợp, không bị giới hạn ở con số 100 của API.

---

## 📁 Cấu trúc thư mục

Để dự án hoạt động trên GitHub Actions, bạn cần đảm bảo cấu trúc thư mục như sau:


ten-repo-cua-ban/
├── .github/
│   └── workflows/
│       └── sync_emails.yml   # Tệp điều khiển lịch chạy của GitHub Actions
├── main_script.py            # Kịch bản Python xử lý logic chính
└── requirements.txt          # Danh sách các thư viện Python cần thiết


---

## 🛠️ Hướng dẫn cài đặt và cấu hình

### 1. Điều kiện tiên quyết

-   Tài khoản [Python](https://www.python.org/downloads/) (phiên bản 3.8 trở lên).
-   Tài khoản [Google Cloud](https://console.cloud.google.com/) để tạo thông tin xác thực cho Gmail API.
-   Tài khoản [Caspio](https://www.caspio.com/) với quyền truy cập API.
-   Tài khoản [GitHub](https://github.com/).

### 2. Cài đặt trên máy cá nhân (Local Setup)

Bước này **bắt buộc** phải thực hiện lần đầu tiên để tạo ra tệp `token.json` cho phép Google xác thực.

1.  **Clone repository:**
    ```bash
    git clone [https://github.com/ten-cua-ban/ten-repo-cua-ban.git](https://github.com/ten-cua-ban/ten-repo-cua-ban.git)
    cd ten-repo-cua-ban
    ```

2.  **Tạo tệp `credentials.json`:**
    -   Làm theo hướng dẫn của Google để tạo **OAuth 2.0 Client ID** cho **Desktop app**.
    -   Tải tệp JSON về và đổi tên thành `credentials.json`, sau đó đặt nó vào thư mục gốc của dự án.

3.  **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Chạy script lần đầu tiên:**
    -   Mở tệp `main_script.py` và tạm thời điền `CASPIO_CLIENT_ID` và `CASPIO_CLIENT_SECRET` của bạn vào.
    -   Chạy script từ terminal:
        ```bash
        python main_script.py
        ```
    -   Một cửa sổ trình duyệt sẽ mở ra, yêu cầu bạn đăng nhập và cấp quyền truy cập Gmail. Hãy làm theo các bước.
    -   Sau khi hoàn tất, một tệp `token.json` sẽ được tạo ra trong thư mục dự án.

### 3. Cấu hình trên GitHub Actions

1.  **Vào repository trên GitHub:**
    -   Đi tới tab **Settings** > **Secrets and variables** > **Actions**.

2.  **Tạo các "Secrets":**
    -   Nhấn **New repository secret** và tạo 4 secret sau đây. Đây là bước quan trọng để bảo mật thông tin của bạn.
        -   `CASPIO_CLIENT_ID`: Dán giá trị Client ID của Caspio.
        -   `CASPIO_CLIENT_SECRET`: Dán giá trị Client Secret của Caspio.
        -   `GMAIL_CREDENTIALS_JSON`: Mở tệp `credentials.json` bạn vừa tạo, sao chép **toàn bộ nội dung** và dán vào đây.
        -   `GMAIL_TOKEN_JSON`: Mở tệp `token.json` bạn vừa tạo, sao chép **toàn bộ nội dung** và dán vào đây.

3.  **Dọn dẹp và Đẩy code:**
    -   Xóa các giá trị `CASPIO_CLIENT_ID` và `CASPIO_CLIENT_SECRET` mà bạn đã điền tạm trong tệp `main_script.py`.
    -   Đẩy toàn bộ các tệp (`main_script.py`, `requirements.txt`, và thư mục `.github`) lên repository của bạn.

---

## ▶️ Cách hoạt động

Sau khi thiết lập xong, GitHub Actions sẽ tự động kích hoạt kịch bản Python theo lịch trình đã định trong tệp `sync_emails.yml` (mặc định là mỗi 10 phút).

Bạn có thể theo dõi các lần chạy trong tab **Actions** của repository. Nếu cần chạy script ngay lập tức, bạn có thể vào workflow "Sync Gmail to Caspio" và chọn **Run workflow**.

>Contact at: `dinhlongvt2004@gmail.com`
# Remote Desktop Control

Để đảm bảo an toàn trong quá trình truy cập từ xa thông qua **Remote Desktop** trên HĐH Windows, Chúng ta có thể thiết lập một số cấu hình an toàn như:

- Đặt mật khẩu đủ [MẠNH](https://www.lastpass.com/features/password-generator)
- Không sử dụng Port mặc định: [3389](https://docs.microsoft.com/en-us/windows-server/remote/remote-desktop-services/clients/change-listening-port)
- Xác thực 2 bước với **[Duo Security](https://duo.com/docs/rdp)**
- Cấu hình tường lửa cho phép hoặc chặn kết nối tùy thời điểm và ngữ cảnh.
- v.v..

Trong phần này tôi giới thiệu hai phương pháp **"không mới và ít tốn kém"** hơn cả đó là lợi dụng chính **Windows Firewall** để kiểm soát kết nối RDP, cách thứ 2 là kết nối 2 máy vào cùng một mạng VPN. Chỉ khi nào chúng ta có nhu cầu kết nối RDP đến máy tính ở xa thì chúng ta mới **BẬT** cho phép kết nối. Khi không có nhu cầu sử dụng nữa, chúng ta sẽ **TẮT**. Việc này vừa đảm bảo an toàn cũng như tránh được các đối tượng bên ngoài **[Rà quét cổng](https://en.wikipedia.org/wiki/Port_scanner)** hay tấn công **[Brute-force](https://en.wikipedia.org/wiki/Brute-force_attack)** mật khẩu.

Giải quyết vấn đề này, ta đi xây dựng một con **Bot Telegram** sẽ chạy ở phía máy tính ở xa đó. Khi đó máy tính tại nhà hoặc cty muốn RDP vào chỉ cần gửi lệnh cho Bot thông qua ứng dụng Telegram để **BẬT** hoặc **TẮT**.


## 1. Các tính năng của Bot
- `/rdp on|off|check`: Quản lý RDP
- `/vpn on|off|check`: Quản lý VPN
- Tương tác qua ứng dụng nhắn tin Telegram

## 2. Các trường hợp sử dụng

- Remote Desktop đến Windows Cloud/VPS Server,.v.v..
- Work from Home - Truy cập vào máy tính trên cty

## 3. Cách thức hoạt động

Giao diện trợ giúp của Bot:

![help](assets/help.png)

### 3.1. Sử dụng Windows Firewall để kiểm soát
Để có thể sử dụng thì phải đảm bảo Windows Firewall luôn được bật phía máy tính ở xa:

![error_firewall](assets/error_firewall.png)

Cho phép kết nối RDP:

![on](assets/on.png)


Từ chối kết nối RDP:

![off](assets/off.png)


**Giải thích:** Theo mặc định Windows Firewall có một bộ gồm 3 rules để kiểm soát RDP. Khi chúng ta ra lệnh cho Bot Bật hoặc Tắt chính là chúng ta đang Enable hoặc Disalbe các rules này.

![rules](assets/rules.png)


### 3.2. Sử dụng VPN để RDP

Kết nối máy đích đến VPN Server

![vpn_on](assets/vpn_on.png)

Kiểm tra trạng thái VPN

![vpn_check](assets/vpn_check.png)

Ngắt kết nối VPN

![vpn_off](assets/vpn_off.png)

Tại máy client ta cũng kết nối đến VPN Server, khi đó cả 2 máy sẽ cùng chung mạng VPN và đã có thể RDP.


## 4. Hướng dẫn build từ mã nguồn

Bot được viết bằng Python nên có thể gây khó khăn khi phân phối ứng dụng. Khắc phục vấn đề này tôi sử dụng gói **[PyInstaller](https://www.pyinstaller.org/)** để đóng gói ứng dụng thành một tệp ***.EXE** duy nhất để có thể chạy được trên các máy tính Windows khác nhau mà không cần phải cài Python. 

- [rdcbot.py](rdcbot.py): Bot viết bằng Python
- [rdcutil.py](rdcutil.py): Builder. Tự động đóng gói, build Bot thành EXE.

Các bước build Bot từ mã nguồn:

1. Cài đặt [Python](https://www.python.org/downloads/windows/)
2. Download hoặc dùng Git clone mã nguồn Bot:
    ```bash
    $ git clone https://github.com/hailehong95/RDC-Bot.git
    ```
3. Cài đặt Virtualenv và tạo môi trường ảo:
    ```bash
   $ cd rdcbot
   $ pip3 install virtualenv
   $ virtualenv -p python3 venv
   $ venv\Scripts\activate
   $ (venv) pip install -r requirements.txt
    ```
4. Build bot

   - Tùy chọn (Không bắt buộc): Download [UPX Packer](https://upx.github.io/) và đặt vào thư mục `upx32` hoặc `upx64` tương ứng bên trong thư mục `packer`. Xem [README.md](packer/README.md)

    ```bash
    $ (venv) python rdcutil.py
    ```
6. Kết quả

- Kiểm tra trong thư mục `releases` xuất hiện tệp `rdcbot.exe`


## 5. Cài đặt và cấu hình

Tham khảo: [Cài đặt và cấu hình RDCBot](docs)

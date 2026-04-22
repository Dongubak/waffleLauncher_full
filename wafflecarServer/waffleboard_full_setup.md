# WaffleBoard Omega2 전체 설정 가이드

## 개요

| 항목 | 내용 |
|------|------|
| 보드 | Onion Omega2 + WaffleBoard V3.0 |
| OS | OpenWRT (BusyBox ash) |
| Python | 2.7 |
| 서버 IP | 192.168.3.1 |
| 서버 포트 | 19126 (제어), 8080 (카메라) |
| SSH 기본 비밀번호 | onioneer |
| WiFi AP 기본 비밀번호 | 12345678 |

---

## 사전 준비 (PC)

- PC WiFi를 **Omega2 AP**에 연결 (`Omega-XXXX`, 비밀번호: `12345678`)
- SSH 클라이언트 준비 (Windows 기본 ssh 명령어 사용 가능)

---

## STEP 1 — SSH 접속

```bash
ssh -o HostKeyAlgorithms=+ssh-rsa root@192.168.3.1
# 비밀번호: onioneer
```

> 접속 오류 시 known_hosts 초기화 후 재시도:
> ```bash
> ssh-keygen -R 192.168.3.1
> ```

---

## STEP 2 — 인터넷 WiFi 연결 (패키지 다운로드용)

```bash
uci set wireless.sta.disabled='0'; uci commit wireless; wifi
wifisetup
# → 1번 선택 → SSID 입력 → 비밀번호 입력
```

연결 확인:
```bash
ping 8.8.8.8
# 응답 오면 성공, Ctrl+C로 중단
```

---

## STEP 3 — 펌웨어 업그레이드

```bash
oupgrade
# 재부팅 후 약 2~3분 대기 후 다시 SSH 접속
```

> **oupgrade 실패 시 (서버 오류 또는 네트워크 문제)**
>
> 아래 오류가 발생하면 현재 펌웨어 버전을 확인합니다:
> ```
> Failed to parse message data
> WARNING: Variable 'image' does not exist or is not an array/object
> ERROR: Downloading firmware has failed!
> ```
>
> ```bash
> # 현재 버전 확인
> ubus call system board | grep firmware
> ```
>
> 버전이 `0.3.x` 이상이면 oupgrade를 건너뛰고 다음 단계로 진행해도 됩니다.

---

## STEP 4 — 패키지 설치

```bash
opkg update && opkg install python-light && opkg install pyOnionGpio && opkg install pyOnionI2C && opkg install mjpg-streamer
```

> **kmod-rtl8812au (외장 USB WiFi 동글 드라이버)**
>
> 이 패키지는 외장 USB WiFi 동글을 사용할 경우에만 필요합니다.
> 외장 동글 없이 Omega2 내장 WiFi를 사용한다면 설치하지 않아도 됩니다.
>
> 설치가 필요한 경우 아래 오류가 발생할 수 있습니다:
> - `Unknown package 'kmod-rtl8812au'` — 저장소에서 삭제됨 (펌웨어 버전에 따라 다름)
> - `Cannot satisfy kernel dependencies` — oupgrade 없이 진행 시 커널 버전 불일치
>
> 두 경우 모두 STEP 3 oupgrade를 먼저 완료해야 해결됩니다.

---

## STEP 5 — 파일 전송 (PC → Omega2)

PC의 `waffleLauncher_full` 디렉토리에서 실행:

```bash
# 서버 메인 파일
scp -o HostKeyAlgorithms=+ssh-rsa wafflecarServer/wafflecarServer.py root@192.168.3.1:/root/

# 자동 시작 서비스 파일
scp -o HostKeyAlgorithms=+ssh-rsa wafflecarServer/runWaffleServer root@192.168.3.1:/etc/init.d/

# 카메라 설정 파일 (반드시 전송 — 기본값 덮어쓰기)
scp -o HostKeyAlgorithms=+ssh-rsa wafflecarServer/mjpg-streamer root@192.168.3.1:/etc/config/mjpg-streamer

# 서보 기본값 파일
scp -o HostKeyAlgorithms=+ssh-rsa wafflecarServer/servoDefaultValue.txt root@192.168.3.1:/root/
```

> **주의**: 새 보드의 기본 mjpg-streamer 설정은 아래와 같이 되어 있어 카메라가 동작하지 않습니다.
> - `option enabled '0'` — 비활성화 상태
> - `option username / password` — 인증 설정으로 OpenCV 접속 차단
>
> 위 SCP 명령으로 `wafflecarServer/mjpg-streamer` 파일을 덮어써야 정상 동작합니다.

---

## STEP 6 — 서비스 등록

```bash
# 서버 서비스
chmod +x /etc/init.d/runWaffleServer
/etc/init.d/runWaffleServer enable

# 카메라 서비스
/etc/init.d/mjpg-streamer enable
/etc/init.d/mjpg-streamer start

# 등록 확인
ls -lh /etc/rc.d | grep runWaffleServer
ls -lh /etc/rc.d | grep mjpg

A787
```

---

## STEP 7 — Ethernet DHCP 설정 (선택 — LAN 직접 연결 시)

> WiFi AP만 사용한다면 이 단계는 건너뜁니다.

Ethernet 포트에서도 PC가 자동으로 `192.168.3.x` IP를 받으려면
`eth0`를 `wlan` 브리지에 추가해야 합니다.

```bash
vi /etc/config/network
```

`wlan` 인터페이스에 `option ifname 'eth0'` 추가:

```
config interface 'wlan'
        option type 'bridge'
        option ifname 'eth0'        ← 이 줄 추가
        option proto 'static'
        option ipaddr '192.168.3.1'
        option netmask '255.255.255.0'
        option ip6assign '60'
```

`wan` 인터페이스 삭제 또는 주석처리:

```
# config interface 'wan'
#         option ifname 'eth0'
#         option proto 'dhcp'
```

네트워크 재시작:
```bash
/etc/init.d/network restart
```

---

## STEP 8 — WiFi 클라이언트 비활성화

```bash
uci set wireless.sta.disabled='1'; uci commit wireless; wifi
```

---

## STEP 9 — 재부팅 및 동작 확인
j
```bash
reboot
```

재부팅 후 SSH 재접속:
```bash
ssh -o HostKeyAlgorithms=+ssh-rsa root@192.168.3.1

# 서버 프로세스 확인
ps | grep wafflecarServer

# 카메라 프로세스 확인
ps | grep mjpg
```

---

## 이후 서버 파일 수정 시 배포

```bash
# PC에서: 수정된 파일 전송
scp -o HostKeyAlgorithms=+ssh-rsa wafflecarServer/wafflecarServer.py root@192.168.3.1:/root/

# Omega2에서: 프로세스 재시작
pkill -f wafflecarServer.py
python /root/wafflecarServer.py &
# 또는 재부팅: reboot
```

---

## 문제 해결

### SSH 접속 오류 — host key changed
```bash
ssh-keygen -R 192.168.3.1
```

### 서버 포트 이미 사용 중 (Address in use)
```bash
pkill -f wafflecarServer.py
python /root/wafflecarServer.py
```

### 카메라 연결 실패 (tcp://192.168.3.1:8080)

**원인 1 — mjpg-streamer가 실행되지 않은 경우**
```bash
ps | grep mjpg          # grep mjpg만 나오면 미실행 상태
/etc/init.d/mjpg-streamer start
```

**원인 2 — 새 보드의 기본 설정 문제 (`enabled '0'` 또는 인증 설정)**

증상: start 명령 실행해도 프로세스가 뜨지 않음

```bash
# 방법 1: PC에서 설정 파일 덮어쓰기 (권장)
scp -o HostKeyAlgorithms=+ssh-rsa wafflecarServer/mjpg-streamer root@192.168.3.1:/etc/config/mjpg-streamer
/etc/init.d/mjpg-streamer restart
```

```bash
# 방법 2: Omega2에서 직접 수정
uci set mjpg-streamer.core.enabled='1'
uci delete mjpg-streamer.core.username
uci delete mjpg-streamer.core.password
uci commit mjpg-streamer
/etc/init.d/mjpg-streamer restart
```

정상 동작 확인:
```bash
ps | grep mjpg              # mjpg_streamer 프로세스 확인
netstat -tlnp | grep 8080   # 포트 리스닝 확인
```

### Ethernet 연결 시 IP 못 받음 (169.254.x.x)
- STEP 7의 Ethernet DHCP 설정을 진행하거나
- PC 이더넷 어댑터를 수동 설정: IP `192.168.3.100`, 서브넷 `255.255.255.0`

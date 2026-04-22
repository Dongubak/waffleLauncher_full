# WaffleBoard (Onion Omega2) 초기 설정

> 상세 내용: `waffleLauncher_full/wafflecarServer/waffleboard_full_setup.md` 참고

## 보드 정보

| 항목 | 내용 |
|---|---|
| 보드 | Onion Omega2 + WaffleBoard V3.0 |
| OS | OpenWRT (BusyBox ash) |
| Python | 2.7 |
| 서버 IP | `192.168.3.1` |
| 서버 포트 | `19126` (제어), `8080` (카메라) |
| SSH 비밀번호 | `onioneer` |
| WiFi AP 비밀번호 | `12345678` |
| WiFi SSID | `Omega-XXXX` |

---

## 빠른 설정 순서

```
1. PC WiFi → Omega AP 연결 (Omega-XXXX / 12345678)
2. SSH 접속: ssh -o HostKeyAlgorithms=+ssh-rsa root@192.168.3.1
3. 인터넷 WiFi 연결: wifisetup
4. 패키지 설치: opkg update && opkg install python-light pyOnionGpio pyOnionI2C mjpg-streamer
5. 파일 전송 (PC → Omega2):
   scp wafflecarServer/wafflecarServer.py root@192.168.3.1:/root/
   scp wafflecarServer/runWaffleServer root@192.168.3.1:/etc/init.d/
   scp wafflecarServer/mjpg-streamer root@192.168.3.1:/etc/config/mjpg-streamer
   scp wafflecarServer/servoDefaultValue.txt root@192.168.3.1:/root/
6. 서비스 등록 및 활성화
7. 재부팅
```

---

## 서버 파일 업데이트

```bash
# PC에서 수정된 파일 전송
scp -o HostKeyAlgorithms=+ssh-rsa wafflecarServer/wafflecarServer.py root@192.168.3.1:/root/

# Omega2에서 프로세스 재시작
pkill -f wafflecarServer.py
python /root/wafflecarServer.py &
```

---

## 주요 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| SSH host key 오류 | known_hosts 불일치 | `ssh-keygen -R 192.168.3.1` |
| 포트 19126 이미 사용 중 | 이전 프로세스 미종료 | `pkill -f wafflecarServer.py` |
| 카메라 연결 실패 | mjpg-streamer 미실행 또는 기본 설정 문제 | SCP로 설정 파일 덮어쓰기 후 restart |
| Ethernet IP 못 받음 | eth0가 wlan 브리지에 미포함 | /etc/config/network에 eth0 추가 |

---

## 관련 문서

- [[202604211000-wafflelauncher-setup]] — PC 환경 설정
- [[202604211001-wafflelauncher-full-analysis]] — 전체 시스템 분석

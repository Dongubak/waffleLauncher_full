# MOC — waffleLauncher

> WaffleCar 자율주행 시스템 전체 문서 지도

## 시작하기

1. [[202604211000-wafflelauncher-setup]] — PC 환경 설정 및 패키지 설치
2. [[202604211003-waffleboard-setup]] — Omega2 보드 초기 설정

## 시스템 이해

- [[202604211001-wafflelauncher-full-analysis]] — 전체 아키텍처 분석

## AI 모델 학습

- [[202604211002-yolov8-training]] — YOLOv8 모델 학습 및 연동
- [[202604211031-yolov8-model-guide]] — 모델 학습·교체 가이드

## 배포

- [[202604221000-distribution-strategy]] — 경량 소스 배포 전략 (requirements.txt, Mac 지원)

---

## 빠른 참조

### 필수 패키지 설치
```bash
pip install -r requirements.txt
```

### 실행
```bash
cd "C:\Users\x0011\OneDrive\바탕 화면\waffleLauncher_full"
python main.py
```

### 제어 명령 포맷
```
L<motion><angle>E      # L 모드: L0150E (정지), L1150E (전진)
H,<R>,<L>,<angle>,E   # H 모드: H,F1,F1,150,E (저속 전진)
Q                      # 연결 종료
```

### 차량 연결 정보
- IP: `192.168.3.1`
- 제어 포트: `19126` (TCP)
- 카메라: `http://192.168.3.1:8080/?action=stream`

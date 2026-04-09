# Zero-Waste VDI Farm

> VDI 자동 프로비저닝 및 유휴 자원 자동 회수 시스템

[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://python.org)
[![Proxmox](https://img.shields.io/badge/Proxmox-VE-orange)](https://proxmox.com)
[![Discord](https://img.shields.io/badge/Discord-Bot-7289DA)](https://discord.com)
[![Claude](https://img.shields.io/badge/Claude-Anthropic-blueviolet)](https://anthropic.com)

---

## 📌 프로젝트 배경

대규모 게임 개발/QA 환경에서는 다양한 OS와 사양의 테스트 환경이 수시로 필요합니다.
기존 방식은 IT 담당자가 수동으로 VM을 생성하고, 사용 후 방치된 **좀비 VM**이 온프레미스
리소스를 고갈시키는 문제가 반복됩니다.

Zero-Waste VDI Farm은 이 두 가지 문제를 해결합니다.

- **자연어 요청** → LLM 파싱 → VM 자동 프로비저닝 (IT 담당자 개입 없음)
- **유휴 VM 자동 감지** → Discord 알림 → 스냅샷 후 자동 회수

---

## 🏗️ 아키텍처

```
Discord 자연어 요청
→ LLM Function Calling (Claude API)
→ Proxmox API VM 자동 생성 (템플릿 클론)
→ cloud-init 초기 설정 (계정, 네트워크)
→ 부팅 시 telegraf-setup.sh 실행
   → Proxmox API로 VM 이름 자동 감지
   → Telegraf 설정 후 메트릭 수집 시작
→ InfluxDB 저장
→ Grafana 대시보드 시각화
→ 유휴 감지 데몬 (CPU + 메모리 + 네트워크 복합 지표)
   → Discord 알림 → 스냅샷 백업 → 자동 회수
```

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| 가상화 | Proxmox VE 8.x |
| 모니터링 | Telegraf → InfluxDB 2.x → Grafana 11.x |
| 자동화 | Python 3.10, Proxmox API |
| LLM | Claude (Anthropic) Function Calling |
| 인터페이스 | Discord Bot |
| 인프라 | On-Premise (베어메탈 또는 VMware) |

---

## ✨ 기존 오픈소스 VDI 솔루션과의 차별점

| 기능 | OpenNebula / IsardVDI | Zero-Waste VDI Farm |
|------|----------------------|---------------------|
| VM 요청 방식 | 웹 UI 수동 선택 | Discord 자연어 요청 |
| 프로비저닝 시간 | 약 30분 (수동) | 약 3분 (자동) |
| 유휴 감지 | 단순 시간 기반 | CPU + 메모리 + 네트워크 복합 지표 |
| 회수 방식 | 단순 삭제 | 스냅샷 백업 후 회수 |
| 게임 QA 특화 | ❌ | ✅ |

---

## 📊 성과 지표

| 지표 | 개선 전 | 개선 후 |
|------|---------|---------|
| VM 프로비저닝 시간 | 약 30분 (수동) | 약 3분 (자동) |
| 유휴 VM 회수율 | 0% (수동 추적) | 100% (자동 감지) |
| IT 담당자 반복 업무 | VM 요청마다 수동 처리 | 완전 자동화 |

---

## 📁 프로젝트 구조

```
zero-waste-vdi/
├── bot.py                          # Discord 봇 진입점
├── config.py                       # 환경변수 로딩
├── proxmox.py                      # Proxmox API 관련
├── llm.py                          # Anthropic LLM 관련
├── daemon.py                       # 유휴 VM 감지 + 자동 회수
├── requirements.txt
├── .env.example
└── monitoring/
    ├── telegraf.conf.example
    └── grafana/
        └── dashboard.json          # Grafana 대시보드 (임포트 가능)
```

---

## 🚀 시작하기

### 사전 요구사항

- Proxmox VE 8.x 설치된 서버
- Python 3.10+
- Discord 봇 토큰
- Anthropic API 키
- InfluxDB 2.x + Grafana

### 설치

```bash
git clone https://github.com/mondayy1/zero-waste-vdi.git
cd zero-waste-vdi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env 파일에 값 입력
```

### 실행

```bash
# Discord 봇
python3 bot.py

# 유휴 VM 감지 데몬
python3 daemon.py
```

### Discord 사용법

```
!vdi QA 테스트용 VM 2코어 4GB로 하나 만들어줘
```

---

## 📸 스크린샷

### Discord VM 요청 및 생성
![Discord](docs/discord.png)

### Grafana 모니터링 대시보드
![Grafana](docs/grafana.png)

### 유휴 VM 자동 회수
![Daemon](docs/daemon.png)

---

## ⚠️ 한계 및 개선 예정

- **IP 자동 조회**: 현재 VMware 환경 제약으로 미구현. 베어메탈 환경에서는 QEMU Guest Agent로 즉시 IP 조회 가능
- **GPU 패스스루**: 베어메탈 Proxmox 환경에서 PCIe 패스스루로 구현 예정
- **유예 기간**: 실운영 환경에서는 알림 후 N시간 대기 후 회수 적용 예정
- **인증**: 실운영 환경에서는 SSH 키 기반 인증 및 일회용 비밀번호 발급으로 대체 예정

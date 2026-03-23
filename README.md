## 프로젝트 개요
### 주요 기능
환자의 병원 이용 여정에 따라 다음과 같은 편의 기능을 제공합니다.

- 진료 예약 및 관리: 24시간 언제 어디서나 진료 예약, 변경, 취소가 가능하며 대리 예약 기능도 지원합니다.
- 병원 이용 안내: 위치 안내, 주차 등록, 외래 접수, 대기 순번 확인 등을 실시간으로 조회할 수 있습니다.
- 결제 및 서류 발급: 창구 대기 없이 카카오페이 등으로 진료비를 결제하고, 제증명서 발급 및 처방전 확인이 가능합니다.
- 입·퇴원 관리: 입원 예약, 병실 배정 확인, 입원 생활 안내 및 퇴원 수속까지 톡 내에서 처리합니다.
- AI 상담챗: 증상을 입력하면 적절한 진료과나 의료진을 추천받거나, 서비스 이용 중 궁금한 점을 AI에게 즉시 물어볼 수 있습니다.



## 프로젝트 구조
이 프로젝트는 모노레포(mono-repo) 구조로 backend/ frontend/ 폴더에 각각의 서비스가 존재합니다.
- backend: fastAPI
- frontend: React + Next.js -> App Router 표준(src/app/layout.tsx + 경로별 page.tsx) 기본 SEO 최적화 구조

```
smart-house-ai/
├── .github/
│   └── workflows/
│       ├── backend-ci.yml      # 백엔드 CI/CD 파이프라인
│       └── frontend-ci.yml     # 프론트엔드 CI/CD 파이프라인
├── backend/                    # FastAPI 백엔드 서비스
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── main.py
│   │   └── ...
│   ├── Dockerfile              # 백엔드 도커 이미지 빌드
│   └── requirements.txt        # 백엔드 의존성
├── frontend/                   # React 프론트엔드 서비스
│   ├── src/
│   ├── public/
│   ├── Dockerfile              # 프론트엔드 도커 이미지 빌드
│   └── package.json            # 프론트엔드 의존성
└── helm/                       # Helm 차트
    ├── backend/
    └── frontend/
```

## 기술 스택
- **백엔드**: Python 3.12, FastAPI
- **프론트엔드**: React, TypeScript, Next.js (App Router), Tailwind CSS
- **CI/CD**: GitHub Actions
- **배포**: ArgoCD, Kubernetes


### 로컬 환경 설정 및 실행
```bash
# 프론트엔드 실행
cd frontend
npm install
npm run dev # 기본적으로 http://localhost:3000 에서 실행됨
# 참고: frontend/.env.local 파일에 API_BASE_URL 환경변수가 설정되어야 합니다.
```

### 도커 빌드 및 실행
```bash
# 백엔드 도커 이미지 빌드
docker build -t backend ./backend

# 프론트엔드 도커 이미지 빌드
docker build -t frontend ./frontend

# 도커 컴포즈로 실행
docker-compose up
```

## CI/CD 파이프라인
### GitHub Actions
- `backend-ci.yml`: 백엔드 코드 변경 시 자동 빌드 및 GHCR에 이미지 푸시
- `frontend-ci.yml`: 프론트엔드 코드 변경 시 자동 빌드 및 GHCR에 이미지 푸시

### ArgoCD
- `helm/backend/`: 백엔드 배포용 Helm 차트
- `helm/frontend/`: 프론트엔드 배포용 Helm 차트
- ArgoCD는 GHCR에 푸시된 이미지를 자동으로 감지하여 Kubernetes 클러스터에 배포합니다.

## API 엔드포인트
- `GET /healthz`: 헬스 체크
- `GET /api/hello`: 샘플 API

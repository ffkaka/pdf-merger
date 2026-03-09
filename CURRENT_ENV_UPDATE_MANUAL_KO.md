# 현재 환경 업데이트 전용 매뉴얼 (KO)

이 문서는 `pdf-merger` 저장소를 이미 사용 중인 환경에서, **항상 최신 상태로 안전하게 업데이트**하는 절차만 따로 정리한 운영 매뉴얼이다.  
기준 날짜: **2026-03-09**

---

## 1. 언제 업데이트할까

- 작업 시작 전 1회
- 다른 기기에서 변경 후 현재 기기로 돌아왔을 때
- `AGENTS.md`, `scripts/`, `README.md`, 매뉴얼 파일이 변경되었을 때

---

## 2. 표준 업데이트 절차 (권장)

이미 운영 중인 환경에서는 아래 순서를 권장한다.

```bash
cd ~/pdf-merger
git pull --ff-only
./scripts/update_env.sh
```

참고:
- `update_env.sh` 안에도 `git pull --ff-only`가 포함되어 있다.
- 운영 중 환경에서는 수동 `git pull --ff-only`를 먼저 실행하면 변경사항 확인이 더 명확하다.

`update_env.sh` 자동 수행 항목:
- 워킹트리 clean 상태 확인
- `git pull --ff-only`
- `./scripts/setup_env.sh` 실행

---

## 3. 수동 절차 (스크립트 사용이 어려울 때)

```bash
cd ~/pdf-merger
git status --short
git pull --ff-only
./scripts/setup_env.sh
```

검증:

```bash
./pmerge japan --keywords-file tmp/pdfs/keywords_sample.txt
```

---

## 4. 업데이트가 막힐 때

### 4-1. `working tree is not clean`

원인: 로컬 변경이 남아 있음.

해결:
```bash
git status --short
git add .
git commit -m "chore: save local changes"
git pull --ff-only
./scripts/update_env.sh
```

### 4-2. `fatal: not a git repository`

원인: 프로젝트 루트 밖에서 실행.

해결:
```bash
cd ~/pdf-merger
./scripts/update_env.sh
```

### 4-3. 의존성 설치 실패

해결:
```bash
python3 --version
python3 -m pip --version
./scripts/setup_env.sh
```

---

## 5. 여러 환경(PC/노트북) 동기화 규칙

1. 작업한 환경에서 자주 반영:
```bash
git add .
git commit -m "chore: sync environment updates"
git push
```

2. 다른 환경에서 즉시 동기화:
```bash
git pull --ff-only
./scripts/update_env.sh
```

---

## 6. 산출물/중간파일 원칙

- 최종 산출물: `output/pdf/`
- 중간 산출물: `tmp/pdfs/`
- 위 경로는 Git 추적 대상에서 제외되므로, 환경 동기화 시 코드/설정 중심으로 유지된다.

---

## 7. 빠른 체크리스트

- 현재 경로가 `~/pdf-merger` 인가?
- `git status --short`가 비어 있는가?
- `./scripts/update_env.sh`가 성공했는가?
- `./pmerge ...` 테스트가 정상인가?

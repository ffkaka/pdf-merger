# AGENTS.md

## 목적
이 저장소의 에이전트는 여러 PDF 파일이 있는 폴더에서 여러 키워드(예: `AAA-BBB1`, `AAA-BBB2` ... `FFF-FFF9`)를 받아, 키워드에 해당하는 PDF를 찾고 **하나의 PDF로 통합 병합**한다.

## 필수 스킬
- pdf (read/create/review PDF with layout fidelity, rendering checks 포함)

## 스킬 자동 설치
아래 스킬이 설치되어 있지 않다면, 다음 명령으로 설치한다.
- codex skill install pdf

## 기본 작업 규칙
- 새 PDF 생성은 `output/pdf/` 아래에 저장한다.
- 중간 산출물은 `tmp/pdfs/` 아래에 둔다.
- 레이아웃 확인이 필요한 경우 페이지 렌더링 후 육안 검수한다.
- 키워드 검색은 PDF 텍스트를 추출해 수행한다.
- 키워드가 여러 개여도 병합 결과는 하나의 PDF로 생성한다.
- 병합 결과 파일명은 기본 `merged_keywords.pdf`를 사용하되, 작업 목적에 맞게 명시적으로 지정할 수 있다.
- 병합 결과 PDF는 **최대 2MB 이하**가 되도록 생성한다.
- 2MB를 초과하면 파일명에 인덱스(`_01`, `_02`, ...)를 붙여 여러 PDF로 분할 생성한다.

## 간단 입력 형식
- 기본 입력은 다음 2개를 받는다.
  - 병합 대상 폴더 경로 (`input_dir`)
  - 키워드 파일 경로 (`keywords_file`, 한 줄에 키워드 1개)
- 권장 실행 예:
  - `PMERGE_KEYWORDS_FILE=/home/<USER>/pdf-merger/keywords.txt pmerge japan`
- 필요 시 파일명 기준 검색:
  - `PMERGE_KEYWORDS_FILE=/home/<USER>/pdf-merger/keywords.txt PMERGE_EXTRA_ARGS="--match-mode filename" pmerge japan`

## 표준 워크플로우
1. 입력 폴더 스캔: PDF 목록을 수집한다.
2. 키워드 검색: 각 PDF에서 텍스트를 추출해 키워드 포함 여부를 판정한다.
3. 병합 대상 선정: 키워드 전체 기준으로 매칭된 PDF를 하나의 목록으로 합친다(중복 제거).
4. 병합: 대상 PDF를 지정된 순서로 하나의 PDF로 합친다.
5. 저장: `output/pdf/` 아래에 단일 결과물을 저장한다.
6. 용량 검증: 결과 PDF가 2MB 이하인지 확인한다.
7. 초과 시 분할: 인덱스 파일로 분할 저장한다. 예: `merged_keywords_01.pdf`, `merged_keywords_02.pdf`
8. 검수: 병합된 PDF를 열어 누락/깨짐 여부를 확인한다.

## 산출물 규칙
- 최종 결과물 파일명은 작업 목적을 반영한다. 예: `환경설정.pdf`, `merged_user_guide.pdf`
- 생성/병합 결과는 항상 `output/pdf/`에 둔다.

# pdf-merger

키워드로 PDF를 필터링해서 병합하는 프로젝트입니다.

## 빠른 사용

프로젝트 루트에서 실행:

```bash
PMERGE_KEYWORDS_FILE=tmp/pdfs/keywords.txt ./pmerge japan
```

파일명 기준 필터링(본문 미검색):

```bash
PMERGE_KEYWORDS_FILE=tmp/pdfs/keywords.txt PMERGE_EXTRA_ARGS="--match-mode filename" ./pmerge japan
```

기본 동작:
- 매칭 결과를 `output/pdf/merged_keywords.pdf`로 생성
- 2MB 초과 시 `merged_keywords_01.pdf`, `merged_keywords_02.pdf`처럼 분할 생성
- 리포트: `tmp/pdfs/keyword_merge_report.json`

## Codex 프롬프트 팁 (`@상대경로`)

Codex 프롬프트에서 `@경로`를 붙이면 대상 파일/폴더 문맥이 명확해집니다.

예:
- `@AGENTS.md`
- `@japan`
- `@tmp/pdfs/keywords.txt`

### 예시 프롬프트

```text
@AGENTS.md 규칙대로 병합해.
입력 폴더는 @japan, 키워드 파일은 @tmp/pdfs/keywords.txt 를 사용해.
PMERGE_KEYWORDS_FILE 방식으로 실행하고 결과는 @output/pdf 에 저장해.
머지 후 결과 PDF와 @tmp/pdfs/keyword_merge_report.json 존재 여부, 파일 크기, 첫 페이지 렌더링까지 검증해.
```

```text
@AGENTS.md 기준으로 이 프로젝트 사용방법 알려줘.
특히 @japan 폴더와 @tmp/pdfs/keywords.txt 를 사용해서
필터링, 병합, 2MB 초과 시 분할 생성, 검증까지 한 번에 하는 절차를
명령어 중심으로 설명해줘.
```

## 문서

- 상세 매뉴얼: `WINDOWS_WSL_CODEX_MANUAL_KO.md`
- PDF 매뉴얼: `WINDOWS_WSL_CODEX_MANUAL_KO.pdf`

# BuildLog 진행 기록

## 지금 상태

- **완료:** Phase 3 (회원가입·로그인·로그아웃·닉네임 변경) — 커밋 `b1d5c35`
- **다음:** Phase 4 (공부 기록·할 일·오류 기록의 데이터 구조)

## 다음 할 일

1. Phase 3 화면을 브라우저에서 직접 확인 (가입 실패 시 이메일·닉네임 유지, 비밀번호만 지움 / 로그인 실패 시 이메일 유지 / 로그아웃 후 로그인 화면 이동)
2. Phase 4 진행 — [plan.md](plan.md) Phase 4
3. 확인 대기: 이메일 대소문자 구분을 그대로 유지할지 (같은 메일함으로 계정 여러 개 생성 가능)
4. 확인 대기: 맨 위 폴더의 `.vscode/`를 Git에 포함할지
5. 확인 대기: 테스트 도구 경고에 따라 `httpx` → `httpx2` 교체 여부
6. 확인 대기: Figma 대시보드에만 있는 개수 요약 카드·완료율·"공부 기록 쓰기" 버튼·날짜를 spec에 넣을지. 홈에서 할 일 체크는 spec 2.4 "이 화면은 기록을 새로 저장하지 않습니다"와 충돌
7. 사이드바 화면을 실제 로그인 상태로 브라우저에서 확인, 360px 휴대폰 너비 확인 (Phase 12)
8. 학습 자료함 화면을 브라우저에서 직접 확인 (등록·AI 요약 표시·원본 보기·영상 재생·삭제, 360px)
9. **OpenAI 키 교체:** 2026-10-27 키가 채팅에 그대로 붙여 넣어졌음. OpenAI에서 새 키를 발급해 `.env`의 `OPENAI_API_KEY`만 바꾸고 기존 키는 폐기
10. 확인 대기: 배포할 때 업로드 파일 저장 위치(서버 디스크 유지 또는 Supabase Storage), 사용자별 용량·업로드 횟수 제한 여부 → [plan.md](plan.md) 10.6

## 완료 기록

### 2026-10-27

- 학습 자료함 + AI 요약 (확장 기능, 커밋 안 함): PRD 12장·spec 14장·plan 10장 추가. `materials` 테이블(Alembic `c3e8f1a7b2d4`, Supabase 적용, RLS 켬), 업로드·목록·원본 보기·삭제 API, `/materials` 화면, 업로드 시 OpenAI `gpt-5.4-nano`로 이미지·영상(6장면) 요약 저장. 서버 테스트 94개 통과, 실제 Supabase·OpenAI로 전체 흐름 확인 → [plan.md](plan.md) 10.5
- 학습 자료함 목록에 미리보기 추가: 이미지 썸네일(누르면 원본), 영상은 목록에서 재생. 원본 파일을 그대로 불러오므로 썸네일 전용 파일은 없음. lint·build 통과, 브라우저 확인은 아직

- Supabase 저장 준비 (Phase 13 일부 앞당김, 커밋 안 함): psycopg 3.3.6 설치, Supabase `postgresql://` 주소를 psycopg·SSL로 연결, 서버·Alembic이 SQLite 주소를 거부하도록 변경. 서버 테스트 67개 통과 (테스트는 임시 SQLite 사용)
- Supabase 연결: 다른 프로젝트(게시판)와 같은 Supabase DB를 사용. 그쪽 이력 표(`alembic_version`)와 겹치지 않도록 BuildLog 이력은 `buildlog_alembic_version`에 기록. `alembic upgrade head`로 `users` 생성, 서버 연결 확인
- 남은 일: 화면에서 회원가입 → Supabase 저장 확인, Data API 차단(RLS, plan.md Phase 13의 3번)
- 문서 차이: PRD·plan은 아직 "개발·테스트는 SQLite" 기준. setup.md만 고침
- Figma 대시보드 적용 (Phase 12 일부 앞당김, 커밋 안 함): 로그인한 화면을 왼쪽 사이드바로 변경, 내 기록 홈 인사말에 로그인 사용자 닉네임 표시, 기록 카드 3개는 빈 안내. 프론트 lint·build 통과. 가짜 `/api/auth/me` 응답으로 1440px·600px 화면 확인 → [plan.md](plan.md) Phase 12 "앞당겨 진행한 부분"

### 2026-10-26

- Phase 0: 문서 충돌(확인-A~H) 정리, 버전·로그인 방식·환경 변수 결정 → [setup.md](setup.md)
- Phase 1: FastAPI·React 뼈대, `/api/health`, Vite 프록시 연결
- Git 초기화, 첫 커밋 `a12367a`
- Phase 2: 사용자 테이블, Alembic 첫 이력, 테스트 24개 통과 → 커밋 `1a46e6d`, GitHub push
- 작업 규칙 [AGENTS.md](../AGENTS.md) 작성, 진행 기록(이 파일) 시작
- Phase 3: 회원 API 5개, 로그인 쿠키(JWT), 회원가입·로그인·홈(빈 틀)·계정 설정 화면, 서버 테스트 67개 통과 → 커밋 `b1d5c35`
- 로그인 쿠키를 항상 HTTPS 전용(Secure)으로 고정. 개발 중 Safari 로그인 불가(Chrome·Edge·Firefox는 가능) → 커밋 `b1d5c35`
- 오류 수정: 백엔드가 꺼져 있을 때 화면이 "요청을 처리하지 못했습니다"만 보여주던 문제 → 화면 서버의 502~504 응답을 "서버에 연결할 수 없습니다"로 안내 (`frontend/src/api/client.js`) → 커밋 "백엔드 연결 실패 시 안내 문구 수정"

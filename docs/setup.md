# BuildLog 개발 환경 설정

> 이 문서는 Phase 0(2026-10-26)에서 정한 개발 환경 기준입니다.
> 실행 명령은 아직 동작하지 않습니다. 각 Phase에서 해당 부분을 만든 뒤 실제로 실행해 확인하고, 이 문서를 고칩니다.

## 1. 내 컴퓨터에 필요한 도구

Phase 0에서 확인한 현재 설치 상태입니다.

| 도구 | 확인된 버전 | 비고 |
| --- | --- | --- |
| Python | 3.13.14 | 명령은 `python` 또는 `py`를 사용합니다. `python3`은 Microsoft Store 연결용이라 사용하지 않습니다. |
| pip | 26.1.2 | |
| SQLite | 3.50.4 | Python에 포함되어 있어 따로 설치하지 않습니다. |
| Node.js | 24.22.1 | Vite 8, React Router 8의 요구 조건(Node 22.22 이상)을 충족합니다. |
| npm | 11.19.1 | |
| Git | 설치됨 | Git 초기화와 커밋은 요청이 있을 때만 합니다. |

## 2. 사용할 패키지와 버전

2026-10-26에 PyPI와 npm에서 확인한 최신 안정 버전입니다. 실제 설치는 해당 Phase에서 하며, 그때 이 버전으로 고정해 `backend/requirements.txt`와 `frontend/package.json`에 기록합니다.

### 서버 (Python)

| 용도 | 패키지 | 버전 | 설치 Phase |
| --- | --- | --- | --- |
| 서버 | fastapi | 0.162.0 | 1 |
| 서버 실행 | uvicorn | 0.54.0 | 1 |
| 설정(.env) 읽기 | pydantic-settings | 2.16.1 | 1 |
| 입력값 검사 | pydantic | 2.14.1 | 1 (fastapi와 함께) |
| 데이터베이스 다루기 | sqlalchemy | 2.1.6 | 2 |
| 데이터베이스 변경 이력 | alembic | 1.20.1 | 2 |
| 비밀번호 안전하게 저장 | pwdlib[argon2] | 0.3.1 | 2 |
| 로그인 유지(JWT) | pyjwt | 2.15.1 | 3 |
| 이메일 형식 검사 | email-validator | 2.3.0 | 3 |
| 서버 자동 테스트 | pytest | 9.1.1 | 2 |
| 테스트용 요청 보내기 | httpx | 0.28.1 | 2 |
| Supabase(PostgreSQL) 접속 | psycopg | 3.3.6 | 13 |

- Phase 1에서 fastapi, uvicorn, pydantic-settings를 설치했습니다. 함께 설치된 주요 의존 패키지는 pydantic 2.14.1, starlette 1.10.0입니다.
- Phase 2에서 sqlalchemy, alembic, pwdlib[argon2], pytest, httpx를 설치했습니다. 테스트 도구(pytest, httpx)도 같은 `requirements.txt`에 기록합니다.
- 비밀번호 저장은 FastAPI 공식 튜토리얼이 권장하는 pwdlib + Argon2를 사용합니다. passlib는 PyPI 최신 버전이 1.7.4에 머물러 있어 사용하지 않습니다.

### 화면 (JavaScript)

| 용도 | 패키지 | 버전 | 설치 Phase |
| --- | --- | --- | --- |
| 화면 | react, react-dom | 19.3.1 | 1 |
| 개발 도구 | vite | 8.3.5 | 1 |
| Vite의 React 지원 | @vitejs/plugin-react | 6.1.2 | 1 |
| 화면 이동 | react-router | 8.5.0 | 3 |

- 화면 코드는 **JavaScript**로 작성합니다 (TypeScript 사용 안 함).
- Vite React 템플릿(create-vite 9.3.1)이 함께 설치한 기본 개발 도구는 템플릿 기본값을 따릅니다: `oxlint` 1.89.0(코드 검사, `npm run lint`), `@types/react`·`@types/react-dom` 19.3.0(편집기 자동 완성용). 정확한 설치 버전은 `frontend/package-lock.json`에 고정됩니다.
- react-router 8은 최신 버전이라 인터넷의 강의나 글(대부분 v6·v7 기준)과 코드가 다를 수 있습니다. 공식 문서를 기준으로 합니다.

## 3. 주소와 파일 위치

| 항목 | 값 |
| --- | --- |
| 서버 주소 | `http://127.0.0.1:8000` |
| 서버 요청 목록 화면 (자동 생성) | `http://127.0.0.1:8000/docs` |
| 화면 주소 | `http://localhost:5173` (Vite 기본값) |
| 화면 → 서버 요청 연결 | Vite 개발용 프록시로 `/api`로 시작하는 요청을 서버로 전달 |
| Python 가상환경 | `backend/.venv` |
| 설정 파일 | 프로젝트 맨 위 폴더의 `.env` (Git 제외) |
| 설정 항목 예시 파일 | 프로젝트 맨 위 폴더의 `.env.example` (Git 기록, 비밀값 없음) |
| 개발용 데이터베이스 | `database/buildlog.sqlite3` (Git 제외) |
| 테스트용 데이터베이스 | 테스트를 실행할 때마다 새로 만들고 끝나면 지움. 개발용 데이터베이스는 건드리지 않음 |

- 화면과 서버를 프록시로 연결하면 브라우저 입장에서 같은 주소가 되어, 주소가 달라서 생기는 접속 차단(CORS) 설정과 쿠키 문제를 줄일 수 있습니다.

## 4. 환경 변수

`.env`에 넣는 항목입니다. `.env.example`에는 이름과 설명만 적고 실제 비밀값은 넣지 않습니다.

| 이름 | 뜻 | 개발용 값 예시 |
| --- | --- | --- |
| `DATABASE_URL` | 데이터베이스 접속 주소 | `sqlite:///database/buildlog.sqlite3` (프로젝트 맨 위 폴더 기준. 서버 코드가 실행 위치와 상관없이 같은 파일을 찾도록 처리) |
| `SECRET_KEY` | 로그인 증명(JWT)에 서명하는 비밀값 | 각자 컴퓨터에서 새로 만든 값 (아래 명령 참고) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 로그인 유지 시간(분) | `10080` (7일) |

비밀값 만드는 명령 (Phase 1에서 사용):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

- Phase 13에서 Supabase로 바꿀 때는 `DATABASE_URL`만 Supabase 접속 주소로 바꿉니다. Supabase 접속 정보는 `.env`에만 넣고 채팅, 코드, 문서에 적지 않습니다.

## 5. 로그인 유지 방식

| 항목 | 결정 |
| --- | --- |
| 방식 | 로그인에 성공하면 서버가 로그인 증명(JWT)을 만들어 쿠키로 보냄 |
| 쿠키 설정 | 화면의 JavaScript가 읽을 수 없게(httpOnly), 다른 사이트에서 보낸 요청에는 실리지 않게(SameSite=Lax). 실제 서비스(HTTPS)에서는 암호화된 연결에서만 전송(Secure) |
| 유지 기간 | 7일 |
| 로그아웃 | 서버가 쿠키를 지우고, 화면은 로그인 화면으로 이동 |

- **알아둘 점:** 이 방식은 서버에 로그인 기록을 저장하지 않습니다. 그래서 로그아웃하면 이 브라우저의 쿠키는 지워지지만, 쿠키가 다른 곳에 복사되었다면 그 사본은 유지 기간(7일)이 끝날 때까지 유효합니다.

## 6. 실행 명령

모두 Windows PowerShell 기준이며, 프로젝트 맨 위 폴더(`buildlog`)에서 시작합니다.

### 처음 한 번만: 설치

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend
npm install
cd ..
```

`.env`가 없다면 `.env.example`을 복사해 `.env`를 만들고 `SECRET_KEY`를 채웁니다 (4장 명령 참고).

### 서버 (Phase 1부터 동작 확인됨)

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- 가상환경을 켜지 않고 `.venv` 안의 Python으로 바로 실행하는 방식이라 PowerShell 실행 정책 문제를 피할 수 있습니다.
- 확인: 브라우저에서 `http://127.0.0.1:8000/api/health` → `{"status":"ok", ...}`, `http://127.0.0.1:8000/docs` → 요청 목록 화면

### 화면 (Phase 1부터 동작 확인됨)

서버를 켠 상태에서 다른 PowerShell 창을 열어 실행합니다.

```powershell
cd frontend
npm run dev
```

- 확인: 브라우저에서 `http://localhost:5173` → "BuildLog 서버가 동작 중입니다."
- 서버가 꺼져 있으면 "서버에 연결할 수 없습니다" 안내가 보입니다.

### 데이터베이스 변경 이력 적용 (Phase 2부터 동작 확인됨)

처음 설치했을 때와, 다른 사람이 만든 새 변경 이력을 받았을 때 실행합니다. `database/buildlog.sqlite3`가 없으면 새로 만듭니다.

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

테이블 구조를 바꾼 뒤 새 변경 이력 파일을 만들 때:

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "변경 내용"
```

- 만들어진 파일은 반드시 열어서 확인합니다. SQLite에서는 대소문자 무시 인덱스 같은 "식 기반 인덱스"를 자동으로 찾지 못해 직접 추가해야 합니다.

### 서버 자동 테스트 (Phase 2부터 동작 확인됨)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

- 테스트는 매번 임시 데이터베이스를 새로 만들어 실행하므로 개발용 데이터베이스를 바꾸지 않습니다.

### VS Code에서 Python 경고가 보일 때

VS Code가 `backend\.venv`가 아닌 다른 Python을 쓰고 있으면 "패키지가 설치되어 있지 않습니다" 같은 표시가 나옵니다. `Ctrl+Shift+P` → "Python: Select Interpreter" → `backend\.venv\Scripts\python.exe`를 선택합니다.

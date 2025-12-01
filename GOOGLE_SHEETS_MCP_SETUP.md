# Google Sheets MCP 설정 가이드

Google Sheets MCP 서버가 성공적으로 설치되었습니다! 이제 Google API 인증을 설정해야 합니다.

## 설치된 구성

- **MCP 서버**: `google-sheets-mcp` (npm 패키지)
- **설정 파일**: `.claude/mcp.json`
- **실행 방법**: npx를 통한 자동 실행

## Google API 인증 설정 단계

### 1단계: Google Cloud Console 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속합니다
2. 새 프로젝트를 생성하거나 기존 프로젝트를 선택합니다
3. 왼쪽 메뉴에서 "API 및 서비스" > "라이브러리"로 이동합니다

### 2단계: 필요한 API 활성화

다음 API들을 검색하여 활성화합니다:
- **Google Sheets API**
- **Google Drive API**

### 3단계: OAuth 2.0 인증 정보 생성

1. "API 및 서비스" > "사용자 인증 정보"로 이동합니다
2. "+ 사용자 인증 정보 만들기" 클릭
3. "OAuth 클라이언트 ID" 선택
4. 애플리케이션 유형: "데스크톱 앱" 선택
5. 이름 입력 후 "만들기" 클릭
6. 생성된 클라이언트 ID의 JSON 파일을 다운로드합니다

### 4단계: 인증 정보 파일 설정

다운로드한 JSON 파일을 다음 위치에 저장합니다:

```bash
mkdir -p ~/.config/google-sheets-mcp
mv ~/Downloads/client_secret_*.json ~/.config/google-sheets-mcp/credentials.json
```

### 5단계: 환경 변수 설정 (선택사항)

`.claude/mcp.json` 파일에 인증 정보 경로를 추가할 수 있습니다:

```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "npx",
      "args": [
        "-y",
        "google-sheets-mcp"
      ],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/home/user/.config/google-sheets-mcp/credentials.json"
      }
    }
  }
}
```

### 6단계: 첫 실행 및 인증

MCP 서버를 처음 실행하면 브라우저가 열리며 Google 계정 로그인을 요청합니다:

1. Google 계정으로 로그인
2. 권한 요청 승인
3. 인증 토큰이 자동으로 저장됩니다

## MCP 서버 기능

이 MCP 서버를 통해 다음 작업을 수행할 수 있습니다:

- 스프레드시트 목록 조회
- 새 스프레드시트 생성
- 스프레드시트 복사
- 셀 데이터 읽기 및 쓰기
- 셀 데이터 편집 및 채우기

## 문제 해결

### 인증 오류가 발생하는 경우

1. 인증 정보 파일 경로가 올바른지 확인
2. Google Sheets API와 Drive API가 활성화되었는지 확인
3. OAuth 동의 화면이 올바르게 설정되었는지 확인

### MCP 서버가 시작되지 않는 경우

```bash
# npx 캐시 정리
npx clear-npx-cache

# 수동으로 패키지 설치 테스트
npx -y google-sheets-mcp
```

## 추가 리소스

- [Google Sheets MCP GitHub](https://github.com/xing5/mcp-google-sheets)
- [Google Sheets API 문서](https://developers.google.com/sheets/api)
- [Claude Code MCP 문서](https://docs.claude.com/ko/docs/claude-code/mcp)

## 참고사항

- 첫 실행 시 인증 과정이 필요합니다
- 토큰은 자동으로 갱신됩니다
- 여러 Google 계정을 사용하는 경우 각각 별도로 인증이 필요합니다

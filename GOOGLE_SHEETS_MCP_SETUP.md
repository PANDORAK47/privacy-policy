# Google Sheets MCP 설정 가이드

Google Sheets MCP 서버(`mcp-gsheets`)가 성공적으로 설치되었습니다!

## 📦 설치된 구성

- **MCP 서버**: `mcp-gsheets@latest` (by freema)
- **npm 패키지**: https://www.npmjs.com/package/mcp-gsheets
- **GitHub**: https://github.com/freema/mcp-gsheets
- **설정 파일**: `.claude/mcp.json`
- **실행 방법**: npx를 통한 자동 실행

## ✅ 연결 테스트 완료

MCP 서버가 정상적으로 실행되는 것을 확인했습니다. 이제 Google API 인증만 설정하면 사용할 수 있습니다.

## 🔐 Google API 인증 설정 (필수)

### 1단계: Google Cloud Console 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속합니다
2. 새 프로젝트를 생성하거나 기존 프로젝트를 선택합니다
3. **APIs & Services** > **Library**로 이동합니다
4. **Google Sheets API**를 검색하여 **활성화**합니다

### 2단계: 서비스 계정 생성

1. **APIs & Services** > **Credentials**로 이동합니다
2. **+ Create Credentials** 클릭
3. **Service Account** 선택
4. 서비스 계정 정보 입력:
   - 이름: `claude-sheets-mcp` (또는 원하는 이름)
   - ID는 자동 생성됩니다
5. **Create and Continue** 클릭
6. Role은 건너뛰거나 "Editor"를 선택할 수 있습니다 (선택사항)
7. **Done** 클릭

### 3단계: 서비스 계정 키 생성 및 다운로드

1. 생성된 서비스 계정을 클릭합니다
2. **Keys** 탭으로 이동
3. **Add Key** > **Create new key** 클릭
4. 키 유형: **JSON** 선택
5. **Create** 클릭하면 JSON 파일이 자동으로 다운로드됩니다

### 4단계: 인증 정보 파일 저장

다운로드한 JSON 파일을 다음 위치에 저장합니다:

```bash
# 디렉토리 생성
mkdir -p ~/.config/google-sheets-mcp

# 다운로드한 파일을 지정된 위치로 이동
# (다운로드 폴더 경로는 사용자 환경에 따라 다를 수 있습니다)
mv ~/Downloads/your-project-*.json ~/.config/google-sheets-mcp/service-account-key.json

# 파일 권한 설정 (보안)
chmod 600 ~/.config/google-sheets-mcp/service-account-key.json
```

### 5단계: Google Sheets 공유 설정

MCP 서버가 스프레드시트에 접근하려면 반드시 공유 설정을 해야 합니다:

1. 사용하려는 Google Sheet를 엽니다
2. 우측 상단의 **공유** 버튼을 클릭합니다
3. JSON 파일에서 `client_email` 값을 찾습니다 (예: `claude-sheets-mcp@your-project.iam.gserviceaccount.com`)
4. 해당 이메일 주소를 공유 대상에 추가합니다
5. 권한: **편집자** 선택
6. **전송** 클릭

## 🎯 현재 MCP 설정

`.claude/mcp.json` 파일이 다음과 같이 구성되어 있습니다:

```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "npx",
      "args": ["-y", "mcp-gsheets@latest"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/home/user/.config/google-sheets-mcp/service-account-key.json"
      }
    }
  }
}
```

## 🔧 대체 인증 방식

### 옵션 A: 환경 변수로 개인 키 직접 설정

JSON 파일 대신 환경 변수로 직접 설정할 수 있습니다:

```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "npx",
      "args": ["-y", "mcp-gsheets@latest"],
      "env": {
        "GOOGLE_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
        "GOOGLE_CLIENT_EMAIL": "your-service-account@your-project.iam.gserviceaccount.com"
      }
    }
  }
}
```

**주의**: 개인 키의 줄바꿈을 `\\n`으로 표현해야 합니다.

### 옵션 B: JSON 문자열 인증

```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "npx",
      "args": ["-y", "mcp-gsheets@latest"],
      "env": {
        "GOOGLE_SERVICE_ACCOUNT_KEY": "{\"type\":\"service_account\",\"project_id\":\"...\",\"private_key\":\"...\"}"
      }
    }
  }
}
```

## 🚀 MCP 서버 기능

이 MCP 서버를 통해 다음 작업을 수행할 수 있습니다:

### 기본 작업
- ✅ 스프레드시트 생성, 읽기, 업데이트, 삭제
- ✅ 시트 추가, 삭제, 이름 변경
- ✅ 셀 데이터 읽기 및 쓰기
- ✅ 범위 기반 데이터 조작

### 고급 작업
- ✅ 배치 작업으로 여러 작업을 한 번에 실행
- ✅ 셀 서식 지정 (색상, 폰트, 정렬 등)
- ✅ 차트 생성 및 관리
- ✅ 조건부 서식 설정
- ✅ 데이터 검증 규칙 설정

## 🧪 테스트 방법

MCP 서버가 제대로 설정되었는지 확인하려면:

1. 위의 모든 단계를 완료했는지 확인
2. Claude Code를 재시작하거나 MCP 설정을 다시 로드
3. Claude에게 다음과 같이 요청해보세요:
   - "Google Sheets에서 새 스프레드시트 만들어줘"
   - "스프레드시트 ID [YOUR_SHEET_ID]의 데이터를 읽어줘"

## ❗ 문제 해결

### 인증 오류가 발생하는 경우

```bash
# 1. JSON 파일 경로 확인
ls -la ~/.config/google-sheets-mcp/service-account-key.json

# 2. JSON 파일 내용 검증
cat ~/.config/google-sheets-mcp/service-account-key.json | jq '.'

# 3. 파일 권한 확인
ls -l ~/.config/google-sheets-mcp/service-account-key.json
```

**확인 사항**:
- JSON 파일이 올바른 위치에 있는지 확인
- Google Sheets API가 활성화되었는지 확인
- 스프레드시트를 서비스 계정 이메일과 공유했는지 확인

### "Permission denied" 오류

스프레드시트를 서비스 계정 이메일(`client_email`)과 공유했는지 확인하세요.

### MCP 서버가 시작되지 않는 경우

```bash
# npx 캐시 정리
npx clear-npx-cache

# 최신 버전으로 수동 테스트
npx -y mcp-gsheets@latest
```

## 📚 추가 리소스

- **공식 GitHub**: https://github.com/freema/mcp-gsheets
- **npm 패키지**: https://www.npmjs.com/package/mcp-gsheets
- **Google Sheets API 문서**: https://developers.google.com/sheets/api
- **Claude Code MCP 문서**: https://docs.claude.com/ko/docs/claude-code/mcp

## 💡 팁

1. **여러 스프레드시트 사용**: 각 스프레드시트를 서비스 계정과 공유하기만 하면 됩니다
2. **보안**: JSON 키 파일은 절대 Git 저장소에 커밋하지 마세요
3. **자동 업데이트**: `mcp-gsheets@latest`를 사용하면 항상 최신 버전이 사용됩니다
4. **성능**: 배치 작업을 사용하면 API 호출 횟수를 줄일 수 있습니다

## 🎉 설치 완료!

모든 설정이 완료되면 Claude Code에서 자연어로 Google Sheets를 조작할 수 있습니다!

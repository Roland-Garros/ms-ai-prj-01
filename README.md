## 프로젝트 명
- **Azure OpenAI 기반 RFP 분석 및 수행 인력 추천 Assistant**

## 서비스 링크
- https://ktds-user03-web-app-09.azurewebsites.net/

## 개요 및 목적
- Azure OpenAI를 활용하여 **RFP 분석 및 사내 업무 담당자 추천**을 수행하는 AI Assistant
  - <b>약 60 페이지(약 4만 글자)</b>가 넘는 Word 포맷 **RFP 문서 핵심 내용 분석**
  - <b>약 1900명(약 30만 글자)</b>의 KT DS 전 직원 **사무분장 정보 기반 담당자 검색**
  - 분석된 RFP 핵심 내용 기반 프로젝트 수행 가능한 KT DS 업무 담당자 추천

## 활용 기술 및 Azure 서비스
- **Azure**
  - **Azure OpenAI** : LLM, Vector Store, Data File, Assistant 배포 및 관리
  - **Azure App Service** : Python Streamlit 기반 웹 페이지 배포
- **활용 기술**
  - **Python 3.12** : Assistant 채팅 화면 및 대화 흐름 개발
    - openai, streamlit
  - **Visual Studio Code** : Python 소스코드 개발 및 수정
  - **GitHub** : Python 소스코드 형상 관리

## 아키텍쳐
- **Azure OpenAI RAG Assistant 중심 구조**
![image](https://github.com/user-attachments/assets/71123193-dfce-46df-ac3e-a8459dfe4e46)

## 기대효과
- 효율적인 RFP(제안요청서) 핵심 내용 분석 **(N시간 -> 15초)**
- RFP 관련 사내 프로젝트 수행 인력 탐색 허비 시간 감소 **(N시간 -> 13초)**
- 동일 업무 담당자가 다른 팀에 흩어져 있어도 One-Time 검색으로 해결 가능
- RFP 내용 변경 시 빠른 대응 가능

## 구현 시 고려사항 (서비스 시 고려사항)
- 다양한 포맷(Word, PDF, PPT, 이미지 등)의 RFP에 대응되도록 Assistant 지속적인 업그레이드 필요
- 직원 사무분장 최신 데이터 획득 Pipeline 협의 필요 (최신 데이터 획득 필수)
- 사무분장 데이터 포맷 개선 (RAG Assistant 답변 품질 지속 개선 필요)
- 최신 사무분장 Raw 데이터 Knowledge 자동 포맷팅 방법 (RPA 등 자동화 Tool을 통한 Knowledge 전처리 필요)

## 통합 대상 서비스 (예상)
- KT DS Works AI의 AI Makers로 배포

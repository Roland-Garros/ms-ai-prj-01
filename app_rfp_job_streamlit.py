### RFP 분석 결과 기반 KT DS 내부 인력 추천 Assistant

import os
import time
from openai import AzureOpenAI
import streamlit as st

# 환경변수 로드
from dotenv import load_dotenv
load_dotenv()

os.system('cls' if os.name == 'nt' else 'clear')

# 필수 환경변수 획득
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_MODEL_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME")
AZURE_OPENAI_DEFAULT_ASSISTANT_ID = os.getenv("AZURE_OPENAI_DEFAULT_ASSISTANT_ID")
AZURE_OPENAI_JOB_ASSISTANT_ID = os.getenv("AZURE_OPENAI_JOB_ASSISTANT_ID")
AZURE_OPENAI_RFP_ASSISTANT_ID = os.getenv("AZURE_OPENAI_RFP_ASSISTANT_ID")
AZURE_OPENAI_JOB_VECTOR_STORE_ID = os.getenv("AZURE_OPENAI_JOB_VECTOR_STORE_ID")
AZURE_OPENAI_RFP_VECTOR_STORE_ID = os.getenv("AZURE_OPENAI_RFP_VECTOR_STORE_ID")


def get_azure_openai_client():
    """
    Azure OpenAI 클라이언트 생성
    """
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version="2024-05-01-preview"
    )


def get_azure_openai_assistant(client):
    """
    Azure OpenAI 어시스턴트 생성
       > Azure OpenAI에 미리 만들어놓은 Assistant를 ID로 호출하여 사용하므로
       > 신규 Assistant를 즉시 생성하는 이 로직은 쓰이지 않음
    """
    return client.beta.assistants.create(
        model=AZURE_OPENAI_MODEL_DEPLOYMENT_NAME,
        instructions="""
        ### 명령문
         - 당신은 프로젝트 제안서와 같은 RFP(Request for Proposal) 성격의 문서를 분석하는 전문가입니다.
         - 사용자가 업로드한 문서를 다각도로 분석하여 프로젝트 핵심 제안 사항을 추출합니다.
         - 핵심 제안 사항은 최대 5개 까지 추출합니다.
         - 답변은 무조건 한국어로 합니다.
         - 영어 고유 명사는 그대로 사용해도 됩니다.

        ### 제약사항
         - 중복 정보는 답변에서 제외합니다.
         - 핵심 제안 사항은 무조건 1개 이상은 도출해야 합니다.
         - 답변은 반드시 "답변형식"에 맞춰서 합니다.

        ### 참고사항
         - 현재 이 회사는 KT DS이며 KT 그룹 계열사입니다.
         - 사내 RPA 툴은 Power Automate, AntBot 입니다.
        
        ### 답변형식
        1. [핵심 제안 사항]
        -----
        """,
        tools=[{"type":"file_search"}],
        tool_resources={"file_search":{"vector_store_ids":[AZURE_OPENAI_RFP_VECTOR_STORE_ID]}},
        temperature=0.2,
        top_p=0.8
    )


def get_azure_openai_assistant_thread(client):
    """
    Azure OpenAI 어시스턴트 스레드 생성
    """
    return client.beta.threads.create()


def list_azure_openai_assistant_threads(client):
    """
    Azure OpenAI 어시스턴트 스레드 목록 조회
    """
    threads = client.beta.threads.list()
    return list(threads)


def delete_azure_openai_assistant_vector_store(client, v_id):
    """
    Azure OpenAI의 특정 Vector Store와 관련된 원본 데이터 파일 전부 삭제
    """
    # RFP Assistant가 바라보는 벡터 스토어 파일 전체 조회
    vs_list = client.vector_stores.files.list(
        vector_store_id=v_id
    )
    for vs in vs_list:
        # 조회된 벡터 스토어 파일 전체 삭제
        delete_result = client.vector_stores.files.delete(
            vector_store_id=v_id,
            file_id=vs.id
        )
        # 벡터 스토어에 업로드되었던 데이터 파일 원본도 삭제
        delete_result = client.files.delete(
            file_id=vs.id
        )


def get_azure_openai_assistant_message(client, assistant, thread, user_input):
    """
    Azure OpenAI 어시스턴트 메시지 생성
    """
    # 쓰레드에 사용자 입력 추가
    message = client.beta.threads.messages.create(
		thread_id=thread.id,
		role="user",
        content=user_input
	)
    # 쓰레드를 run 객체에 얹어서 실행
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    # run 객체 실행이 끝나서 메시지 생성이 완료될때까지 대기
    while run.status in ['queued', 'in_progress', 'cancelling']:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
    # run 객체 실행 종료 후처리
    if run.status == 'completed':
        thread_messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        thread_messages = list(thread_messages)
    elif run.status == 'requires_action':
        # the assistant requires calling some functions
        # and submit the tool outputs back to the run
        pass
    else:
        pass
    # Assistant 답변 메시지 반환
    return thread_messages[0].content[0].text.value


def run_job_assistant(msg_text):
    """
    사무분장 기반 사내 인력 추천 Assistant 호출
    """
    # 버튼 클릭 시 원하는 동작
    st.session_state.messages.append({'role': 'assistant', 'content': '사내 담당자 추천을 시작합니다.'})
    st.chat_message('system').write("사내 담당자 추천을 시작합니다.")
    # job assistant 추가 호출
    with st.spinner('****** 사내 담당자 분석 중'):
        response = get_azure_openai_assistant_message(
            azure_openai_client, 
            azure_openai_client.beta.assistants.retrieve(assistant_id=AZURE_OPENAI_JOB_ASSISTANT_ID), 
            get_azure_openai_assistant_thread(azure_openai_client), 
            msg_text
        )
        # 사내 담당자 추천 결과 출력
        st.session_state.messages.append({'role': 'assistant', 'content': response})
        st.chat_message('assistant').write(response)


def set_run_job_state(i):
    """
    사내 담당자 추천 시작 버튼 status 조정 함수
      > 0 : Not Start
      > 1 : Start
    """
    st.session_state.run_job_btn_clicked = i


# Azure OpenAI 클라이언트 초기화
azure_openai_client = get_azure_openai_client()

# Azure OpenAI RFP Assistant Vector Store 초기화
if 'rfp_vector_cleared' not in st.session_state:
    # RFP Assistant가 바라보는 벡터 스토어 내부 및 원본 파일 전체 삭제
    delete_azure_openai_assistant_vector_store(azure_openai_client, AZURE_OPENAI_RFP_VECTOR_STORE_ID)
    # 초기화 완료 status 설정
    st.session_state['rfp_vector_cleared'] = True

# StreamLit 기본 UI 설정
st.title('Azure OpenAI 기반 RFP 분석 및 수행 인력 추천 Assistant')
st.write('업로드된 RFP 핵심 내용 분석 + 분석 결과 기반 KT DS 수행인력 추천')

# 대화 초기화 버튼
sidebar_button_clicked=st.sidebar.button('새 대화')
if sidebar_button_clicked:
    st.session_state['messages'] = []
    # RFP Assistant가 바라보는 벡터 스토어 내부 및 원본 파일 전체 삭제
    delete_azure_openai_assistant_vector_store(azure_openai_client, AZURE_OPENAI_RFP_VECTOR_STORE_ID)

# 채팅 기록의 초기화
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
    # RFP Assistant가 바라보는 벡터 스토어 내부 및 원본 파일 전체 삭제
    delete_azure_openai_assistant_vector_store(azure_openai_client, AZURE_OPENAI_RFP_VECTOR_STORE_ID)

# 채팅 기록 표시
for message in st.session_state['messages']:
    st.chat_message(message['role']).write(message['content'])

# 사용자 입력 받기
if user_input := st.chat_input(
    placeholder='RFP 파일을 업로드하고, 분석 지시사항을 입력하세요 : ', 
    accept_file=True,
    file_type=['md', 'pdf', 'doc', 'docx', 'txt', 'csv', 'xls', 'xlsx']
    ):
    # 사용자 입력 메시지 추가
    st.session_state['messages'].append({'role': 'user', 'content': user_input.text})
    st.chat_message('user').write(user_input.text)
    
    # 사용자 첨부파일 Azure OpenAI Assistant Vector Store 업로드 처리
    if len(user_input.files) > 0:
        with st.spinner('*** RFP 파일 업로드 중'):
            uploaded_file = user_input.files[0]
            # RFP Assistant가 바라보는 벡터 스토어 내부 및 원본 파일 전체 삭제
            delete_azure_openai_assistant_vector_store(azure_openai_client, AZURE_OPENAI_RFP_VECTOR_STORE_ID)
            # RFP Azure OpenAI Assistant가 바라보는 벡터 스토어에 파일 업로드
            upload_result = azure_openai_client.vector_stores.files.upload_and_poll(
                vector_store_id=AZURE_OPENAI_RFP_VECTOR_STORE_ID,
                file=uploaded_file
            )
        # 사용자 첨부파일 업로드 완료 문구 출력
        st.session_state.messages.append({'role': 'system', 'content': 'RFP 파일 업로드 완료. 분석을 시작합니다!'})
        st.chat_message('system').write('RFP 파일 업로드 완료. 분석을 시작합니다!')

        # RFP 분석 Assistant 답변 요청
        with st.spinner('****** RFP 파일 분석 결과 생성 중'):
            response = get_azure_openai_assistant_message(
                azure_openai_client, 
                azure_openai_client.beta.assistants.retrieve(assistant_id=AZURE_OPENAI_RFP_ASSISTANT_ID), 
                get_azure_openai_assistant_thread(azure_openai_client), 
                user_input.text
            )
        # RFP 분석 Assistant 답변 출력
        st.session_state.messages.append({'role': 'assistant', 'content': response})
        st.chat_message('assistant').write(response)
        st.session_state['rfp_response'] = response
        # 사내 담당자 추천 프로세스 진행 여부
        str_job_search_offer = 'RFP 분석이 완료되었습니다! RFP 분석 결과를 활용하여 사내 담당자 추천까지 진행하시겠습니까?'
        st.session_state.messages.append({'role': 'system', 'content': str_job_search_offer})
        st.chat_message('system').write(str_job_search_offer)
        # 사내 담당자 추천 버튼 표시
        #   -> 이 버튼 클릭 시 RFP 분석 데이터 기반 사내 담당자 추천 Assistant 호출
        st.chat_message('system').button("사내 담당자 추천 진행하기", on_click=set_run_job_state, args=[1])
    
    # 사용자가 첨부파일을 업로드하지 않은 경우 일반 대화 진행
    else:
        with st.spinner('*** 답변 생성 중'):
            response = get_azure_openai_assistant_message(
                azure_openai_client, 
                azure_openai_client.beta.assistants.retrieve(assistant_id=AZURE_OPENAI_DEFAULT_ASSISTANT_ID), 
                get_azure_openai_assistant_thread(azure_openai_client), 
                user_input.text
            )
        # Assistant 답변 출력
        st.session_state.messages.append({'role': 'assistant', 'content': response})
        st.chat_message('assistant').write(response)


# 사내 담당자 추천 Assistant 호출 진행 여부 초기화
if 'run_job_btn_clicked' not in st.session_state:
    st.session_state.run_job_btn_clicked = 0

# 사내 담당자 추천 Assistant 호출
#   -> 채팅 내에서 버튼을 클릭하여 특정 함수를 실행하려면 status 컨트롤 필수
if st.session_state.run_job_btn_clicked == 1:
    # 사내 담당자 추천 Assistant 호출 처리
    run_job_assistant(st.session_state['rfp_response'])
    # Assistant 호출 진행 여부 초기화
    st.session_state.run_job_btn_clicked = 0
    st.session_state.messages.append({'role': 'system', 'content': '사내 담당자 추천이 완료되었습니다!'})
    st.chat_message('system').write('사내 담당자 추천이 완료되었습니다!')

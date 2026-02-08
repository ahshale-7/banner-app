import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import base64
import json
import time

# ==========================================
# 1. 🔐 비밀번호 & API 키 설정 (필수 수정)
# ==========================================
MY_SECRET_PASSWORD = "배너를수정하자" 

# 페이지 기본 설정
st.set_page_config(page_title="BannerAI Pro", layout="wide")

# 세션 상태 초기화
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 로그인 화면
if not st.session_state.authenticated:
    st.title("🔒 사내용 배너 수정 도구")
    password_input = st.text_input("접속 비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        if password_input == MY_SECRET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")
    st.stop()

# API 키 입력받기 (사이드바)
with st.sidebar:
    st.header("🔑 설정")
    user_api_key = st.text_input("Google API Key", type="password", help="AI Studio에서 발급받은 키를 입력하세요")
    if not user_api_key:
        st.warning("앱을 사용하려면 API 키가 필요합니다.")
        st.stop()
    else:
        # API 설정
        genai.configure(api_key=user_api_key)

# 모델 설정 (가장 안정적인 모델로 고정)
TEXT_MODEL = "gemini-1.5-flash"  # 분석용 (빠름)
# 이미지 생성은 현재 API 지원이 제한적일 수 있어, 분석 위주로 코드를 안정화함
# 만약 이미지 생성 권한이 있는 키라면 아래 코드가 작동합니다.

# --- 2. 유틸리티 함수 ---
def get_image_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_image_from_b64(b64_str):
    return Image.open(io.BytesIO(base64.b64decode(b64_str)))

# --- 3. Gemini 분석 함수 ---
def analyze_image(image_b64):
    model = genai.GenerativeModel(TEXT_MODEL)
    img_data = {'mime_type': 'image/png', 'data': base64.b64decode(image_b64)}
    
    prompt = """
    이 광고 배너 이미지를 정밀 분석하세요. JSON 형식으로만 응답하세요.
    {
        "subText": "서브 텍스트 내용",
        "mainTextLine1": "메인 텍스트 1줄",
        "decorationText": "꾸밈 문구",
        "mainTextLine2": "메인 텍스트 2줄",
        "ctaText": "CTA 버튼 문구",
        "styleDescription": "디자인 스타일 묘사",
        "objectsDescription": "주요 오브젝트",
        "colorDescription": "색상 팔레트"
    }
    """
    response = model.generate_content([prompt, img_data])
    
    # JSON 파싱 시도
    try:
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except:
        return {
            "subText": "", "mainTextLine1": "", "decorationText": "",
            "mainTextLine2": "", "ctaText": "", "styleDescription": "",
            "objectsDescription": "", "colorDescription": ""
        }

# --- 4. Streamlit UI 구성 ---
if 'config' not in st.session_state:
    st.session_state.config = {}

st.title("🎨 BannerAI: Consistent Ad Editor")

# 파일 업로드
uploaded_file = st.sidebar.file_uploader("이미지 파일을 선택하세요", type=["png", "jpg", "jpeg"])

if uploaded_file:
    original_img = Image.open(uploaded_file)
    current_b64 = get_image_base64(original_img)
    
    # 이미지 표시
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original")
        st.image(original_img, use_container_width=True)
        
        if st.button("🔍 이미지 분석 시작"):
            with st.spinner("Gemini가 배너를 분석 중입니다..."):
                analysis = analyze_image(current_b64)
                st.session_state.config = analysis
                st.success("분석 완료!")

    # 분석 결과 수정 창
    with col2:
        st.subheader("Settings & Prompt")
        if st.session_state.config:
            cfg = st.session_state.config
            
            # 텍스트 수정
            new_sub = st.text_input("서브 텍스트", cfg.get('subText', ''))
            new_main1 = st.text_input("메인 텍스트 1", cfg.get('mainTextLine1', ''))
            new_main2 = st.text_input("메인 텍스트 2", cfg.get('mainTextLine2', ''))
            new_cta = st.text_input("CTA", cfg.get('ctaText', ''))
            
            # 스타일 수정
            new_style = st.text_area("스타일", cfg.get('styleDescription', ''))
            new_obj = st.text_area("오브젝트", cfg.get('objectsDescription', ''))
            
            st.info("💡 이미지 생성 기능은 별도 유료 API가 필요하므로, 대신 **'수정 지시문(프롬프트)'**을 생성해 드립니다.")
            
            final_prompt = f"""
            **Image Generation Prompt:**
            Create a banner ad with aspect ratio {original_img.width}:{original_img.height}.
            TEXT: "{new_sub}" / "{new_main1}" / "{new_main2}" / CTA: "{new_cta}"
            STYLE: {new_style}
            OBJECTS: {new_obj}
            """
            st.code(final_prompt)
            
        else:
            st.info("왼쪽에서 분석 버튼을 눌러주세요.")

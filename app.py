import streamlit as st
import requests
import pandas as pd
from openai import OpenAI

# ================= 1. 网页全局配置 =================
st.set_page_config(page_title="AI 城市规划决策系统", page_icon="🏗️", layout="wide")
st.title("🏗️ AI 城市规划决策系统 - 全国通用版")
st.markdown("集成周边配套扫描、跨城市交通测算、AI 综合价值评估。")

# ================= 2. 侧边栏：参数输入 =================
st.sidebar.header("🔑 密钥授权")

# 尝试去系统的密码保险箱里找钥匙，如果找不到（比如别人在用），就留空
default_amap = st.secrets.get("AMAP_KEY", "")
default_ai = st.secrets.get("DEEPSEEK_KEY", "")

# 把找到的钥匙作为输入框的“默认值 (value)”填进去
amap_key = st.sidebar.text_input("高德 API Key", type="password", value=default_amap)
ai_key = st.sidebar.text_input("DeepSeek API Key", type="password", value=default_ai)

st.sidebar.divider()
st.sidebar.header("📍 地块定位")
center = st.sidebar.text_input("中心经纬度", value="117.200983,39.128867")
radius = st.sidebar.slider("搜索半径 (米)", 500, 5000, 1000)

st.sidebar.divider()
st.sidebar.header("🚗 交通测算配置")
city = st.sidebar.text_input("目标城市", value="天津")
landmarks = st.sidebar.text_input("核心节点 (逗号分隔)", value="火车站,机场,市政府,核心商圈")

# ================= 3. 核心功能逻辑 =================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔍 周边配套扫描")
    poi_keywords = st.text_input("搜索配套关键词", value="餐饮,写字楼,购物,学校")
    if st.button("开始扫描周边"):
        if not amap_key: st.error("请先输入高德Key")
        else:
            with st.spinner("抓取配套数据中..."):
                url = f"https://restapi.amap.com/v3/place/around?key={amap_key}&location={center}&keywords={poi_keywords}&radius={radius}&output=json&offset=20"
                data = requests.get(url).json()
                if data['status'] == '1':
                    pois = data['pois']
                    clean_pois = [{'名称': p['name'], '类型': p['type'], '距离(米)': int(p['distance'])} for p in pois]
                    # 获取到数据后，存入“记忆背包”
                    st.session_state['poi_data'] = pd.DataFrame(clean_pois)
                else: st.error("抓取失败")
                
    # 🌟 核心修复点：把展示表格的逻辑移到按钮外面
    # 意思是：只要“记忆背包”里有配套数据，就一直显示出来，不管页面怎么刷新
    if 'poi_data' in st.session_state:
        st.dataframe(st.session_state['poi_data'], use_container_width=True)

with col2:
    st.subheader("🚥 交通通达性分析")
    if st.button("开始测算通勤"):
        if not amap_key: st.error("请先输入高德Key")
        else:
            with st.spinner(f"正在分析 {city} 交通网..."):
                traffic_results = []
                for name in landmarks.split(','):
                    s_url = f"https://restapi.amap.com/v3/place/text?key={amap_key}&keywords={name}&city={city}&output=json"
                    s_res = requests.get(s_url).json()
                    if s_res['status'] == '1' and s_res['pois']:
                        target = s_res['pois'][0]['location']
                        r_url = f"https://restapi.amap.com/v3/direction/driving?key={amap_key}&origin={center}&destination={target}"
                        r_res = requests.get(r_url).json()
                        if r_res['status'] == '1':
                            path = r_res['route']['paths'][0]
                            traffic_results.append({
                                '目标节点': name,
                                '实际匹配': s_res['pois'][0]['name'],
                                '距离(km)': round(int(path['distance'])/1000, 1),
                                '耗时(分)': int(path['duration'])//60
                            })
                # 获取到数据后，存入“记忆背包”
                st.session_state['traffic_data'] = pd.DataFrame(traffic_results)
                
    # 🌟 核心修复点：同理，把展示交通表格的逻辑移到按钮外面
    if 'traffic_data' in st.session_state:
        st.table(st.session_state['traffic_data'])

# ================= 4. AI 智能规划咨询室 (对话模式) =================
st.divider()
st.subheader("💬 AI 智能规划咨询室")

# 1. 初始化聊天记录的“记忆背包”
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. 初始报告生成按钮 (只有在没有任何聊天记录时才显示)
if len(st.session_state.messages) == 0:
    if st.button("✨ 基于抓取数据，生成初始诊断报告"):
        if not ai_key: 
            st.error("请先输入 DeepSeek API Key")
        elif 'poi_data' not in st.session_state or 'traffic_data' not in st.session_state:
            st.warning("请先完成上方左侧和右侧的两项数据采集。")
        else:
            with st.spinner("AI 正在深度研判地块价值..."):
                client = OpenAI(api_key=ai_key, base_url="https://api.deepseek.com")
                
                # 把表格数据拼装好
                context = f"""
                地块所在城市：{city}
                1. 周边配套抽样：\n{st.session_state['poi_data'].head(10).to_string()}
                2. 核心交通通达性：\n{st.session_state['traffic_data'].to_string()}
                """
                
                # 构造第一句 Prompt
                first_prompt = f"""
                你是一位拥有20年经验的城市规划院长和地产资深顾问。
                请根据以下调研数据，为甲方提交一份《地块开发潜力综合评估报告》。
                报告需包含：1.[地块成色诊断] 2.[交通骨架评价] 3.[建议开发模式] 4.[规划师忠告]。
                要求：专业、锐利、客观，拒绝废话。
                
                调研数据：
                {context}
                """
                
                # 把我们的系统要求伪装成用户的第一次发言，存入记忆
                st.session_state.messages.append({"role": "user", "content": first_prompt})
                
                # 呼叫 AI
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=st.session_state.messages
                )
                
                # 把 AI 写的报告也存入记忆
                reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
                # 刷新页面，让下方的聊天气泡显示出来
                st.rerun()

# 3. 渲染历史聊天气泡
for msg in st.session_state.messages:
    # 为了界面美观，如果是第一句带有大量丑陋表格数据的系统提示词，我们换个优雅的显示方式
    if msg["role"] == "user" and "你是一位拥有20年经验" in msg["content"]:
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown("*(系统指令)*：请基于当前抓取的数据，生成初始评估报告。")
    else:
        # 正常的聊天气泡
        avatar_icon = "🧑‍💻" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar_icon):
            st.markdown(msg["content"])

# 4. 底部的对话输入框 (供甲方持续追问)
if prompt := st.chat_input("向 AI 规划师提问，例如：‘如果这里改做高端养老地产，你觉得可行吗？’"):
    if not ai_key:
        st.error("请先输入 DeepSeek API Key")
    else:
        # 显示用户刚刚输入的问题，并存入记忆
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 呼叫 AI 进行回答 (注意：这里把包含所有历史记录的 messages 发给了 AI)
        with st.chat_message("assistant", avatar="🤖"):
            client = OpenAI(api_key=ai_key, base_url="https://api.deepseek.com")
            
            with st.spinner("思考中..."):
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=st.session_state.messages # 将全部上下文喂给AI
                )
                reply = response.choices[0].message.content
                st.markdown(reply)
                
        # 把 AI 的最新回答存入记忆
        st.session_state.messages.append({"role": "assistant", "content": reply})
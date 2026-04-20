import streamlit as st
import requests
import pandas as pd

# ================= 网页界面设计 =================
st.set_page_config(page_title="城市规划AI助手", page_icon="🗺️")
st.title("🗺️ 城市规划大师 - 选址调研神器")
st.markdown("不用再改代码啦！在左侧输入信息，点击按钮直接获取周边配套数据。")

st.sidebar.header("⚙️ 调研参数设置")
my_key = st.sidebar.text_input("🔑 你的高德API Key", type="password") 
center = st.sidebar.text_input("📍 中心坐标 (经度,纬度)", value="117.200983,39.128867")
keywords = st.sidebar.text_input("🔍 搜索关键词 (如：咖啡馆, 医院)", value="咖啡馆")
radius = st.sidebar.slider("📏 搜索半径 (米)", min_value=100, max_value=5000, value=1000, step=100) 

# ================= 核心处理逻辑 =================
if st.sidebar.button("🚀 开始一键调研"):
    if not my_key:
        st.error("⚠️ 请先输入高德API Key！")
    else:
        with st.spinner('正在向高德地图发送请求，请稍候...'):
            url = f"https://restapi.amap.com/v3/place/around?key={my_key}&location={center}&keywords={keywords}&radius={radius}&output=json"
            
            try:
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if data['status'] == '1':
                    pois = data['pois']
                    if len(pois) == 0:
                        st.warning("在这个范围内没找到目标，试试扩大半径或换个关键词？")
                    else:
                        st.success(f"✅ 抓取成功！共找到 {len(pois)} 个目标。")
                        
                        # 🌟 修复报错的关键：数据清洗逻辑 🌟
                        clean_data = []
                        for item in pois:
                            # 提取地址，如果高德发来的是奇怪的格式（不是文字），就统一写成"暂无地址"
                            addr = item.get('address')
                            if not isinstance(addr, str):
                                addr = "暂无地址"
                            
                            # 把清洗干净的数据放进新列表
                            clean_data.append({
                                '名称': item.get('name', '未知名称'),
                                '详细地址': addr,
                                '距离(米)': item.get('distance', '未知')
                            })
                        
                        # 用清洗后的干净数据生成表格，Pandas 就不会报错了
                        df = pd.DataFrame(clean_data)
                        
                        st.dataframe(df, use_container_width=True)
                        
                        csv = df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 下载为CSV表格（Excel可用）",
                            data=csv,
                            file_name=f'{keywords}_调研结果.csv',
                            mime='text/csv',
                        )
                else:
                    st.error(f"❌ 抓取失败！高德报错：{data.get('info', '未知错误')}")
            except Exception as e:
                st.error(f"❌ 网络似乎有点问题：{e}")
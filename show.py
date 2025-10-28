import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

# ======================================================
# ✅ Browser LocalStorage 持久化解决方案
# ======================================================
LOCALSTORAGE_JS = """
<script>
function saveData(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

function loadData(key) {
    return JSON.parse(localStorage.getItem(key));
}

function sendDataToStreamlit(key) {
    const data = loadData(key);
    const event = new CustomEvent("streamlit:setData", { detail: { key, data }});
    window.dispatchEvent(event);
}

window.addEventListener("streamlit:saveData", (event) => {
    const { key, value } = event.detail;
    saveData(key, value);
});

document.addEventListener("DOMContentLoaded", () => {
    sendDataToStreamlit("user_data");
});
</script>
"""

components.html(LOCALSTORAGE_JS, height=0)

# ======================================================
# ✅ LocalStorage Handler
# ======================================================
def save_to_local(data):
    components.html(
        f"""
        <script>
        window.dispatchEvent(new CustomEvent("streamlit:saveData", {{
            detail: {{ key: "user_data", value: {json.dumps(data)} }}
        }}));
        </script>
        """,
        height=0,
    )

# 响应数据回填
if "user_data" not in st.session_state:
    st.session_state.user_data = {}

def receive_data():
    event_data = st.session_state.get("data_from_js", None)
    if event_data:
        st.session_state.user_data = event_data


# ======================================================
# ✅ 初始化数据
# ======================================================
ALL_PRODUCTS = ["手机", "电脑", "耳机", "手表", "平板", "键盘", "鼠标"]

if "step" not in st.session_state:
    st.session_state.step = 1
if "current_user" not in st.session_state:
    st.session_state.current_user = None

receive_data()


# ======================================================
# ✅ Step1 用户登录/注册
# ======================================================
if st.session_state.step == 1:
    st.title("🧠 个性化推荐系统")
    user_list = list(st.session_state.user_data.keys())

    option = st.radio("请选择：", ["登录已有用户", "注册新用户"])

    if option == "登录已有用户":
        if user_list:
            name = st.selectbox("选择用户", user_list)
            if st.button("进入系统"):
                st.session_state.current_user = name
                st.session_state.step = 2
                st.rerun()
        else:
            st.info("暂无用户，请先注册")

    else:
        name = st.text_input("新用户名")
        if st.button("注册用户"):
            if name.strip() == "":
                st.error("用户名不能为空")
            elif name in st.session_state.user_data:
                st.warning("用户已存在")
            else:
                st.session_state.user_data[name] = {"浏览": [], "购买": []}
                save_to_local(st.session_state.user_data)
                st.session_state.current_user = name
                st.session_state.step = 2
                st.rerun()

# ======================================================
# ✅ Step2 编辑商品行为数据
# ======================================================
elif st.session_state.step == 2:
    user = st.session_state.current_user
    data = st.session_state.user_data[user]

    st.subheader(f"{user} 的商品记录")

    st.write("📖 浏览：", ", ".join(data["浏览"]))
    st.write("🛍️ 购买：", ", ".join(data["购买"]))

    st.write("---")
    st.write("🔄 添加行为记录")

    new_view = st.multiselect("选择浏览商品", [p for p in ALL_PRODUCTS if p not in data["浏览"]])
    new_buy = st.multiselect("选择购买商品", [p for p in ALL_PRODUCTS if p not in data["购买"]])

    custom_v = st.text_input("自定义浏览商品 例：VR眼镜")
    custom_b = st.text_input("自定义购买商品 例：电动滑板")

    if st.button("✅ 保存并推荐"):
        data["浏览"].extend(new_view)
        data["购买"].extend(new_buy)

        if custom_v:
            for item in [x.strip() for x in custom_v.split(",")]:
                if item and item not in ALL_PRODUCTS:
                    ALL_PRODUCTS.append(item)
                if item not in data["浏览"]:
                    data["浏览"].append(item)

        if custom_b:
            for item in [x.strip() for x in custom_b.split(",")]:
                if item and item not in ALL_PRODUCTS:
                    ALL_PRODUCTS.append(item)
                if item not in data["购买"]:
                    data["购买"].append(item)

        save_to_local(st.session_state.user_data)

        st.session_state.step = 3
        st.rerun()

    if st.button("⬅ 回到登录"):
        st.session_state.step = 1
        st.rerun()

# ======================================================
# ✅ Step3 推荐结果（Top3）
# ======================================================
elif st.session_state.step == 3:
    user = st.session_state.current_user
    data = st.session_state.user_data

    st.subheader("🎯 推荐结果展示")

    my_items = set(data[user]["浏览"] + data[user]["购买"])

    def jac(a, b):
        return len(a & b) / len(a | b) if a | b else 0

    sims = []
    for u in data:
        if u == user: continue
        sims.append((u, jac(my_items, set(data[u]["浏览"] + data[u]["购买"]))))

    sims = sorted(sims, key=lambda x: x[1], reverse=True)[:3]

    if not sims:
        st.warning("暂无其他用户")
    else:
        for other, s in sims:
            if s == 0: continue
            other_items = set(data[other]["浏览"] + data[other]["购买"])
            recs = list(other_items - my_items)

            if recs:
                st.markdown(f"**🧍 相似用户：{other}（相似度 {s:.2f}）**")
                for r in recs:
                    st.success(f"✅ {r} —— 推荐理由：{other}也喜欢")

    if st.button("继续添加数据"):
        st.session_state.step = 2
        st.rerun()

    if st.button("🏠 回到首页"):
        st.session_state.step = 1
        st.rerun()

import streamlit as st
import pandas as pd
from streamlit.runtime.storage import Storage

# 初始化 Storage
storage = Storage("reco_storage")

# 初始化数据结构（首次运行）
if storage.get("user_data") is None:
    storage.set("user_data", {})
if storage.get("all_products") is None:
    storage.set("all_products", ["手机", "电脑", "耳机", "手表", "平板", "键盘", "鼠标", "相机", "音箱", "显示器"])

# Session state 控制流程
if "step" not in st.session_state:
    st.session_state.step = 1
if "current_user" not in st.session_state:
    st.session_state.current_user = None


# ============= STEP 1：登录 注册 =================
if st.session_state.step == 1:
    st.title("🧠 个性化推荐系统")
    st.subheader("Step 1 - 登录或注册")

    user_data = storage.get("user_data")
    user_list = list(user_data.keys())

    op = st.radio("操作：", ["登录已有用户", "注册新用户"])

    if op == "登录已有用户":
        if user_list:
            sel = st.selectbox("选择用户：", user_list)
            if st.button("进入系统"):
                st.session_state.current_user = sel
                st.session_state.step = 2
                st.rerun()
        else:
            st.warning("暂无用户，请先注册！")

    else:
        new_name = st.text_input("新用户名：")
        if st.button("注册"):
            if not new_name.strip():
                st.error("不能为空！")
            elif new_name in user_data:
                st.warning("用户已存在")
            else:
                user_data[new_name] = {"浏览": set(), "购买": set()}
                storage.set("user_data", user_data)
                st.session_state.current_user = new_name
                st.session_state.step = 2
                st.rerun()


# ============= STEP 2：用户行为记录 ================
elif st.session_state.step == 2:
    user_data = storage.get("user_data")
    all_products = storage.get("all_products")

    u = st.session_state.current_user
    st.subheader(f"Step 2 - 管理 {u} 的商品行为")

    behavior = user_data[u]

    # 展示历史记录
    st.write("📖 浏览：", ", ".join(behavior["浏览"]) or "暂无记录")
    st.write("🛍 购买：", ", ".join(behavior["购买"]) or "暂无记录")

    st.write("### 添加记录")

    new_view = st.multiselect("浏览：", [x for x in all_products if x not in behavior["浏览"]])
    new_buy = st.multiselect("购买：", [x for x in all_products if x not in behavior["购买"]])

    cv = st.text_input("自定义浏览（逗号隔开）")
    cb = st.text_input("自定义购买（逗号隔开）")

    if st.button("保存并推荐"):
        behavior["浏览"].update(new_view)
        behavior["购买"].update(new_buy)

        if cv.strip():
            behavior["浏览"].update([x.strip() for x in cv.split(",")])
        if cb.strip():
            behavior["购买"].update([x.strip() for x in cb.split(",")])

        # 更新全局商品库
        all_products = list(set(all_products) | behavior["浏览"] | behavior["购买"])

        user_data[u] = behavior
        storage.set("user_data", user_data)
        storage.set("all_products", all_products)

        st.session_state.step = 3
        st.rerun()

    if st.button("⬅ 返回"):
        st.session_state.step = 1
        st.rerun()


# ============= STEP 3：推荐结果展示 ================
elif st.session_state.step == 3:
    user_data = storage.get("user_data")
    u = st.session_state.current_user
    behavior = user_data[u]

    st.subheader("Step 3 - 推荐结果")
    st.write("当前用户：", u)

    pref = behavior["浏览"] | behavior["购买"]

    # 相似度计算：Top3
    def sim(a, b):
        return len(a & b) / len(a | b) if a | b else 0

    sims = []
    for other, data in user_data.items():
        if other == u: continue
        score = sim(pref, data["浏览"] | data["购买"])
        if score > 0:
            sims.append((other, score))

    sims = sorted(sims, key=lambda x: x[1], reverse=True)[:3]

    if sims:
        for other, score in sims:
            st.info(f"与您相似用户：**{other}**（相似度 {score:.2f}）")

            other_pref = user_data[other]["浏览"] | user_data[other]["购买"]
            rec = other_pref - pref

            for item in rec:
                with st.container(border=True):
                    st.write(f"📌 推荐商品：**{item}**")
                    st.caption(f"推荐理由：**{other} 也喜欢这个！**")
    else:
        st.warning("缺少有效推荐！")

    st.divider()
    if st.button("继续编辑"):
        st.session_state.step = 2
        st.rerun()
    if st.button("🏠 返回首页"):
        st.session_state.step = 1
        st.rerun()

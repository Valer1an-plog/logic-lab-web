import streamlit as st
import json
import os

DATA_FILE = "user_data.json"

# ================= 持久化存储 =================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # JSON 不支持 set，这里转回来
            for user in data["user_data"]:
                data["user_data"][user]["浏览"] = set(data["user_data"][user]["浏览"])
                data["user_data"][user]["购买"] = set(data["user_data"][user]["购买"])
            return data
    return {
        "user_data": {},
        "all_products": ["手机", "电脑", "耳机", "手表", "平板", "键盘", "鼠标", "相机", "音箱", "显示器"]
    }

def save_data(data):
    # 存回 JSON（转 list）
    out = {
        "user_data": {},
        "all_products": data["all_products"]
    }
    for user, behaviors in data["user_data"].items():
        out["user_data"][user] = {
            "浏览": list(behaviors["浏览"]),
            "购买": list(behaviors["购买"])
        }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


# ================= Session 初始化 =================
if "step" not in st.session_state:
    st.session_state.step = 1
if "current_user" not in st.session_state:
    st.session_state.current_user = None

data = load_data()

# ================= STEP 1：登录 注册 =================
if st.session_state.step == 1:
    st.title("🧠 个性化推荐系统")
    user_list = list(data["user_data"].keys())
    
    mode = st.radio("请选择操作：", ["登录已有用户", "注册新用户"])
    
    if mode == "登录已有用户":
        if user_list:
            sel = st.selectbox("选择用户：", user_list)
            if st.button("进入"):
                st.session_state.current_user = sel
                st.session_state.step = 2
                st.rerun()
        else:
            st.warning("暂无用户，请先注册！")

    else:
        new_user = st.text_input("请输入用户名：")
        if st.button("注册"):
            if not new_user.strip():
                st.error("用户名不能为空")
            elif new_user in user_list:
                st.warning("已存在")
            else:
                data["user_data"][new_user] = {"浏览": set(), "购买": set()}
                save_data(data)
                st.session_state.current_user = new_user
                st.session_state.step = 2
                st.rerun()


# ================= STEP 2：添加行为记录 =================
elif st.session_state.step == 2:
    u = st.session_state.current_user
    bev = data["user_data"][u]
    
    st.subheader(f"用户：{u}")
    st.write("📖 浏览：", ", ".join(bev["浏览"]) or "暂无")
    st.write("🛍 购买：", ", ".join(bev["购买"]) or "暂无")

    st.divider()
    
    prod = data["all_products"]

    new_view = st.multiselect("添加浏览：", [x for x in prod if x not in bev["浏览"]])
    new_buy  = st.multiselect("添加购买：", [x for x in prod if x not in bev["购买"]])

    cv = st.text_input("自定义浏览（逗号隔开）")
    cb = st.text_input("自定义购买（逗号隔开）")

    if st.button("保存并推荐"):
        bev["浏览"].update(new_view)
        bev["购买"].update(new_buy)

        if cv.strip():
            bev["浏览"].update([x.strip() for x in cv.split(",")])
        if cb.strip():
            bev["购买"].update([x.strip() for x in cb.split(",")])

        # 更新商品库
        data["all_products"] = sorted(list(set(prod) | bev["浏览"] | bev["购买"]))

        save_data(data)
        st.session_state.step = 3
        st.rerun()

    if st.button("⬅ 返回首页"):
        st.session_state.step = 1
        st.rerun()


# ================= STEP 3：推荐展示 =================
elif st.session_state.step == 3:
    u = st.session_state.current_user
    bev = data["user_data"][u]
    pref = bev["浏览"] | bev["购买"]

    st.subheader("🎯 推荐结果")

    def jaccard(a,b):
        return len(a & b) / len(a | b) if a | b else 0

    sim_list = []
    for other, x in data["user_data"].items():
        if other == u: continue
        score = jaccard(pref, x["浏览"]|x["购买"])
        if score>0:
            sim_list.append((other, score))

    sim_list = sorted(sim_list, key=lambda x:x[1], reverse=True)[:3]

    if not sim_list:
        st.warning("暂无推荐（可能用户太少）")
    else:
        for other,score in sim_list:
            st.info(f"相似用户：{other}（{score:.2f}）")

            other_pref = data["user_data"][other]["浏览"] | data["user_data"][other]["购买"]
            rec_items = other_pref - pref

            for item in rec_items:
                st.markdown(f"""
                <div style='padding:10px;border:1.5px solid #ccc;border-radius:10px;margin:6px 0'>
                    <b>{item}</b><br>
                    <span style='font-size:13px;color:gray;'>推荐理由：{other} 也喜欢</span>
                </div>
                """, unsafe_allow_html=True)

    st.divider()
    if st.button("继续编辑"):
        st.session_state.step = 2
        st.rerun()
    if st.button("🏠 返回首页"):
        st.session_state.step = 1
        st.rerun()

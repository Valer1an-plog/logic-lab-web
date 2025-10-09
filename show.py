import streamlit as st
import re
from itertools import product

st.set_page_config(page_title="离散数学逻辑实验系统", layout="centered")

# ------------------------------
# 帮助表
# ------------------------------
def show_symbol_help():
    st.markdown("""
### 🧮 逻辑符号输入帮助
| 逻辑符号 | 键盘输入 | 含义 |
|:----------:|:-----------:|:-----------|
| ¬ | `~` 或 `!` | 否定（非） |
| ∧ | `&` 或 `and` | 合取（且） |
| ∨ | `|` 或 `or` | 析取（或） |
| → | `->` 或 `=>` | 蕴含（如果...那么） |
| ↔ | `<->` 或 `<=>` | 等价（当且仅当） |
""", unsafe_allow_html=True)

# ------------------------------
# 符号标准化
# ------------------------------
def standardize_formula(formula: str) -> str:
    """将用户输入转换为统一的数学逻辑符号"""
    if not formula:
        return ""
    s = str(formula).strip()

    # 优先替换长符号
    s = s.replace("<->", "↔").replace("<=>", "↔")
    s = s.replace("->", "→").replace("=>", "→")

    # 替换逻辑符号
    s = re.sub(r'\band\b', '∧', s, flags=re.IGNORECASE)
    s = re.sub(r'\bor\b', '∨', s, flags=re.IGNORECASE)
    s = s.replace("&", "∧").replace("|", "∨")
    s = s.replace("!", "¬").replace("~", "¬")

    return re.sub(r'\s+', '', s)

# ------------------------------
# 真值计算核心
# ------------------------------
def evaluate_formula(formula: str):
    """计算命题公式真值表，支持 ¬ ∧ ∨ → ↔ 括号"""
    vars_list = sorted(set(re.findall(r'[pqrs]', formula)))
    if not vars_list:
        return None, None

    def imply(a, b):
        return (not a) or b

    def equiv(a, b):
        return (a and b) or ((not a) and (not b))

    # 转换逻辑表达式为 Python 可执行形式
    def convert(expr: str):
        expr = expr.replace("¬", " not ")
        expr = expr.replace("∧", " and ")
        expr = expr.replace("∨", " or ")
        # 使用正则替换 → 和 ↔
        while "→" in expr:
            expr = re.sub(r'([^()]+)→([^()]+)', r'imply(\1,\2)', expr)
        while "↔" in expr:
            expr = re.sub(r'([^()]+)↔([^()]+)', r'equiv(\1,\2)', expr)
        return expr

    results = []
    for combo in product([True, False], repeat=len(vars_list)):
        env = dict(zip(vars_list, combo))
        exp = formula
        for k, v in env.items():
            exp = re.sub(r'\b' + re.escape(k) + r'\b', str(v), exp)
        exp = convert(exp)
        try:
            val = eval(exp, {"imply": imply, "equiv": equiv})
        except Exception:
            return None, None
        results.append((env, bool(val)))
    return vars_list, results

# ------------------------------
# 真值表显示
# ------------------------------
def show_truth_table(formula):
    formula_std = standardize_formula(formula)
    st.write(f"解析后的公式：**{formula_std}**")

    vars_list, results = evaluate_formula(formula_std)
    if results is None:
        st.error("⚠️ 输入无效或计算失败，请检查公式格式（仅支持 p,q,r,s 和逻辑符号）。")
        return

    st.write("**真值表：**")
    header = " | ".join(vars_list + [formula_std])
    st.code(header)
    for env, val in results:
        row = " | ".join('T' if env[v] else 'F' for v in vars_list) + " | " + ('T' if val else 'F')
        st.code(row)

    vals = [r[1] for r in results]
    if all(vals):
        st.success("✅ 该公式是重言式（永真式）。")
    elif not any(vals):
        st.error("❌ 该公式是矛盾式（永假式）。")
    else:
        st.info("ℹ️ 该公式是可满足式（部分为真）。")

# ------------------------------
# 等价性判定
# ------------------------------
def show_equivalence_check(formula1, formula2):
    f1s = standardize_formula(formula1)
    f2s = standardize_formula(formula2)
    st.write(f"解析后的公式：**{f1s}** 与 **{f2s}**")

    vars_list = sorted(set(re.findall(r'[pqrs]', f1s + f2s)))
    if not vars_list:
        st.error("⚠️ 未检测到命题变元。")
        return

    _, r1 = evaluate_formula(f1s)
    _, r2 = evaluate_formula(f2s)
    if r1 is None or r2 is None:
        st.error("⚠️ 输入有误，请检查公式格式。")
        return

    st.write("**真值表对比：**")
    header = " | ".join(vars_list + [f1s, f2s])
    st.code(header)

    equal = True
    for i in range(len(r1)):
        env = r1[i][0]
        val1, val2 = r1[i][1], r2[i][1]
        row = " | ".join('T' if env[v] else 'F' for v in vars_list) + f" | {'T' if val1 else 'F'} | {'T' if val2 else 'F'}"
        st.code(row)
        if val1 != val2:
            equal = False
            diff = ", ".join([f"{k}={'T' if env[k] else 'F'}" for k in vars_list])
            st.warning(f"差异赋值：{diff}")

    if equal:
        st.success("✅ 两个公式等价。")
    else:
        st.error("❌ 两个公式不等价。")

# ------------------------------
# 门禁系统
# ------------------------------
def show_access_system():
    st.subheader("题目 3：基于逻辑的门禁系统")
    W = st.radio("是否为工作日(W)：", ["是", "否"])
    T = st.radio("是否为工作时间(T)：", ["是", "否"])
    role = st.radio("人员类型：", ["学生(S)", "教师(E)", "访客(V)"])
    C = st.radio("是否有学生证(C)：", ["是", "否"])
    A = st.radio("是否有教师陪同(A)：", ["是", "否"])

    if st.button("推理结果"):
        W, T, C, A = (W == "是"), (T == "是"), (C == "是"), (A == "是")
        S = role == "学生(S)"
        E = role == "教师(E)"
        V = role == "访客(V)"

        st.write(f"1️⃣ 已知：W={W}, T={T}, S={S}, E={E}, V={V}, C={C}, A={A}")

        if sum([S, E, V]) != 1:
            st.error("⚠️ 人员身份必须唯一。")
            return

        if E:
            st.success("2️⃣ 教师 (E) → 无条件允许进入。")
            st.success("✅ 结论：可以进入实验室。")
            return

        if S:
            if W and T and C:
                st.success("2️⃣ 应用规则1：(W∧T∧S)→(C↔允许)，满足条件，允许进入。")
                st.success("✅ 结论：可以进入实验室。")
            elif W and T and not C:
                st.warning("2️⃣ 应用规则1：未出示学生证，不允许进入。")
                st.error("❌ 结论：不可以进入实验室。")
            elif W and not T:
                st.warning("2️⃣ 应用规则2：W∧¬T∧S→¬允许进入，满足条件。")
                st.error("❌ 结论：不可以进入实验室。")
            else:
                st.warning("2️⃣ 非工作日学生不得进入。")
                st.error("❌ 结论：不可以进入实验室。")
            return

        if V:
            if A:
                st.success("2️⃣ 应用规则4：V→(允许↔A)，有教师陪同，允许进入。")
                st.success("✅ 结论：可以进入实验室。")
            else:
                st.warning("2️⃣ 应用规则4：V→(允许↔A)，无陪同，禁止进入。")
                st.error("❌ 结论：不可以进入实验室。")

# ------------------------------
# 主页面结构
# ------------------------------
st.title("💡 离散数学逻辑实验系统（Final V2）")
show_symbol_help()
st.divider()

option = st.selectbox("请选择题目：", [
    "题目 1：命题逻辑真值表生成器",
    "题目 2：命题公式等价性判定",
    "题目 3：基于逻辑的门禁系统"
])

st.divider()

if option == "题目 1：命题逻辑真值表生成器":
    st.subheader(option)
    formula = st.text_input("请输入命题公式（输入后按 Enter 自动计算）：", placeholder="例如：p↔¬p 或 (p∧q)→r 或 p∨¬p")
    if formula:
        show_truth_table(formula)

elif option == "题目 2：命题公式等价性判定":
    st.subheader(option)
    f1 = st.text_input("请输入第一个公式：", placeholder="例如：p→q")
    f2 = st.text_input("请输入第二个公式：", placeholder="例如：¬p∨q")
    if f1 and f2:
        show_equivalence_check(f1, f2)

elif option == "题目 3：基于逻辑的门禁系统":
    show_access_system()

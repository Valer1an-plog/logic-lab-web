import streamlit as st
import re
from itertools import product

st.set_page_config(page_title="离散数学逻辑实验系统", layout="centered")

# ------------------------------
# 只显示修正后的符号表（去掉多余标题文字）
# ------------------------------
st.markdown("""
<style>
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: center; }
th { background-color: #f9f9f9; }
</style>

<table>
<thead>
<tr>
<th>符号</th><th>键盘输入</th><th>含义</th>
</tr>
</thead>
<tbody>
<tr><td>¬</td><td>~ 或 !</td><td>否定（非）</td></tr>
<tr><td>∧</td><td>&amp; 或 and</td><td>合取（且）</td></tr>
<tr><td>∨</td><td>| 或 or</td><td>析取（或）</td></tr>
<tr><td>→</td><td>-&gt; 或 =&gt;</td><td>蕴含（如果...那么）</td></tr>
<tr><td>↔</td><td>&lt;-&gt; 或 &lt;=&gt;</td><td>等价（当且仅当）</td></tr>
</tbody>
</table>
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

    # 单词替换
    s = re.sub(r'\band\b', '∧', s, flags=re.IGNORECASE)
    s = re.sub(r'\bor\b', '∨', s, flags=re.IGNORECASE)

    # 单字符替换
    s = s.replace("&", "∧").replace("|", "∨")
    s = s.replace("!", "¬").replace("~", "¬")

    # 去掉空格
    return re.sub(r'\s+', '', s)

# ------------------------------
# 真值表计算（支持 ¬ ∧ ∨ → ↔）
# ------------------------------
def evaluate_formula(formula: str):
    """计算命题公式真值表，返回 (vars_list, [(env,val),...]) 或 (None,None)"""
    vars_list = sorted(set(re.findall(r'[pqrs]', formula)))
    if not vars_list:
        return None, None

    def imply(a, b):
        return (not a) or b

    def equiv(a, b):
        return (a and b) or ((not a) and (not b))

    # 将 → ↔ 用函数表示，先替换基础逻辑
    def convert(expr: str) -> str:
        e = expr
        e = e.replace("¬", " not ")
        e = e.replace("∧", " and ")
        e = e.replace("∨", " or ")
        # 尝试把所有的 → 和 ↔ 用函数形式替换（保守替换）
        # 先把所有的 ↔ 和 → 标记为占位，后面用函数名替换
        e = e.replace('↔', ' <=> ')
        e = e.replace('→', ' => ')
        return e

    results = []
    for combo in product([True, False], repeat=len(vars_list)):
        env = dict(zip(vars_list, combo))
        exp = formula
        # 将变量替换为 True/False（按单词边界）
        for k, v in env.items():
            exp = re.sub(r'\b' + re.escape(k) + r'\b', str(v), exp)
        # 基本替换
        exp = convert(exp)
        # 把占位符替换为函数名（带空格以便安全替换）
        exp = exp.replace('<=>', ' equiv ')
        exp = exp.replace('=>', ' imply ')
        try:
            val = eval(exp, {"imply": imply, "equiv": equiv})
        except Exception:
            return None, None
        results.append((env, bool(val)))
    return vars_list, results

# ------------------------------
# 显示真值表
# ------------------------------
def show_truth_table(formula):
    fs = standardize_formula(formula)
    st.write(f"解析后的公式：**{fs}**")
    vars_list, results = evaluate_formula(fs)
    if results is None:
        st.error("⚠️ 输入无效或计算失败，请检查公式格式（仅支持变元 p,q,r,s 和逻辑符号）。")
        return

    st.write("**真值表：**")
    header = " | ".join(vars_list + [fs])
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
def show_equivalence_check(f1, f2):
    f1s = standardize_formula(f1)
    f2s = standardize_formula(f2)
    st.write(f"解析后的公式：**{f1s}**  与  **{f2s}**")
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
# 门禁系统（不变）
# ------------------------------
def show_access_system():
    st.subheader("题目：基于逻辑的门禁系统")
    W = st.radio("是否为工作日 (W)", ["是", "否"])
    T = st.radio("是否为工作时间 (T)", ["是", "否"])
    role = st.radio("人员类型", ["学生(S)", "教师(E)", "访客(V)"])
    C = st.radio("是否有学生证 (C)", ["是", "否"])
    A = st.radio("是否有教师陪同 (A)", ["是", "否"])

    if st.button("推理结果"):
        Wv, Tv, Cv, Av = (W == "是"), (T == "是"), (C == "是"), (A == "是")
        Sv, Ev, Vv = (role == "学生(S)"), (role == "教师(E)"), (role == "访客(V)")

        st.write(f"1. 已知：W={Wv}，T={Tv}，S={Sv}，E={Ev}，V={Vv}，C={Cv}，A={Av}")

        if sum([Sv, Ev, Vv]) != 1:
            st.error("⚠️ 人员身份必须唯一。")
            return
        if Ev:
            st.success("2. 教师 E → 无条件允许进入。结论：可以进入。")
            return
        if Sv:
            if Wv and Tv and Cv:
                st.success("2. 应用规则1：满足 -> 允许进入。")
            elif Wv and Tv and not Cv:
                st.error("2. 应用规则1：未出示学生证 -> 不允许进入。")
            elif Wv and not Tv:
                st.error("2. 应用规则2：工作日非工作时间 -> 不允许进入。")
            else:
                st.error("2. 非工作日学生不得进入。")
            return
        if Vv:
            if Av:
                st.success("2. 应用规则4：有教师陪同 -> 允许进入。")
            else:
                st.error("2. 应用规则4：无教师陪同 -> 不允许进入。")
            return

# ------------------------------
# 主界面：三个题目选择（输入回车自动触发结果）
# ------------------------------
st.title("离散数学逻辑实验系统")

option = st.selectbox("请选择题目：", [
    "题目 1：命题逻辑真值表生成器",
    "题目 2：命题公式等价性判定",
    "题目 3：基于逻辑的门禁系统"
])

st.divider()

if option == "题目 1：命题逻辑真值表生成器":
    st.subheader(option)
    formula = st.text_input("请输入命题公式（输入后按 Enter 自动计算）：", placeholder="例如：p<->!p 或 (p&q)->r 或 p|~p")
    if formula:
        show_truth_table(formula)

elif option == "题目 2：命题公式等价性判定":
    st.subheader(option)
    f1 = st.text_input("请输入第一个公式：", placeholder="例如：p->q")
    f2 = st.text_input("请输入第二个公式：", placeholder="例如：~p|q")
    if f1 and f2:
        show_equivalence_check(f1, f2)

else:
    show_access_system()

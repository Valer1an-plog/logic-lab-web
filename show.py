import re
from itertools import product
import streamlit as st

# ===================== 工具函数 =====================
def normalize_formula(s):
    """将用户输入的逻辑符号标准化"""
    s = s.strip()
    s = s.replace("<->", "↔").replace("<=>", "↔").replace("->", "→").replace("=>", "→")
    s = re.sub(r'\band\b', '∧', s, flags=re.I)
    s = re.sub(r'\bor\b', '∨', s, flags=re.I)
    s = s.replace('&', '∧').replace('|', '∨').replace('v', '∨')
    s = s.replace('!', '¬').replace('~', '¬')
    return re.sub(r'\s+', '', s)

def to_py_expr(formula):
    """将逻辑公式转为 Python 可执行表达式"""
    return (formula
            .replace('¬', ' not ')
            .replace('∧', ' and ')
            .replace('∨', ' or ')
            .replace('→', ' <= ')
            .replace('↔', ' == '))

def evaluate_formula(formula):
    """计算命题公式真值表"""
    vars_list = sorted(set(re.findall(r'[pqrs]', formula)))
    if not vars_list:
        return None, None
    py_expr = to_py_expr(formula)
    results = []
    for combo in product([True, False], repeat=len(vars_list)):
        env = dict(zip(vars_list, combo))
        try:
            val = eval(py_expr, {}, env)
        except Exception:
            return None, None
        results.append((env, val))
    return vars_list, results


# ===================== Streamlit 页面 =====================
st.set_page_config(page_title="离散数学逻辑实验平台", layout="centered")
st.title("🧮 离散数学逻辑实验平台")

# 符号表（HTML版）
st.markdown("""
<style>
table {
    border-collapse: collapse;
    width: 100%;
}
th, td {
    border: 1px solid #ccc;
    padding: 6px 10px;
    text-align: center;
}
th {
    background-color: #f9f9f9;
}
</style>

欢迎使用本系统！请选择要进行的实验题目。  

<table>
<thead>
<tr>
<th>符号</th>
<th>键盘输入</th>
<th>含义</th>
</tr>
</thead>
<tbody>
<tr><td>¬</td><td>~ 或 !</td><td>否定（非）</td></tr>
<tr><td>∧</td><td>& 或 and</td><td>合取（且）</td></tr>
<tr><td>∨</td><td>| 或 or</td><td>析取（或）</td></tr>
<tr><td>→</td><td>-> 或 =></td><td>蕴含（如果...那么）</td></tr>
<tr><td>↔</td><td><-> 或 <=> </td><td>等价（当且仅当）</td></tr>
</tbody>
</table>
""", unsafe_allow_html=True)

# 左侧菜单
option = st.sidebar.radio(
    "📘 选择实验题目：",
    ["题目1：命题逻辑真值表生成器",
     "题目2：命题公式等价性判定",
     "题目4：基于逻辑的门禁系统"]
)

# ===================== 题目 1 =====================
if option == "题目1：命题逻辑真值表生成器":
    st.header("题目1：命题逻辑真值表生成器")
    st.markdown("""
输入命题逻辑公式（含 p、q、r、s 和逻辑符号），程序会自动生成真值表并判断公式类型：  
- 重言式：所有结果为真  
- 矛盾式：所有结果为假  
- 可满足式：部分为真
""")

    user_input = st.text_input("请输入命题逻辑公式：", placeholder="例如：(p&q)->r 或 p|~p")
    if user_input:  # 直接按Enter触发
        formula = normalize_formula(user_input)
        st.write(f"解析后的公式：**{formula}**")
        vars_list, rows = evaluate_formula(formula)
        if not vars_list:
            st.error("⚠️ 输入无效，请检查公式格式。")
        else:
            table = []
            for env, val in rows:
                row = ['T' if env[v] else 'F' for v in vars_list]
                row.append('T' if val else 'F')
                table.append(row)
            st.table([vars_list + [formula]] + table)

            vals = [v for _, v in rows]
            if all(vals):
                st.success("✅ 该公式是 **重言式**（所有组合为真）")
            elif not any(vals):
                st.error("❌ 该公式是 **矛盾式**（所有组合为假）")
            else:
                st.info("ℹ️ 该公式是 **可满足式**（但不是重言式）")


# ===================== 题目 2 =====================
elif option == "题目2：命题公式等价性判定":
    st.header("题目2：命题公式等价性判定")
    st.markdown("""
输入两个命题逻辑公式，系统会自动生成真值表并判定是否等价。
""")

    f1 = st.text_input("第一个公式：", placeholder="如：p->q")
    f2 = st.text_input("第二个公式：", placeholder="如：~p∨q")

    if f1 and f2:  # 按 Enter 触发
        f1m, f2m = normalize_formula(f1), normalize_formula(f2)
        all_vars = sorted(set(re.findall(r'[pqrs]', f1m + f2m)))
        py1, py2 = to_py_expr(f1m), to_py_expr(f2m)
        diffs, results = [], []

        for combo in product([True, False], repeat=len(all_vars)):
            env = dict(zip(all_vars, combo))
            try:
                v1, v2 = eval(py1, {}, env), eval(py2, {}, env)
            except Exception:
                st.error("⚠️ 输入错误，请检查公式。")
                st.stop()
            results.append((env, v1, v2))
            if v1 != v2:
                diffs.append(env)

        header = all_vars + [f1m, f2m]
        table = []
        for env, v1, v2 in results:
            row = ['T' if env[v] else 'F' for v in all_vars] + ['T' if v1 else 'F', 'T' if v2 else 'F']
            table.append(row)
        st.table([header] + table)

        if not diffs:
            st.success("✅ 两个公式 **等价**")
        else:
            st.error("❌ 两个公式 **不等价**")
            st.write("差异赋值如下：")
            for d in diffs:
                st.write({k: ('真' if v else '假') for k, v in d.items()})


# ===================== 题目 4 =====================
elif option == "题目4：基于逻辑的门禁系统":
    st.header("题目4：基于逻辑的门禁系统")
    st.markdown("""
根据输入条件判断是否允许进入实验室，并展示逻辑推理过程。  
规则如下：  
1. 若为工作日且在工作时间，学生需出示学生证才能进入；  
2. 若为工作日但不在工作时间，学生即使有学生证也不能进入；  
3. 教师任何时间均可进入；  
4. 访客必须有教师陪同才能进入。
""")

    W = st.selectbox("是否工作日 (W)", ["请选择", "是", "否"])
    T = st.selectbox("是否工作时间 (T)", ["请选择", "是", "否"])
    identity = st.selectbox("人员类型", ["请选择", "学生", "教师", "访客"])
    C = st.selectbox("是否有学生证 (C)", ["请选择", "是", "否"])
    A = st.selectbox("是否有教师陪同 (A)", ["请选择", "是", "否"])

    if all(x != "请选择" for x in [W, T, identity, C, A]):
        Wv, Tv = (W == "是"), (T == "是")
        Cv, Av = (C == "是"), (A == "是")
        Sv, Ev, Vv = (identity == "学生"), (identity == "教师"), (identity == "访客")

        st.write(f"1️⃣ 已知条件：W={Wv}，T={Tv}，S={Sv}，E={Ev}，V={Vv}，C={Cv}，A={Av}")

        allowed, reason = False, ""
        if Ev:
            allowed = True
            reason = "应用规则3：教师任何时间可进入。"
        elif Sv:
            if Wv and Tv:
                if Cv:
                    allowed = True
                    reason = "应用规则1：(W∧T∧S)→C，条件满足，允许进入。"
                else:
                    allowed = False
                    reason = "应用规则1：(W∧T∧S)→C，但未出示学生证，禁止进入。"
            elif Wv and not Tv:
                allowed = False
                reason = "应用规则2：W∧¬T∧S→¬允许进入，满足条件。"
            else:
                allowed = False
                reason = "学生仅在工作日工作时间内可进入。"
        elif Vv:
            if Av:
                allowed = True
                reason = "应用规则4：V→(允许↔A)，有教师陪同，允许进入。"
            else:
                allowed = False
                reason = "应用规则4：V→(允许↔A)，无教师陪同，禁止进入。"
        else:
            reason = "输入身份无效。"

        st.write(f"2️⃣ 推理过程：{reason}")
        if allowed:
            st.success("✅ 结论：可以进入实验室。")
        else:
            st.error("❌ 结论：不可以进入实验室。")

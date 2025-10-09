import streamlit as st
import re
from itertools import product

st.set_page_config(page_title="离散数学实验系统", layout="centered")

# ------------------------------
# 逻辑符号与帮助信息
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
# 通用逻辑公式解析与求值（修正：先替换长符号）
# ------------------------------
def standardize_formula(formula: str) -> str:
    """将用户输入转换为统一的数学逻辑符号，先替换多字符运算符以避免冲突"""
    if formula is None:
        return ""
    s = str(formula)

    # 去除两端空白但保留中间空格以便 regex 匹配单词边界（后面会去掉所有空格）
    s = s.strip()

    # 先替换**多字符**运算符（非常重要：先做长的）
    s = s.replace("<->", "↔").replace("<=>", "↔")
    s = s.replace("->", "→").replace("=>", "→")

    # 然后处理单词形式（and/or）用正则按单词边界替换
    s = re.sub(r'\band\b', '∧', s, flags=re.IGNORECASE)
    s = re.sub(r'\bor\b', '∨', s, flags=re.IGNORECASE)

    # 单字符替换（符号）
    s = s.replace("&", "∧")
    s = s.replace("|", "∨")
    # 小写字母 v 也可能被当作或（但谨慎替换：只替换孤立的 v）
    s = re.sub(r'\b[vV]\b', '∨', s)

    s = s.replace("!", "¬").replace("~", "¬")

    # 去掉所有空格（标准化输出时不需要空格）
    s = re.sub(r'\s+', '', s)

    return s

def to_py_expr(formula: str) -> str:
    """将数学符号公式转换为 Python 可执行表达式的中间形式
       其中把 → 替为占位 '=>'，↔ 替为 '<=>'，后面 evaluate 时替换为函数调用"""
    f = formula
    f = f.replace('¬', ' not ')
    f = f.replace('∧', ' and ')
    f = f.replace('∨', ' or ')
    # 使用占位符（避免直接 eval 导致语义混淆）
    f = f.replace('→', ' => ')
    f = f.replace('↔', ' <=> ')
    return f

def evaluate_formula(formula: str):
    """计算命题公式的真值表，返回 (vars_list, [(env, val), ...])；
       若解析或计算失败则返回 (None, None)"""
    vars_list = sorted(set(re.findall(r'[pqrs]', formula)))
    if not vars_list:
        return None, None

    expr = to_py_expr(formula)

    # 自定义逻辑函数
    def imply(a, b):
        return (not a) or b

    def equiv(a, b):
        return (a and b) or ((not a) and (not b))

    results = []
    for combo in product([True, False], repeat=len(vars_list)):
        env = dict(zip(vars_list, combo))
        exp = expr
        try:
            # 将变量名替换为 True/False 字符串（按单词边界）
            for k, v in env.items():
                exp = re.sub(r'\b' + re.escape(k) + r'\b', str(v), exp)
            # 把占位符替换为函数名（带空格以保证替换安全）
            exp = exp.replace('<=>', ' equiv ')
            exp = exp.replace('=>', ' imply ')
            # eval 时提供函数定义
            val = eval(exp, {"imply": imply, "equiv": equiv})
        except Exception:
            return None, None
        results.append((env, bool(val)))
    return vars_list, results

# ------------------------------
# 显示/交互函数（与之前相同）
# ------------------------------
def show_truth_table(formula):
    formula_std = standardize_formula(formula)
    st.write(f"解析后的公式：**{formula_std}**")

    vars_list, results = evaluate_formula(formula_std)
    if results is None:
        st.error("⚠️ 输入无效或解析/计算失败，请检查公式格式（只支持变元 p,q,r,s 和逻辑符号）。")
        return

    st.write("**真值表（变量顺序按字母）**")
    header = " | ".join(vars_list + [formula_std])
    st.code(header)
    for env, val in results:
        row = " | ".join('T' if env[v] else 'F' for v in vars_list) + " | " + ('T' if val else 'F')
        st.code(row)

    vals = [r[1] for r in results]
    if all(vals):
        st.success("✅ 该公式是重言式（在所有赋值下为真）。")
    elif not any(vals):
        st.error("❌ 该公式是矛盾式（在所有赋值下为假）。")
    else:
        st.info("ℹ️ 该公式是可满足式（至少存在一个赋值为真）。")

def show_equivalence_check(formula1, formula2):
    f1s = standardize_formula(formula1)
    f2s = standardize_formula(formula2)
    st.write(f"解析后的公式：**{f1s}**  与  **{f2s}**")

    vars_list = sorted(set(re.findall(r'[pqrs]', f1s + f2s)))
    if not vars_list:
        st.error("⚠️ 未检测到命题变元（p,q,r,s）。")
        return

    v1, r1 = evaluate_formula(f1s)
    v2, r2 = evaluate_formula(f2s)
    if r1 is None or r2 is None:
        st.error("⚠️ 公式解析或计算失败，请检查输入。")
        return

    st.write("**真值表对比（变量按字母顺序）：**")
    header = " | ".join(vars_list + [f1s, f2s])
    st.code(header)

    equal = True
    for i in range(len(r1)):
        env = r1[i][0]
        val1 = r1[i][1]
        # find corresponding row in r2 by same env order (evaluate_formula uses same var order)
        val2 = r2[i][1]
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

def show_access_system():
    st.subheader("题目 3：基于逻辑的门禁系统")
    W = st.selectbox("是否为工作日 (W)", ["请选择", "是", "否"])
    T = st.selectbox("是否为工作时间 (T)", ["请选择", "是", "否"])
    role = st.selectbox("人员类型", ["请选择", "学生(S)", "教师(E)", "访客(V)"])
    C = st.selectbox("是否有学生证 (C)", ["请选择", "是", "否"])
    A = st.selectbox("是否有教师陪同 (A)", ["请选择", "是", "否"])

    if all(x != "请选择" for x in [W, T, role, C, A]):
        Wv, Tv, Cv, Av = (W == "是"), (T == "是"), (C == "是"), (A == "是")
        Sv, Ev, Vv = (role == "学生(S)"), (role == "教师(E)"), (role == "访客(V)")
        st.write(f"1. 已知：W={Wv}，T={Tv}，S={Sv}，E={Ev}，V={Vv}，C={Cv}，A={Av}")

        # 确保身份唯一
        if sum([Sv, Ev, Vv]) != 1:
            st.error("⚠️ 人员身份必须唯一（学生 / 教师 / 访客 三选一）。")
            return

        if Ev:
            st.success("2. 应用规则3：教师 E → 允许。结论：可以进入。")
            return
        if Sv:
            if Wv and Tv:
                if Cv:
                    st.success("2. 应用规则1：(W∧T∧S)→(允许↔C)，满足 -> 允许进入。")
                else:
                    st.error("2. 应用规则1：满足前件但未出示学生证 -> 不允许进入。")
                return
            if Wv and not Tv:
                st.error("2. 应用规则2：W∧¬T∧S -> 不允许进入。")
                return
            st.error("2. 非工作日学生不得进入（按规则）。")
            return
        if Vv:
            if Av:
                st.success("2. 应用规则4：V→(允许↔A)，有陪同 -> 允许进入。")
            else:
                st.error("2. 应用规则4：无陪同 -> 不允许进入。")
            return

# ------------------------------
# 页面主结构
# ------------------------------
st.title("💡 离散数学逻辑实验系统（修复 ↔ 与 -> 替换顺序问题）")
show_symbol_help()

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
    f1 = st.text_input("请输入第一个公式（输入后按 Enter 自动计算）：", placeholder="例如：p->q")
    f2 = st.text_input("请输入第二个公式（输入后按 Enter 自动计算）：", placeholder="例如：~p|q")
    if f1 and f2:
        show_equivalence_check(f1, f2)

elif option == "题目 3：基于逻辑的门禁系统":
    show_access_system()

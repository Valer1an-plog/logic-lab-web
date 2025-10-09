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
""")

# ------------------------------
# 通用逻辑公式解析与求值
# ------------------------------
def standardize_formula(formula):
    """标准化输入公式符号"""
    formula = formula.replace(" ", "")
    formula = formula.replace("->", "→")
    formula = formula.replace("=>", "→")
    formula = formula.replace("<->", "↔")
    formula = formula.replace("<=>", "↔")
    formula = formula.replace("&", "∧")
    formula = formula.replace("and", "∧")
    formula = formula.replace("|", "∨")
    formula = formula.replace("or", "∨")
    formula = formula.replace("!", "¬")
    formula = formula.replace("~", "¬")
    return formula

def to_py_expr(formula):
    """将逻辑公式转为 Python 表达式"""
    f = formula
    f = f.replace('¬', ' not ')
    f = f.replace('∧', ' and ')
    f = f.replace('∨', ' or ')
    f = f.replace('→', ' => ')
    f = f.replace('↔', ' <=> ')
    return f

def evaluate_formula(formula):
    """计算命题公式的真值表"""
    vars_list = sorted(set(re.findall(r'[pqrs]', formula)))
    if not vars_list:
        return None, None

    expr = to_py_expr(formula)

    def imply(a, b):  # 蕴含
        return (not a) or b

    def equiv(a, b):  # 等价
        return (a and b) or ((not a) and (not b))

    results = []
    for combo in product([True, False], repeat=len(vars_list)):
        env = dict(zip(vars_list, combo))
        exp = expr
        try:
            # 替换变量为 True/False
            for k, v in env.items():
                exp = re.sub(r'\b' + k + r'\b', str(v), exp)
            # 处理等价和蕴含
            exp = exp.replace('<=>', ' equiv ')
            exp = exp.replace('=>', ' imply ')
            val = eval(exp, {"imply": imply, "equiv": equiv})
        except Exception:
            return None, None
        results.append((env, val))
    return vars_list, results


def show_truth_table(formula):
    formula = standardize_formula(formula)
    st.write(f"解析后的公式：**{formula}**")

    vars_list, results = evaluate_formula(formula)
    if results is None:
        st.error("⚠️ 输入无效，请检查公式格式。")
        return

    # 构建真值表
    header = " | ".join(vars_list + [formula])
    st.write("**真值表：**")
    st.code(header)
    for env, val in results:
        row = " | ".join('T' if env[v] else 'F' for v in vars_list) + " | " + ('T' if val else 'F')
        st.code(row)

    # 判定公式类型
    vals = [r[1] for r in results]
    if all(vals):
        st.success("✅ 该公式是 **重言式（永真式）**。")
    elif not any(vals):
        st.error("❌ 该公式是 **矛盾式（永假式）**。")
    else:
        st.info("ℹ️ 该公式是 **可满足式（部分为真）**。")


# ------------------------------
# 等价性判定
# ------------------------------
def show_equivalence_check(formula1, formula2):
    f1, f2 = standardize_formula(formula1), standardize_formula(formula2)
    st.write(f"解析后的公式：{f1}   和   {f2}")

    vars_list = sorted(set(re.findall(r'[pqrs]', f1 + f2)))
    if not vars_list:
        st.error("⚠️ 未找到命题变元。")
        return

    v1, r1 = evaluate_formula(f1)
    v2, r2 = evaluate_formula(f2)

    if not r1 or not r2:
        st.error("⚠️ 输入有误，请检查格式。")
        return

    st.write("**真值表对比：**")
    header = " | ".join(vars_list + [f1, f2])
    st.code(header)

    same = True
    for i in range(len(r1)):
        env = r1[i][0]
        val1, val2 = r1[i][1], r2[i][1]
        row = " | ".join('T' if env[v] else 'F' for v in vars_list) + f" | {'T' if val1 else 'F'} | {'T' if val2 else 'F'}"
        st.code(row)
        if val1 != val2:
            same = False
            diff = ", ".join([f"{v}={'T' if env[v] else 'F'}" for v in vars_list])
            st.warning(f"差异赋值：{diff}")

    if same:
        st.success("✅ 两个公式等价。")
    else:
        st.error("❌ 两个公式不等价。")


# ------------------------------
# 门禁系统逻辑推理
# ------------------------------
def show_access_system():
    st.subheader("题目 3：基于逻辑的门禁系统")

    W = st.radio("是否工作日(W)：", ["是", "否"])
    T = st.radio("是否工作时间(T)：", ["是", "否"])
    role = st.radio("人员类型：", ["学生(S)", "教师(E)", "访客(V)"])
    C = st.radio("是否有学生证(C)：", ["是", "否"])
    A = st.radio("是否有教师陪同(A)：", ["是", "否"])

    if st.button("推理结果"):
        W, T, C, A = (W == "是"), (T == "是"), (C == "是"), (A == "是")
        S = role == "学生(S)"
        E = role == "教师(E)"
        V = role == "访客(V)"

        st.write(f"1️⃣ 已知条件：W={W}, T={T}, S={S}, E={E}, V={V}, C={C}, A={A}")

        if sum([S, E, V]) != 1:
            st.error("⚠️ 输入非法：人员身份必须唯一。")
            return

        if E:
            st.success("2️⃣ 应用规则3：E→允许，教师无条件允许进入。")
            st.success("✅ 结论：可以进入实验室。")
            return

        if S:
            if W and T:
                if C:
                    st.success("2️⃣ 应用规则1：(W∧T∧S)→(C↔允许)，满足条件，允许进入。")
                    st.success("✅ 结论：可以进入实验室。")
                else:
                    st.warning("2️⃣ 应用规则1：未出示学生证，不允许进入。")
                    st.error("❌ 结论：不可以进入实验室。")
            elif W and not T:
                st.warning("2️⃣ 应用规则2：W∧¬T∧S→¬允许进入。")
                st.error("❌ 结论：不可以进入实验室。")
            else:
                st.warning("2️⃣ 非工作日学生不得进入。")
                st.error("❌ 结论：不可以进入实验室。")
            return

        if V:
            if A:
                st.success("2️⃣ 应用规则4：V→(允许↔A)，满足条件，有陪同可进入。")
                st.success("✅ 结论：可以进入实验室。")
            else:
                st.warning("2️⃣ 应用规则4：V→(允许↔A)，无陪同禁止进入。")
                st.error("❌ 结论：不可以进入实验室。")
            return


# ------------------------------
# 页面结构
# ------------------------------
st.title("💡 离散数学逻辑实验系统")
show_symbol_help()

option = st.selectbox("请选择题目：", [
    "题目 1：命题逻辑真值表生成器",
    "题目 2：命题公式等价性判定",
    "题目 3：基于逻辑的门禁系统"
])

st.divider()

if option == "题目 1：命题逻辑真值表生成器":
    st.subheader(option)
    formula = st.text_input("请输入命题公式：", placeholder="例如：(p∧q)→r 或 p∨¬p")
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

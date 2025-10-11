import re
import streamlit as st
from itertools import product

# ========== 符号处理与逻辑计算 ==========
def normalize_formula(s):
    s = s.strip()
    s = s.replace("<->", "↔").replace("<=>", "↔").replace("->", "→").replace("=>", "→")
    s = re.sub(r'\band\b', '∧', s, flags=re.I)
    s = re.sub(r'\bor\b', '∨', s, flags=re.I)
    s = s.replace('&', '∧').replace('|', '∨').replace('v', '∨')
    s = s.replace('!', '¬').replace('~', '¬')
    return re.sub(r'\s+', '', s)

def to_py_expr(formula):
    return (formula
            .replace('¬', ' not ')
            .replace('∧', ' and ')
            .replace('∨', ' or ')
            .replace('→', ' <= ')
            .replace('↔', ' == '))

def evaluate_formula(formula):
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

# ========== Streamlit 界面 ==========
st.set_page_config(page_title="逻辑实验系统", layout="centered")
st.title("🧮 离散数学逻辑实验系统")
st.write("请选择要进行的实验题目：")

option = st.radio(
    "选择实验题目：",
    ["题目1：命题逻辑真值表生成器", "题目2：命题公式等价性判定"]
)

if option == "题目1：命题逻辑真值表生成器":
    st.subheader("输入逻辑公式（例如：(p∧q)→r 或 p|~p）")
    user_input = st.text_input("公式输入", "")
    if st.button("生成真值表"):
        formula = normalize_formula(user_input)
        st.write(f"解析后的公式：**{formula}**")
        vars_list, rows = evaluate_formula(formula)
        if not vars_list:
            st.error("输入无效，请检查公式。")
        else:
            # 真值表
            table = []
            for env, val in rows:
                row = [ 'T' if env[v] else 'F' for v in vars_list ]
                row.append('T' if val else 'F')
                table.append(row)
            st.table([vars_list + [formula]] + table)

            vals = [v for _, v in rows]
            if all(vals):
                st.success("该公式是 **重言式**（所有组合为真） ✅")
            elif not any(vals):
                st.error("该公式是 **矛盾式**（所有组合为假） ❌")
            else:
                st.info("该公式是 **可满足式**（但不是重言式）")

elif option == "题目2：命题公式等价性判定":
    st.subheader("输入两个逻辑公式进行等价性判定")
    f1 = st.text_input("第一个公式", "")
    f2 = st.text_input("第二个公式", "")
    if st.button("判定等价性"):
        f1m = normalize_formula(f1)
        f2m = normalize_formula(f2)
        all_vars = sorted(set(re.findall(r'[pqrs]', f1m + f2m)))
        py1, py2 = to_py_expr(f1m), to_py_expr(f2m)
        diffs = []
        results = []
        for combo in product([True, False], repeat=len(all_vars)):
            env = dict(zip(all_vars, combo))
            try:
                v1, v2 = eval(py1, {}, env), eval(py2, {}, env)
            except Exception:
                st.error("输入错误，请检查公式")
                st.stop()
            results.append((env, v1, v2))
            if v1 != v2:
                diffs.append(env)
        # 表格显示
        header = all_vars + [f1m, f2m]
        table = []
        for env, v1, v2 in results:
            row = [ 'T' if env[v] else 'F' for v in all_vars ] + [ 'T' if v1 else 'F', 'T' if v2 else 'F' ]
            table.append(row)
        st.table([header] + table)
        if not diffs:
            st.success("两个公式 **等价** ✅")
        else:
            st.error("两个公式 **不等价** ❌")
            st.write("差异赋值：")
            for d in diffs:
                st.write({k: ('真' if v else '假') for k,v in d.items()})

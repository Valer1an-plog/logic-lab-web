def evaluate_formula(formula: str):
    """计算命题公式真值表（支持 ↔、→、¬、∧、∨、括号）"""
    vars_list = sorted(set(re.findall(r'[pqrs]', formula)))
    if not vars_list:
        return None, None

    def imply(a, b):
        return (not a) or b

    def equiv(a, b):
        return (a and b) or ((not a) and (not b))

    # 将公式转为 Python 表达式
    def convert(expr: str):
        expr = expr.replace("¬", " not ")
        expr = expr.replace("∧", " and ")
        expr = expr.replace("∨", " or ")
        # 处理蕴含和等价：使用正则递归替换，保证括号安全
        while "→" in expr:
            expr = re.sub(r"([A-Za-z\)\s]+)→([A-Za-z\(\snotandor]+)", r"imply(\1,\2)", expr)
        while "↔" in expr:
            expr = re.sub(r"([A-Za-z\)\s]+)↔([A-Za-z\(\snotandor]+)", r"equiv(\1,\2)", expr)
        return expr

    results = []
    for combo in product([True, False], repeat=len(vars_list)):
        env = dict(zip(vars_list, combo))
        exp = formula
        # 替换变量为 True/False
        for k, v in env.items():
            exp = re.sub(r'\b' + re.escape(k) + r'\b', str(v), exp)
        exp = convert(exp)
        try:
            val = eval(exp, {"imply": imply, "equiv": equiv})
        except Exception:
            return None, None
        results.append((env, bool(val)))
    return vars_list, results


def show_truth_table(formula):
    formula_std = standardize_formula(formula)
    st.write(f"解析后的公式：**{formula_std}**")

    vars_list, results = evaluate_formula(formula_std)
    if results is None:
        st.error("⚠️ 输入无效或解析/计算失败，请检查公式格式（支持 p,q,r,s, ¬, ∧, ∨, →, ↔）。")
        return

    # 输出真值表
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
        st.info("ℹ️ 该公式是可满足式（部分真部分假）。")

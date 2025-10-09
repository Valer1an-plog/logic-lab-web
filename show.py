import streamlit as st
import re
from itertools import product

st.set_page_config(page_title="离散数学逻辑实验系统", layout="centered")

# ------------------------------------
# 逻辑符号对照表（HTML展示）
# ------------------------------------
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


# =========================
# 题目1 —— 高精度逻辑公式解析器
# =========================

class Node:
    def evaluate(self, env): raise NotImplementedError
    def vars(self): raise NotImplementedError

class Var(Node):
    def __init__(self, name): self.name = name
    def evaluate(self, env): return env[self.name]
    def vars(self): return {self.name}

class Not(Node):
    def __init__(self, c): self.c = c
    def evaluate(self, env): return not self.c.evaluate(env)
    def vars(self): return self.c.vars()

class And(Node):
    def __init__(self, a,b): self.a=a; self.b=b
    def evaluate(self, env): return self.a.evaluate(env) and self.b.evaluate(env)
    def vars(self): return self.a.vars() | self.b.vars()

class Or(Node):
    def __init__(self, a,b): self.a=a; self.b=b
    def evaluate(self, env): return self.a.evaluate(env) or self.b.evaluate(env)
    def vars(self): return self.a.vars() | self.b.vars()

class Impl(Node):
    def __init__(self,a,b): self.a=a; self.b=b
    def evaluate(self, env): return (not self.a.evaluate(env)) or self.b.evaluate(env)
    def vars(self): return self.a.vars() | self.b.vars()

class Equiv(Node):
    def __init__(self,a,b): self.a=a; self.b=b
    def evaluate(self, env): return self.a.evaluate(env) == self.b.evaluate(env)
    def vars(self): return self.a.vars() | self.b.vars()


# ---- 词法分析
_token_spec = [
    ('EQUIV', r'(<->|<=>|↔)'),
    ('IMPL',  r'(->|=>|→)'),
    ('NOT',   r'(¬|~|!)'),
    ('AND',   r'(∧|&|\\band\\b)'),
    ('OR',    r'(∨|\\||\\bor\\b|\\bv\\b)'),
    ('LP',    r'[\\(\\[\\{]'),
    ('RP',    r'[\\)\\]\\}]'),
    ('VAR',   r'[pqrsPQRS]'),
    ('SPACE', r'\\s+'),
    ('OTHER', r'.'),
]
_token_re = re.compile('|'.join(f'(?P<{n}>{p})' for n,p in _token_spec), re.I)
_PRE = {'NOT':5,'AND':4,'OR':3,'IMPL':2,'EQUIV':1}
_ASSOC = {'NOT':'RIGHT','AND':'LEFT','OR':'LEFT','IMPL':'RIGHT','EQUIV':'RIGHT'}

def tokenize(s):
    tokens = []
    i=0
    while i<len(s):
        m=_token_re.match(s,i)
        if not m: raise ValueError
        typ=m.lastgroup; txt=m.group(typ)
        i=m.end()
        if typ=='SPACE': continue
        if typ=='OTHER': raise ValueError
        if typ=='VAR': tokens.append(('VAR',txt.lower()))
        else: tokens.append((typ,txt))
    return tokens

def shunting_yard(tokens):
    out, ops = [], []
    for typ,txt in tokens:
        if typ=='VAR': out.append(('VAR',txt))
        elif typ in _PRE:
            while ops:
                top=ops[-1]
                if top=='LP': break
                if ((_ASSOC[typ]=='LEFT' and _PRE[typ]<=_PRE[top]) or
                    (_ASSOC[typ]=='RIGHT' and _PRE[typ]<_PRE[top])):
                    out.append((ops.pop(),None))
                else: break
            ops.append(typ)
        elif typ=='LP': ops.append('LP')
        elif typ=='RP':
            while ops and ops[-1]!='LP': out.append((ops.pop(),None))
            if not ops: raise ValueError
            ops.pop()
        else: raise ValueError
    while ops:
        t=ops.pop()
        if t=='LP': raise ValueError
        out.append((t,None))
    return out

def rpn_to_ast(rpn):
    st=[]
    for typ,val in rpn:
        if typ=='VAR': st.append(Var(val))
        elif typ=='NOT':
            if not st: raise ValueError
            st.append(Not(st.pop()))
        elif typ in ('AND','OR','IMPL','EQUIV'):
            if len(st)<2: raise ValueError
            b=st.pop(); a=st.pop()
            if typ=='AND': st.append(And(a,b))
            elif typ=='OR': st.append(Or(a,b))
            elif typ=='IMPL': st.append(Impl(a,b))
            elif typ=='EQUIV': st.append(Equiv(a,b))
    if len(st)!=1: raise ValueError
    return st[0]

def normalize_display(s):
    s=s.replace('<->','↔').replace('<=>','↔')
    s=s.replace('->','→').replace('=>','→')
    s=re.sub(r'\\band\\b','∧',s,flags=re.I)
    s=re.sub(r'\\bor\\b','∨',s,flags=re.I)
    return s.replace('&','∧').replace('|','∨').replace('!','¬').replace('~','¬').replace(' ','').strip()


def show_truth_table(formula):
    try:
        toks=tokenize(formula)
        rpn=shunting_yard(toks)
        ast=rpn_to_ast(rpn)
    except Exception:
        st.error("⚠️ 输入无效，请检查公式格式。")
        return

    fs=normalize_display(formula)
    vars_present=sorted(ast.vars(), key=lambda x: "pqrs".index(x))
    st.write(f"解析后的公式：**{fs}**")
    st.write("**真值表：**")
    header=" | ".join(vars_present+[fs])
    st.code(header)

    results=[]
    for combo in product([True,False], repeat=len(vars_present)):
        env=dict(zip(vars_present,combo))
        val=ast.evaluate(env)
        results.append(val)
        row=" | ".join('T' if env[v] else 'F' for v in vars_present)+" | "+('T' if val else 'F')
        st.code(row)

    if all(results):
        st.success("✅ 该公式是重言式（永真式）")
    elif not any(results):
        st.error("❌ 该公式是矛盾式（永假式）")
    else:
        st.info("ℹ️ 该公式是可满足式（但不是重言式）")


# =========================
# 题目2 —— 等价性判定
# =========================
def show_equivalence_check(f1,f2):
    try:
        a1=rpn_to_ast(shunting_yard(tokenize(f1)))
        a2=rpn_to_ast(shunting_yard(tokenize(f2)))
    except Exception:
        st.error("⚠️ 输入有误，请检查公式。")
        return

    v=sorted(set(a1.vars()|a2.vars()), key=lambda x:"pqrs".index(x))
    st.write(f"解析后的公式：**{normalize_display(f1)}** 与 **{normalize_display(f2)}**")
    st.write("**真值表对比：**")
    header=" | ".join(v+[normalize_display(f1),normalize_display(f2)])
    st.code(header)
    eq=True
    for c in product([True,False],repeat=len(v)):
        env=dict(zip(v,c))
        v1=a1.evaluate(env); v2=a2.evaluate(env)
        row=" | ".join('T' if env[x] else 'F' for x in v)+f" | {'T' if v1 else 'F'} | {'T' if v2 else 'F'}"
        st.code(row)
        if v1!=v2: eq=False
    if eq:
        st.success("✅ 两个公式等价。")
    else:
        st.error("❌ 两个公式不等价。")


# =========================
# 题目3 —— 门禁系统
# =========================
def show_access_system():
    st.subheader("题目 3：基于逻辑的门禁系统")
    W=st.radio("是否为工作日(W)",["是","否"])
    T=st.radio("是否为工作时间(T)",["是","否"])
    role=st.radio("人员类型",["学生(S)","教师(E)","访客(V)"])
    C=st.radio("是否有学生证(C)",["是","否"])
    A=st.radio("是否有教师陪同(A)",["是","否"])
    if st.button("推理结果"):
        Wv,Tv,Cv,Av=(W=="是"),(T=="是"),(C=="是"),(A=="是")
        Sv,Ev,Vv=(role=="学生(S)"),(role=="教师(E)"),(role=="访客(V)")
        st.write(f"1. 已知：W={Wv}，T={Tv}，S={Sv}，E={Ev}，V={Vv}，C={Cv}，A={Av}")
        if Ev:
            st.success("2. 教师 E→允许进入。结论：可以进入实验室。")
        elif Sv:
            if Wv and Tv and Cv:
                st.success("2. 应用规则1：(W∧T∧S)→C，满足条件。结论：允许进入。")
            elif Wv and not Tv:
                st.error("2. 应用规则2：W∧¬T∧S→¬允许进入。结论：不允许进入。")
            elif not Wv:
                st.error("2. 非工作日学生禁止进入。")
            else:
                st.error("2. 未出示学生证，禁止进入。")
        elif Vv:
            if Av:
                st.success("2. 应用规则4：V→(允许↔A)。满足条件，可进入。")
            else:
                st.error("2. 无教师陪同，不允许进入。")


# =========================
# 主界面导航
# =========================
st.title("离散数学逻辑实验系统")

option = st.selectbox("请选择题目：", [
    "题目 1：命题逻辑真值表生成器",
    "题目 2：命题公式等价性判定",
    "题目 3：基于逻辑的门禁系统"
])

st.divider()

if option=="题目 1：命题逻辑真值表生成器":
    st.subheader(option)
    f=st.text_input("请输入命题公式（输入后按 Enter 自动计算）：", placeholder="例如：p<->!p 或 (p&q)->r 或 p|~p")
    if f: show_truth_table(f)
elif option=="题目 2：命题公式等价性判定":
    st.subheader(option)
    f1=st.text_input("请输入第一个公式：")
    f2=st.text_input("请输入第二个公式：")
    if f1 and f2: show_equivalence_check(f1,f2)
else:
    show_access_system()

import streamlit as st
import re
import os
from google import genai
from google.genai.errors import APIError
import json

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="Oct Validator", page_icon="🐙", layout="centered")

# 👇 مفتاح الـ API
API_KEY = "AIzaSyAY6iisYKpbpNCJkkakh4E-u01g0_RRd_I"

if API_KEY and API_KEY != "AIzaSyAY6iisYKpbpNCJkkakh4E-u01g0_RRd_I":
    os.environ["GEMINI_API_KEY"] = API_KEY

# ==========================================
# 2. CSS STYLING
# ==========================================
st.markdown("""
<style>
    header, footer {visibility: hidden !important;}
    .stApp {background: #EEEEEE;}
    div[data-testid="stForm"] { background-color: #FFFBF7; border-radius: 20px; box-shadow: 0 10px 25px rgba(230, 81, 0, 0.08); border: 3px solid #FFA500; padding: 2rem; }
    div[data-testid="stForm"] h1, label, p, h3 { color: #333 !important; }
    
    .main-header {
        display: flex; align-items: center; justify-content: center;
        gap: 15px; margin-bottom: 30px;
    }
    .main-title {
        font-family: 'Helvetica Neue', sans-serif; font-weight: 900;
        font-size: 3rem; color: #E65100; margin: 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .octo-logo {
        font-size: 60px; 
        filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.2));
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }

    .stTextInput input, .stTextArea textarea { background-color: #FFFFFF !important; border: 1px solid #FFCC80 !important; border-radius: 10px !important; color: #000000 !important; font-size: 16px !important; }
    .stTextInput input:focus, .stTextArea textarea:focus { border-color: #EF6C00 !important; box-shadow: 0 0 0 1px #EF6C00 !important; }
    
    /* 6. الأزرار (تعديل إجباري) */
    
    /* استهداف الزر الأساسي (Validate) */
    div[data-testid="stForm"] button[kind="primary"],
    div[data-testid="stForm"] button[data-testid="baseButton-primary"] {
        background: #FFA500 !important;        /* اللون للنسخ القديمة */
        background-color: #FFA500 !important;  /* اللون للنسخ الحديثة */
        background-image: none !important;     /* إلغاء أي تدرج لوني */
        border: 1px solid #FFA500 !important;  /* حدود بنفس اللون */
        color: White !important;               /* نص أبيض */
        font-weight: 800 !important;
        border-radius: 10px !important;
        padding: 0.6rem 2rem !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }

    /* تأثير الماوس (Hover) */
    div[data-testid="stForm"] button[kind="primary"]:hover,
    div[data-testid="stForm"] button[data-testid="baseButton-primary"]:hover {
        background-color: #E69500 !important;  /* لون أغمق سنة */
        background-image: none !important;
        border-color: #E69500 !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        color: white !important;
    }

    /* زر Gemini Check */
    div[data-testid="stForm"] button[kind="secondary"] {
        background-color: #2C3E50 !important;
        background-image: none !important;
        color: white !important;
        border: none !important;
        font-weight: 800 !important;
        border-radius: 10px !important;
    }
    button[kind="secondary"] { border: 2px solid #EF6C00 !important; color: #EF6C00 !important; background: Orange !important; font-weight: 800 !important; border-radius: 10px !important; }

    .result-card { margin-top: 25px; padding: 20px; background-color: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 6px solid; color: #333; }
    .valid { border-color: #28a745; background-color: #F1F8E9; }
    .error { border-color: #dc3545; background-color: #FFF5F5; }

    div[data-testid="stPopover"] { position: fixed; bottom: 20px; left: 20px; z-index: 9999; }
    div[data-testid="stPopover"] button { background-color: #2C3E50 !important; color: white !important; border-radius: 12px !important; border: none !important; padding: 10px 20px !important; font-weight: bold !important; box-shadow: 0 4px 12px rgba(0,0,0,0.2); width: auto !important; height: auto !important; display: flex; align-items: center; gap: 8px; }
    div[data-testid="stPopover"] button::after { content: "✨ Gemini"; font-size: 16px; }
    #copyright { position: fixed; bottom: 10px; right: 20px; font-size: 12px; color: Black; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. SESSION STATE
# ==========================================
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'gemini_chat' not in st.session_state: st.session_state.gemini_chat = None
if 'validation_complete' not in st.session_state: st.session_state.validation_complete = False
if 'last_res' not in st.session_state: st.session_state.last_res = None
if 'chat_input_widget' not in st.session_state: st.session_state.chat_input_widget = ""

# ==========================================
# 4. KNOWLEDGE BASE (DATA)
# ==========================================
AD_WORDS_LIST = ["creamy","tender","refreshing","fiery","tropical","organic","crispy","aromatic","crunchy","buttery","juicy","fudgy","zesty","chewy","moist","handcrafted","fresh","whipped","classic","pure","soft","natural","seasonal","squeezed","premium","crusty","carbonated","flaky","fizzy","thick","thin","spiced","healthy","flavored","chunky","sweet","golden","salty","nutty","perfect for"]
GENERIC_PHRASES = ["perfectly paired with","often served with","typically","usually served with","traditionally","mighty with","ideal for","great for","can be with","maybe for","suggested with","suggestion","try it with","example","such as","likely"]
CHOICE_INDICATORS = ["choice","choose","selection","select","option","pick","اختيار","اختار", "بين", "between"]
CHOICE_SEPARATORS = [" or ", "/", "\\", " أو ", " أم "]
FLUFF_WORDS = ["with","and","in","the","a","an","of","for","to","served","plate","dish","meal","platter","box","bowl","piece","pcs","nice","delicious","tasty","yummy","amazing","best","good","great","hot","cold","warm","special","signature","authentic","original","traditional","famous","rich","favorite","cooked","prepared","enjoy","try","our","same as","نفس", "sauce", "top", "topping", "mix"]

ITEM_CATEGORIES = {"DRINK": ["juice", "soda", "water", "coffee", "tea", "cola", "pepsi", "عصير", "مشروب", "ماء", "قهوة", "شاي"], "SWEET": ["cake", "ice cream", "cookie", "chocolate", "knafeh", "basbousa", "baklava", "dessert", "كيك", "آيس كريم", "شوكولاتة", "حلويات", "كنافة", "بسبوسة", "بقلاوة", "crepe", "waffle", "krip", "wafl", "pistachio", "caramel", "كريب", "وافل", "فستق", "صوص حلو", "كريم"], "SAVORY_MAIN": ["chicken", "beef", "burger", "pizza", "sandwich", "shawarma", "rice", "pasta", "steak", "grill", "kebab", "meat", "zinger", "دجاج", "لحم", "برجر", "بيتزا", "شاورما", "أرز", "مكرونة", "كباب"]}
SECTION_CONFLICTS = {"main dishes": ["DRINK", "SWEET"], "main course": ["DRINK", "SWEET"], "desserts": ["SAVORY_MAIN"], "beverages": ["SAVORY_MAIN", "SWEET"], "appetizers": ["SWEET", "DRINK"]}
CONFLICT_GROUPS = [["chicken","beef","meat","lamb","fish","shrimp","tuna","pork","zinger", "دجاج", "لحم", "سمك"], ["pepsi","coca cola","cola","7up","sprite","mirinda","mountain dew"], ["pizza","burger","pasta","sandwich","shawarma","kebab","rice","biryani"], { "a": ["cheesecake","waffle","crepe","chocolate","dessert","cake","ice cream","brownie","tiramisu","pudding"], "b": ["onion","garlic","chicken","meat","pastrami","beef","shrimp","sausage","bacon","hot dog","burger","kebab","mayonnaise","ketchup","mustard","pickle","tuna"] }]
INCOMPATIBLE_PAIRS = [{ "a": ["sushi"], "b": ["bread","fries","burger"] }, { "a": ["pizza"], "b": ["rice","couscous"] }, { "a": ["soup"], "b": ["ice cream","waffle","cake"] }]
FORBIDDEN_LIST = ["wine","liquor","beer","tequila","vodka","ham","pig","whisky","bacon","chicharrón","cigarettes","e-cigarettes","vape","shisha","hooka flavors","alcohol","pork","lechon","tobacco","slave","hookah","dirty","naughty"]
OFFER_KEYWORDS = ["offer","special offer","buy 1","buy one","combo","discount"]
OFFER_EXCEPTIONS = ["share box","value meal","saving meal","free add-on","free item","combo","وجبة توفير","وجبة قيمة","صندوق مشاركة","كومبو"]
SAFE_BACON = ["beef","halal","turkey","veal","ديك رومي","بقري","حلال"]
SAFE_CURACAO = ["syrup","flavor","شراب","نكهة"]
INEDIBLE_ITEMS = ["iphone","samsung","mobile","laptop","mouse","car","bike","tire","chair","table","plastic","metal","glass","hooka tube","charcoal holder"]
INEDIBLE_PATTERN = r'\b(' + '|'.join(re.escape(w) for w in INEDIBLE_ITEMS) + r')\b'

# ==========================================
# 5. LOGIC FUNCTIONS
# ==========================================
def normalize_text(text): return text.lower().strip() if text else ""

def check_validation(name, desc, section, source):
    n, d, s = normalize_text(name), normalize_text(desc), normalize_text(section)
    
    # 1. Forbidden
    for w in FORBIDDEN_LIST:
        if w in n or w in d:
            if ("bacon" in w or "ham" in w) and any(safe in (n+d) for safe in SAFE_BACON): continue
            if "curacao" in w and any(safe in (n+d) for safe in SAFE_CURACAO): continue
            if w in n: return ("ERROR", "Forbidden Item (Name)", f"Forbidden word '{w}' in Name.", "DELETE ITEM", None)
            elif w in d:
                if source == "Main Menu": return ("ERROR", "Forbidden Item (Desc - Main)", f"Forbidden word '{w}' in Desc.", "DELETE ITEM", None)
                else: return ("ERROR", "Forbidden Item (Desc - Sep)", f"Forbidden word '{w}' in Desc.", "DELETE Description & Get from Library", None)
    
    # 2. Inedible
    match = re.search(INEDIBLE_PATTERN, d)
    if match: return ("ERROR", "Non-Food Item", f"Description contains inedible item: '{match.group(1)}'", "DELETE Description & Get from Library", None)

    # 3. Section Mismatch
    if s:
        for sec_key, banned_cats in SECTION_CONFLICTS.items():
            if sec_key in s:
                for cat in banned_cats:
                    for item_word in ITEM_CATEGORIES.get(cat, []):
                        if item_word in n:
                            if cat == "SAVORY_MAIN" and "main" in sec_key: continue
                            suggestion_list = [k for k, v in SECTION_CONFLICTS.items() if cat not in v]
                            suggestion = next((k for k in suggestion_list if "beverages" in k), suggestion_list[0] if suggestion_list else "Appropriate Section")
                            return ("ERROR", "Section Mismatch", f"Item '{name}' appears to be a {cat} (contains '{item_word}'), which doesn't belong in '{section}'.", "MOVE_OR_CREATE", suggestion)

    # 4. Conflicts
    for pair in INCOMPATIBLE_PAIRS:
        if any(w in n for w in pair['a']) and any(w in d for w in pair['b']):
             action = "DELETE ITEM" if source == "Main Menu" else "DELETE Description & Get from Library"
             return ("ERROR", "Mismatch", f"Conflict between '{pair['a'][0]}' and ingredients.", action, None)
    for group in CONFLICT_GROUPS:
        if isinstance(group, dict):
            if any(w in n for w in group['a']) and any(w in d for w in group['b']):
                action = "DELETE ITEM" if source == "Main Menu" else "DELETE Description & Get from Library"
                return ("ERROR", "Mismatch", "Sweet item paired with savory ingredients.", action, None)
        else:
            p_name = next((w for w in group if w in n), None)
            p_desc = next((w for w in group if w in d), None)
            if p_name and p_desc and p_name != p_desc:
                 action = "DELETE ITEM" if source == "Main Menu" else "DELETE Description & Get from Library"
                 return ("ERROR", "Mismatch", f"Protein mismatch: {p_name} vs {p_desc}", action, None)
    
    # 5. Offers
    if any(w in (n+d) for w in OFFER_KEYWORDS) and not any(e in (n+d) for e in OFFER_EXCEPTIONS):
        return ("ERROR", "Offer Detected", "Item appears to be a promotion/offer.", "DELETE ITEM", None)
    
    # 6. No Value Added (FIXED HERE)
    if is_no_value(n, d):
        return ("ERROR", "No Value", "Description adds no value.", "DELETE Description & Get from Library", None)

    # 7. Generic
    if "likely" in d: 
        action = "DELETE ITEM" if source == "Main Menu" else "DELETE Description & Get from Library"
        return ("ERROR", "Generic", "Vague description (likely).", action, None)
    if "like" in d and not re.search(r'like\s+.*?\s+(flavor|taste|نكهة|طعم)', d):
        action = "DELETE ITEM" if source == "Main Menu" else "DELETE Description & Get from Library"
        return ("ERROR", "Generic", "Contains 'like' without flavor context.", action, None)
    gen = next((p for p in GENERIC_PHRASES if p in d), None)
    if gen: 
        action = "DELETE ITEM" if source == "Main Menu" else "DELETE Description & Get from Library"
        return ("ERROR", "Generic", f"Contains suggestion: '{gen}'", action, None)

    # 8. Choices
    chk = check_choices(n, d, source)
    if chk["status"] == "undefined": 
        action = "DELETE ITEM" if source == "Main Menu" else "DELETE Description (Leave Empty)"
        return ("ERROR", "Undefined Choice", "Choices implied but no clear list.", action, None)
    elif chk["status"] == "defined_error_sep": 
        return ("WARNING", "Defined Choice (Sep)", "Choices not in Name.", "DELETE Description (Leave Empty)", None)

    return ("VALID", "Valid Item", "Content looks good.", "None", None)

def check_choices(name, desc, src):
    choice_pattern = r'\b(' + '|'.join(re.escape(w) for w in CHOICE_INDICATORS) + r')\b'
    has_indicator = bool(re.search(choice_pattern, desc))
    has_standard_sep = any(s in desc for s in CHOICE_SEPARATORS)
    has_between = "between" in desc or "بين" in desc
    has_and_sep = has_between and (" and " in desc or " و " in desc)
    if not (has_indicator or has_standard_sep or has_and_sep): return {"status": "none"}
    if has_indicator and not (has_standard_sep or has_and_sep): return {"status": "undefined"} 
    if src == "Main Menu": return {"status": "defined_valid"}
    else: 
        name_has_sep = any(s in name for s in CHOICE_SEPARATORS)
        return {"status": "defined_valid"} if name_has_sep else {"status": "defined_error_sep"}

# *** FIXED: Specific fix for Vegetables/Vegetable ***
def is_no_value(name, desc):
    # 1. Immediate Fail
    if "same as" in desc or "نفس" in desc: return True 
    
    # 2. Immediate Pass (Ad Words)
    for word in AD_WORDS_LIST:
        if re.search(rf'\b{re.escape(word)}\b', desc): return False

    # 3. Normalization (Force Vegetables -> Vegetable)
    # This simple replace fixes the plural issue specifically for common food terms
    clean_name = name.replace("vegetables", "vegetable").replace("fruits", "fruit")
    clean_desc = desc.replace("vegetables", "vegetable").replace("fruits", "fruit")

    # 4. Cleaning Logic
    # Remove Name tokens from Desc
    name_tokens = re.findall(r'\w+', clean_name.lower())
    for token in name_tokens:
        if len(token) > 1: 
            clean_desc = re.sub(rf'\b{re.escape(token)}s?\b', '', clean_desc) # Remove token + optional s
            
    for w in FLUFF_WORDS: 
        clean_desc = re.sub(rf'\b{re.escape(w)}\b', '', clean_desc)
        
    return len(re.sub(r'\W+', '', clean_desc).strip()) < 3

def get_action_text(key, src, name, suggestion=None):
    if key == "MOVE_OR_CREATE": 
        return f"MOVE Item to Section: **{suggestion}** or CREATE NEW Section for it"
    actions = {"DELETE ITEM": "DELETE Item", "DELETE Description & Get from Library": "DELETE Description and Get from Library", "DELETE Description (Leave Empty)": "DELETE Description (Leave Empty)"}
    return actions.get(key, key)

def generate_comment(title, msg, action, src, name, key):
    clean_msg = re.sub(r'<[^>]+>', '', msg)
    reason = clean_msg
    if "Forbidden" in title: reason = f"forbidden word"
    elif "Mismatch" in title: reason = "mismatch between item and description"
    elif "Section Mismatch" in title: 
        parts = clean_msg.split("'")
        if len(parts) >= 4: reason = f'Item "{parts[1]}" (contains "{parts[3]}") is placed in the wrong section.'
    elif "No Value" in title: reason = "description does not add value"
    elif "Generic" in title: reason = "generic description"
    elif "Undefined" in title: reason = "undefined choices"
    elif "Offer" in title: reason = "it is an offer"
    
    if "DELETE ITEM" in action: return f'I deleted item "{name}" because of {reason} in {src}.'
    elif "DELETE Description & Get from Library" in action: return f'I deleted item\'s description "{name}" because of {reason} in {src} and replaced it from description library.'
    elif "DELETE Description (Leave Empty)" in action: return f'I deleted item\'s description "{name}" because of {reason} in {src}.'
    elif "DELETE Description" in action: return f'I deleted item\'s description "{name}" because of {reason} in {src}.'
    elif "MOVE" in action:
        return f'I moved item "{name}" to section "**{key if key else "appropriate"}**" because of {reason} in {src}.'
    return f"Action taken: {action}"

# ==========================================
# 6. GEMINI FUNCTIONS
# ==========================================
def init_gemini_client():
    if not API_KEY or API_KEY == "PASTE_YOUR_API_KEY_HERE": return None
    try: return genai.Client(api_key=API_KEY)
    except: return None

def get_gemini_verdict(name, desc, section, error_context):
    client = init_gemini_client()
    if not client: return "⚠️ API Key Missing"
    prompt = f"Context: Item: {name}, Desc: {desc}, Section: {section}, Error: {error_context}. Task: Check if this is a TRUE culinary/logic error. Output JSON: {{'Verdict': 'Valid' or 'Invalid', 'Reason': '...'}}"
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text.replace("```json", "").replace("```", "")
    except Exception as e: return f"AI Error: {e}"

def handle_chat_input():
    user_msg = st.session_state.chat_input_widget
    st.session_state.chat_input_widget = "" 
    client = init_gemini_client()
    if user_msg and client:
        try:
            history_context = "\n".join([f"{m['role']}: {m['text']}" for m in st.session_state.chat_history[-6:]])
            full_prompt = f"Previous Chat Context:\n{history_context}\n\nUser Question: {user_msg}\nAssistant:"
            res = client.models.generate_content(model='gemini-2.5-flash', contents=full_prompt)
            st.session_state.chat_history.append({"role": "user", "text": user_msg})
            st.session_state.chat_history.append({"role": "ai", "text": res.text})
        except Exception as e: st.error(f"Chat Error: {e}")

# ==========================================
# 7. UI LAYOUT (سنتر اللوجو والاسم)
# ==========================================
import base64

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# محاولة قراءة الصورة وعرضها في المنتصف مع النص
try:
    img_base64 = get_base64_of_bin_file("logo.png")
    
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 20px; margin-bottom: 30px;">
            <img src="data:image/png;base64,{img_base64}" width="80" style="filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.2)); animation: float 3s ease-in-out infinite;">
            <h1 style="margin: 0; padding: 0; line-height: 1; font-family: sans-serif; font-weight: 900; font-size: 3.5rem;">
                <span style="color: #FF5A00;">OCT</span>
                <span style="color: #000000;">VALIDATOR</span>
            </h1>
        </div>
        <style>
        @keyframes float {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-8px); }}
            100% {{ transform: translateY(0px); }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
except FileNotFoundError:
    # بديل في حالة عدم وجود الصورة
    st.markdown("""
        <h1 style='text-align: center; margin-bottom: 30px;'>
            <span style='color: #FF5A00;'>Oct</span> <span style='color: #000000;'>Validator</span> 🐙
        </h1>
    """, unsafe_allow_html=True)
    st.warning("⚠️ ملف logo.png غير موجود في الفولدر!")


with st.form("validation_form"):
    st.markdown("### Item Details")
    
    # ... (باقي الفورم زي ما هو ماتغيرش فيه حاجة) ...
    c1, c2 = st.columns([1, 2])
    with c1: source = st.radio("Source", ["Main Menu", "Sep Sheet"], horizontal=True)
    with c2: section = st.text_input("Section Name (Optional)", placeholder="e.g., Main Course")
    
    st.markdown("")
    name = st.text_input("Item Name", placeholder="Enter the item name")
    desc = st.text_area("Item Description", placeholder="Enter ingredients or description", height=100)
    
    st.markdown("---")
    b1, b2 = st.columns([1, 1])
    with b1: validate_btn = st.form_submit_button("VALIDATE ITEM", type="primary", use_container_width=True)
    with b2: gemini_btn = st.form_submit_button("GEMINI CHECK", type="secondary", use_container_width=True)

if validate_btn:
    if not name: st.warning("⚠️ Please enter an Item Name.")
    else:
        res_type, title, msg, action, suggestion = check_validation(name, desc, section, source)
        st.session_state.last_res = (res_type, title, msg, action, suggestion)
        st.session_state.validation_complete = True

if gemini_btn:
    if not st.session_state.validation_complete: st.error("⚠️ Please run 'VALIDATE' first.")
    elif st.session_state.last_res[0] == "VALID": st.success("✅ Item is VALID. No AI check needed.")
    else:
        with st.spinner("🤖 Gemini is analyzing..."):
            ai_res = get_gemini_verdict(name, desc, section, st.session_state.last_res[2])
            st.markdown(f"#### ✨ Gemini Opinion")
            st.markdown(f"""<div style="background: #FFF3E0; padding: 15px; border-radius: 10px; border-left: 5px solid #E65100; color: #333; margin-top: 20px;"><strong>✨ Gemini Opinion:</strong><br>{ai_res}</div>""", unsafe_allow_html=True)

if st.session_state.validation_complete:
    rtype, title, msg, action_key, suggestion = st.session_state.last_res
    card_class, icon, title_color = ("valid", "✅", "#28a745") if rtype == "VALID" else ("error", "⛔", "#dc3545")
    final_action_text = get_action_text(action_key, source, name, suggestion)

    st.markdown(f"""
    <div class="result-card {card_class}">
        <h3 style='margin-top:0; color:{title_color}; display:flex; align-items:center; gap:10px;'><span style='font-size:1.3em;'>{icon}</span> {title}</h3>
        <p style='font-size:1.1rem; font-weight:500; margin: 15px 0; color: #333;'>{msg}</p>
        <div style='background: rgba(0,0,0,0.04); padding: 12px; border-radius: 8px; margin-top:15px;'>
            <p style='margin-bottom:0; font-size:1rem; color:#222;'><strong>👉 Action Required:</strong> {final_action_text}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if rtype != "VALID":
        comment = generate_comment(title, msg, final_action_text, source, name, suggestion)
        st.code(comment, language="text")

with st.popover("💬"):
    st.markdown("### ✨ Gemini Chat")
    st.caption("Ask me anything...")
    chat_container = st.container(height=300)
    with chat_container:
        if not st.session_state.chat_history: st.info("👋 Hi! How can I help?")
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user': st.markdown(f"""<div style='text-align:right; background:#FFECB3; color:#333; padding:8px 12px; border-radius:15px 15px 0 15px; display:inline-block; margin:5px 0; float:right; clear:both;'>{msg['text']}</div>""", unsafe_allow_html=True)
            else: st.markdown(f"""<div style='text-align:left; background:#F5F5F5; color:#333; padding:8px 12px; border-radius:15px 15px 15px 0; display:inline-block; margin:5px 0; float:left; clear:both;'>{msg['text']}</div>""", unsafe_allow_html=True)
    st.text_input("Message...", key="chat_input_widget", on_change=handle_chat_input)

st.markdown('<div id="copyright">© 2025 Aly Maher</div>', unsafe_allow_html=True)

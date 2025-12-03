import streamlit as st
import re
import time
import os
from google import genai
from google.genai.errors import APIError
import json

# ==========================================
# GEMINI INTEGRATION FUNCTION (Omitted for brevity)
# ==========================================
def get_gemini_analysis(item_name, item_desc, current_error_msg):
    """يستدعي Gemini لتقديم اقتراح محسّن لوصف المنتج بناءً على خطأ التحقق."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "⚠️ Gemini Analysis Failed: API Key not set."

        client = genai.Client(api_key=api_key)

        system_prompt = (
            "You are a Senior Menu Content Validator for a large food delivery platform. "
            "Your task is to review an item and an identified conflict. "
            "You must suggest the single best way to correct the item description and item name to resolve the conflict and add commercial value. "
            "Respond ONLY with the suggested action and improved text, formatted as a clean JSON object."
        )

        user_prompt = (
            f"Item Name: {item_name}\n"
            f"Item Description: {item_desc}\n"
            f"Validator Error: {current_error_msg}\n\n"
            "Suggest an IMPROVED Item Name and IMPROVED Description to fix the conflict and sound professional. "
            "Output MUST be a JSON object with two keys: 'Improved Name' and 'Improved Description'."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config={
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "Improved Name": {"type": "string", "description": "The suggested new item name."},
                        "Improved Description": {"type": "string", "description": "The suggested new item description."},
                    },
                    "required": ["Improved Name", "Improved Description"],
                }
            }
        )
        
        data = json.loads(response.text)
        
        return (
            f"💡 **Gemini Suggestion:**\n\n"
            f"**Improved Name:** {data.get('Improved Name', 'N/A')}\n\n"
            f"**Improved Description:** {data.get('Improved Description', 'N/A')}"
        )

    except APIError as e:
        return f"❌ Gemini Analysis Failed: Check API connection or key validity. (Error: {e})"
    except Exception as e:
        return f"❌ Gemini Analysis Failed (Internal Error: {e})"

def gemini_knowledge_search(query):
    """يستدعي Gemini لتقديم إجابة سريعة على أي استعلام معرفي."""
    if not query:
        return "Please enter a search query."
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "⚠️ Search Failed: API Key not set."

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                "You are a rapid knowledge retrieval tool. Answer the following question briefly and clearly:",
                query
            ]
        )
        return response.text
    except Exception as e:
        return f"❌ Search Error: {e}"

def gemini_consistency_check(item_name, item_desc, section_name):
    """يفحص Gemini الاتساق الشامل بين القسم والمنتج والوصف."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "⚠️ Consistency Check Failed: API Key not set."

        client = genai.Client(api_key=api_key)

        system_prompt = (
            "You are a Senior Commercial Content Reviewer for a major food delivery app. "
            "Your main objective is to enforce high-quality, non-ambiguous, and commercially compelling menu content. "
            "CRITERIA:\n"
            "1. Consistency: Check for clear logical match between the Item Name and Item Description, and ensure they are contextually appropriate for the Section Name.\n"
            "2. Quality: REJECT content if the description is too generic (e.g., 'good for you', 'delicious', 'try it with'), if it repeats the item name without adding value, or if it implies customer choice without explicit options (e.g., 'choose your meat').\n"
            "3. Standards: Flag any content that suggests illegal or offensive items, or promotes offers/discounts which should be handled elsewhere.\n"
            "Determine the final verdict (ACCEPTED/REJECTED). Respond ONLY with a JSON object."
        )

        user_prompt = (
            f"Section Name: {section_name}\n"
            f"Item Name: {item_name}\n"
            f"Item Description: {item_desc}\n\n"
            "Based on commercial content standards: Is the item internally consistent (Name/Desc) and contextually consistent (Section)? "
            "Does the description contain ambiguous or generic language that should be REJECTED, or is it ACCEPTABLE?"
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config={
                "system_instruction": system_prompt,
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "Consistency Status": {"type": "string", "description": "'Perfect Match' or 'Inconsistent: [reason]'."},
                        "Generic Language Decision": {"type": "string", "description": "'ACCEPTED' or 'REJECTED: [reason]'."}
                    },
                    "required": ["Consistency Status", "Generic Language Decision"],
                }
            }
        )
        
        data = json.loads(response.text)
        
        return (
            f"--- **Comprehensive Check (Gemini)** ---\n"
            f"**Consistency Status:** {data.get('Consistency Status', 'N/A')}\n"
            f"**Generic Language Decision:** {data.get('Generic Language Decision', 'N/A')}\n"
        )

    except Exception:
        return "❌ Comprehensive Check Failed (API or Internal Error)."

# (Remaining helper functions and logic definitions remain the same)
AD_WORDS_LIST = ["creamy","tender","refreshing","fiery","tropical","organic","crispy","aromatic","crunchy","buttery","juicy","fudgy","zesty","chewy","moist","handcrafted","fresh","whipped","classic","pure","soft","natural","seasonal","squeezed","premium","crusty","carbonated","flaky","fizzy","thick","thin","spiced","healthy","flavored","chunky","sweet","golden","salty","nutty","perfect for"]
GENERIC_PHRASES = ["perfectly paired with","often served with","typically","usually served with","traditionally","mighty with","ideal for","great for","can be with","maybe for","suggested with","suggestion","try it with","example","such as","يقدم مع","عادة يقدم مع","مثالي مع","تقليديا","اقتراح","جربه مع","مثل","اختيارك من", "likely"]
CHOICE_INDICATORS = ["choice","choose","selection","select","option","pick","اختيار","اختار"]
CHOICE_SEPARATORS = [" or ","/","\\"," أو "," أم "]
FLUFF_WORDS = ["with","and","in","the","a","an","of","for","to","served","plate","dish","meal","platter","box","bowl","piece","pcs","nice","delicious","tasty","yummy","amazing","best","good","great","hot","cold","warm","special","signature","authentic","original","traditional","famous","rich","favorite","cooked","prepared","enjoy","try","our","مع","و","في","ال","طبق","وجبة","صحن","قطعة","لذيذ","شهي","رائع","مميز","ساخن","بارد","أصلي","تقليدي","فاخر","غني","مفضل","مطبوخ","مجهز","استمتع","جرب","مكونات","طعم","نكهة","خلطة","تتبيلة","محضر","طريقة","خاصة","من","على"]
CONFLICT_GROUPS = [
    ["chicken","beef","meat","lamb","fish","shrimp","tuna","pork","دجاج","لحم","سمك","جمبري","تونا","خنزير","بقري","غنم", "zinger"],
    ["pepsi","coca cola","cola","7up","sprite","mirinda","mountain dew","بيبسي","كولا","سفن","ميريندا","مشروب"],
    ["pizza","burger","pasta","sandwich","shawarma","kebab","rice","biryani","بيتزا","برجر","باستا","ساندوتش","شاورما","كباب","أرز","برياني"],
    { "a": ["cheesecake","waffle","crepe","chocolate","dessert","cake","ice cream","brownie","tiramisu","pudding","حلو","كيك","شوكولاتة","وافل","كريب","آيس كريم","تحلية"], 
      "b": ["onion","garlic","chicken","meat","pastrami","beef","shrimp","sausage","bacon","hot dog","burger","kebab","mayonnaise","ketchup","mustard","pickle","tuna","بصل","ثوم","دجاج","لحم","بسطرمة","سجق","برجر","كاتشب","مايونيز"] }
]
INCOMPATIBLE_PAIRS = [
    { "a": ["sushi","سوشي"], "b": ["bread","fries","burger","خبز","بطاطس"] },
    { "a": ["pizza","بيتزا"], "b": ["rice","couscous","أرز","كسكسي"] },
    { "a": ["soup","شوربة"], "b": ["ice cream","waffle","cake","آيس كريم"] }
]
PRIMARY_FOOD_KEYWORDS = ["burger", "pizza", "kebab", "shawarma", "sandwich", "chicken", "beef", "meat", "lamb", "دجاج", "لحم", "برجر", "بيتزا", "شاورما", "ساندوتش", "وجبة"]
ITEM_CATEGORIES = {
    "DRINK": ["juice", "soda", "water", "coffee", "tea", "عصير", "مشروب", "ماء", "قهوة", "شاي"],
    "SWEET": ["cake", "ice cream", "cookie", "chocolate", "كيك", "آيس كريم", "شوكولاتة", "حلويات", "crepe", "waffle", "كريب", "وافل", "pistachio", "فستق", "صوص حلو", "sweet sauce", "caramel", "كريم"],
    "SAVORY_MAIN": ["chicken", "beef", "burger", "pizza", "sandwich", "shawarma", "rice", "دجاج", "لحم", "برجر", "بيتزا", "شاورما", "أرز"],
}
SECTION_CONFLICTS = {
    "main dishes": ["DRINK", "SWEET"], "main course": ["DRINK", "SWEET"], "desserts": ["SAVORY_MAIN"], "beverages": ["SAVORY_MAIN", "SWEET"] 
}
FORBIDDEN_LIST = ["wine","liquor","beer","tequila","vodka","ham","pig","whisky","bacon","chicharrón","cigarettes","e-cigarettes","vape","shisha","hooka flavors","alcohol","pork","lechon","tobacco","slave","israel","israeli","trotters","prosciutto","blue curacao","fatback","gammon","pancetta","afelia","crubeens","crispy pata","pata tim","bondiola","butadon","butajiru","cochon","carnitas","eisbein","cassoeula","chorizo","ciccioli","cochinita pibil","margarita","v60 tobacco","نبيذ","بيرة","كحول","خنزير","شيشة","معسل","فحم", "hookah", "dirty", "naughty"]
UAE_ONLY_FORBIDDEN = ["valencay cheese","uranus star water"]
INEDIBLE_ITEMS = ["iphone","samsung","mobile","phone","laptop","keyboard","mouse","app","car","bike","taxi","bus","engine","tire","wheel","table","chair","sofa","bed","furniture","door","window","shirt","pants","shoe","dress","clothing","socks","dog","cat","pet","poison","plastic","metal","gold","silver", "hooka tube", "charcoal holder", "shisha items"]
OFFER_KEYWORDS = ["offer","عروض","عرض","special offer","خصم"]
OFFER_EXCEPTIONS = ["share box","value meal","saving meal","free add-on","free item","combo","وجبة توفير","وجبة قيمة","صندوق مشاركة","كومبو"]
SAFE_BACON = ["beef","halal","veal","بقري","حلال", "turkey", "ديك رومي"]
SAFE_CURACAO = ["syrup","flavor","شراب","نكهة"]
INEDIBLE_PATTERN = r'\b(' + '|'.join(re.escape(w) for w in INEDIBLE_ITEMS) + r')\b'

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'[ًٌٍَُِّْ]', '', text)
    return text

def check_forbidden(name, desc):
    full_text = f"{name} {desc}"
    
    for w in UAE_ONLY_FORBIDDEN:
        if w in full_text: return {"msg": f'Forbidden (UAE Only): "{w}"', "location": "name" if w in name else "desc"}
    
    for w in FORBIDDEN_LIST:
        if w in full_text:
            is_ham_or_bacon = "bacon" in w or "ham" in w
            if is_ham_or_bacon and any(s in full_text for s in SAFE_BACON): continue
            
            if "curacao" in w and any(s in full_text for s in SAFE_CURACAO): continue
            return {"msg": f'Forbidden: "{w}"', "location": "name" if w in name else "desc"}
    
    match = re.search(INEDIBLE_PATTERN, desc)
    if match: 
        banned_word = match.group(1) 
        return {"msg": f'Inedible item: "{banned_word}"', "location": "desc"}
    
    return None

def check_offers(sec, name_raw, desc_raw):
    sec = normalize_text(sec)
    full_text = f"{name_raw.lower()} {desc_raw.lower()}"
    if sec and ("offer" in sec or "عروض" in sec): return {"msg": "Section has 'Offer'.", "action": "DELETE SECTION"}
    if re.search(r'(\d+\s*\+|\+\s*\d+)|(buy\s+\d)|(\d+\s*free)|(\d+\s*مجانا)|(اشتري\s+\d)', name_raw.lower()):
        return {"msg": "Numerical Offer detected.", "action": "DELETE ITEM"}
    if any(w in full_text for w in OFFER_KEYWORDS) and not any(ex in full_text for ex in OFFER_EXCEPTIONS):
        return {"msg": "Item flagged as Offer.", "action": "DELETE ITEM"}
    return None

def find_conflict(name, desc, section):
    for pair in INCOMPATIBLE_PAIRS:
        if any(w in name for w in pair['a']) and any(w in desc for w in pair['b']):
            conflict = next((w for w in pair['b'] if w in desc), "")
            if conflict and conflict not in name: return {"n": next((w for w in pair['a'] if w in name), ""), "d": conflict, "type": "Internal"}
    for group in CONFLICT_GROUPS:
        if isinstance(group, dict):
            sweet, savory = next((s for s in group['a'] if s in name), None), next((s for s in group['b'] if s in desc), None)
            if sweet and savory and savory not in name: return {"n": sweet, "d": savory, "type": "Internal"}
        else:
            in_name, in_desc = [w for w in group if w in name], [w for w in group if w in desc]
            conflict = next((x for x in in_desc if x not in in_name), None)
            if in_name and in_desc and conflict and conflict not in name: return {"n": in_name[0], "d": conflict, "type": "Internal"}
    
    if section:
        for sec_key, banned_categories in SECTION_CONFLICTS.items():
            if sec_key in section:
                
                for banned_cat_key in banned_categories:
                    banned_items = ITEM_CATEGORIES.get(banned_cat_key, [])
                    banned_word = next((w for w in banned_items if w in name), None)
                    
                    if banned_word:
                        is_primary_food = any(w in name for w in PRIMARY_FOOD_KEYWORDS)
                        if is_primary_food and sec_key in ["main dishes", "main food", "main course"]: 
                            continue
                        
                        suggested_section_name = next((k for k, v in SECTION_CONFLICTS.items() if banned_cat_key in v and k != sec_key and k not in ["main dishes", "main course"]), None)
                        
                        best_match = suggested_section_name if suggested_section_name else "N/A"
                        
                        return {
                            "n": name, 
                            "d": section, 
                            "type": "SectionMismatch", 
                            "banned": banned_word, 
                            "suggestion": best_match
                        }
    
    return None

def check_choices(name, desc, src):
    choice_pattern = r'\b(' + '|'.join(re.escape(w) for w in CHOICE_INDICATORS) + r')\b'
    has_indicator = bool(re.search(choice_pattern, desc))
    has_standard_sep = any(s in desc for s in CHOICE_SEPARATORS)
    has_between = "between" in desc or "بين" in desc
    has_and_sep = has_between and (" and " in desc or " و " in desc)
    
    if not (has_indicator or has_standard_sep or has_and_sep):
        return {"status": "none"}
    if has_indicator and not (has_standard_sep or has_and_sep):
         return {"status": "undefined"} 

    temp_desc = desc
    if has_between:
        temp_desc = temp_desc.replace(" and ", " / ").replace(" و ", " / ")
        
    parts = re.split(r'(\/| or |\\| أو | أم )', temp_desc)
    match = any(len(p.strip()) > 2 and p.strip().lower() in name for p in parts if p.strip() not in CHOICE_SEPARATORS)
    
    if src == "Sep Sheet": return {"status": "defined_valid"} if match else {"status": "defined_error_sep"}
    return {"status": "defined_valid"}

def is_no_value(name, desc):
    if "same as" in desc or "نفس" in desc:
        return True 

    if "flavored" in desc or "flavor" in desc:
        return False
    
    for word in AD_WORDS_LIST:
        if word in desc:
            return False

    clean = desc
    for t in re.split(r'[^\w]+', name): 
        if len(t)>1: clean = re.sub(rf'\b(ال)?{re.escape(t)}\b', "", clean)
    
    fluff_and_same_as = FLUFF_WORDS + ["same as", "نفس"] 
    for w in fluff_and_same_as: 
        clean = re.sub(rf'\b{re.escape(w)}\b', "", clean)
        
    return len(re.sub(r'[^\w]+', "", clean).strip()) < 2

def get_action_text(key, src, name, suggestion=None):
    actions = {
        "DELETE SECTION": "DELETE THE WHOLE SECTION",
        "DELETE ITEM": "DELETE Item",
        "forbidden_name": "DELETE Item",
        "forbidden_desc_logic": "DELETE Item" if src == "Main Menu" else "DELETE Description & Get from Library",
        "mismatch": "DELETE Item" if src == "Main Menu" else "DELETE Description & Get from Library",
        "section_mismatch": f"MOVE Item to Section: **{suggestion}**" if suggestion != "N/A" else "CREATE NEW Section for Item",
        "generic": "DELETE Item" if src == "Main Menu" else "DELETE Description & Get from Library",
        "undefined_choice": "DELETE Item" if src == "Main Menu" else "DELETE Description (Leave Empty)",
        "defined_choice_sep": "DELETE Description (Leave Empty)",
        "novalue": "DELETE Description & Get from Library"
    }
    
    if key == "section_mismatch":
        return f"MOVE Item to Section: **{suggestion}**" if suggestion != "N/A" else "CREATE NEW Section for Item"
    
    return actions.get(key, "")

def generate_comment(title, msg, action, src, name, key):
    clean_msg = re.sub(r'<[^>]+>', '', msg)
    reason = clean_msg
    if "Forbidden" in title: reason = f'forbidden word "{clean_msg.split(chr(34))[1] if chr(34) in clean_msg else "found"}"'
    elif "Mismatch" in title: reason = "mismatch between item and description"
    elif "Section Mismatch" in title: 
        parts = clean_msg.split('**')
        item_name_part = parts[1]
        banned_word_part = parts[3].strip('"')
        section_name_part = parts[5]
        suggested_section_part = parts[7]
        reason = f'Item "{item_name_part}" (contains "{banned_word_part}") is placed in the wrong section "{section_name_part}".'
    elif "No Value" in title: reason = "description does not add value"
    elif "Generic" in title: reason = "generic description"
    elif "Undefined" in title: reason = "undefined choices"
    elif "Offer" in title: reason = "it is an offer"

    if "DELETE Item" in action or "WHOLE SECTION" in action:
        return f'I deleted item "{name}" because of {reason} in {src}.'
    elif "DELETE Description" in action:
        extra = " and replaced it from library" if "Library" in action else ""
        if key == "defined_choice_sep": reason, extra = "choices not mentioned in item name", ""
        if key == "undefined_choice" and src == "Sep Sheet": extra = ""
        return f'I deleted item\'s description "{name}" because of {reason} in {src}{extra}.'
    elif "MOVE Item" in action:
        parts = clean_msg.split('**')
        banned_word_part = parts[3].strip('"')
        suggested_section_part = parts[7]
        section_name_part = parts[5]
        return f'I moved item "{name}" because it contains "{banned_word_part}" which belongs in a section like "{suggested_section_part}" instead of "{section_name_part}".'
    elif "CREATE NEW Section" in action:
        parts = clean_msg.split('**')
        item_name_part = parts[1]
        banned_word_part = parts[3].strip('"')
        section_name_part = parts[5]
        return f'I recommend creating a new section for Item "{item_name_part}" because it contains "{banned_word_part}" which conflicts with "{section_name_part}" and no suitable section was found.'
    return ""

# ==========================================
# UI STRUCTURE 
# ==========================================

# 1. Custom CSS for layout cleanup
st.markdown(
    """
    <style>
    /* Restore clean centered main block */
    .stApp {
        background-color: #F8F8F8; 
    }
    .block-container {
        padding-top: 2rem; 
        padding-bottom: 2rem;
        max-width: 650px; 
    }
    
    /* Custom style for the fixed Gemini container at bottom-left */
    .gemini-fixed-container {
        position: fixed;
        bottom: 20px;
        left: 20px;
        width: 300px;
        z-index: 1000;
        background-color: white; 
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        padding: 15px;
        border: 1px solid #ddd;
    }
    .stTextInput label {
        visibility: collapse; /* Hide label in fixed container */
    }
    </style>
    """, unsafe_allow_html=True
)

# 2. Main Title (Restore to clean centered look)
st.markdown("<h1>Oct <span>Validator</span> 🐙</h1>", unsafe_allow_html=True) 
st.write(" ")

with st.form("main_form"):
    c1, c2 = st.columns([1, 2])
    # Language FIX: All labels and options changed to English
    with c1: source = st.radio("Source", ["Main Menu", "Sep Sheet"], horizontal=True, label_visibility="collapsed")
    with c2: section_name = st.text_input("Section", placeholder="Section Name (Optional)", label_visibility="collapsed")
    
    item_name = st.text_input("Item Name", placeholder="Enter Item Name", label_visibility="collapsed")
    item_desc = st.text_area("Description", placeholder="Enter Item Description", height=68, label_visibility="collapsed")
    
    submit = st.form_submit_button("VALIDATE", type="primary")

# ==========================================
# RESULTS DISPLAY
# ==========================================
if submit:
    st.markdown('<div class="result-container">', unsafe_allow_html=True)
    if not item_name or not item_desc:
        st.warning("⚠️ Please enter Item Name and Description.")
    else:
        n_clean, d_clean = normalize_text(item_name), normalize_text(item_desc)
        s_clean = normalize_text(section_name)
        res = None
        
        # 1. Check Forbidden
        chk = check_forbidden(n_clean, d_clean)
        if chk: res = ("ERROR", "Forbidden Item", chk["msg"], "DELETE ITEM" if chk["location"]=="name" else "forbidden_desc_logic")
        
        # 2. Check Conflicts (Internal & Section)
        if not res:
            chk = find_conflict(n_clean, d_clean, s_clean)
            if chk:
                if chk['type'] == "SectionMismatch":
                    msg = f"Item **{item_name}** contains **\"{chk['banned']}\"**, which conflicts with the Section **\"{section_name}\"**. Suggested Section: **{chk['suggestion']}**"
                    res = ("ERROR", "Section Mismatch", msg, "section_mismatch", chk['suggestion'])
                else:
                    msg = f"Conflict: **{chk['n']}** vs **{chk['d']}**."
                    res = ("ERROR", "Internal Mismatch", msg, "mismatch")
        
        # 3. Check Offers
        if not res:
            chk = check_offers(s_clean, item_name, item_desc)
            if chk: res = ("ERROR", "Offer Forbidden", chk["msg"], chk["action"])
        
        # 4. Check Generic Phrases
        if not res:
            like_generic = False
            if "like" in d_clean:
                like_exception_pattern = r'like\s+.*?\s+(flavor|taste|نكهة|طعم)'
                if not re.search(like_exception_pattern, d_clean):
                    like_generic = True
            
            if like_generic:
                res = ("ERROR", "Generic / Suggestion", 'Contains keyword: "like" without flavor/taste context.', "generic")
            
            elif "often" in d_clean: 
                res = ("ERROR", "Generic / Suggestion", 'Contains keyword: "often".', "generic")
            else:
                gen = next((p for p in GENERIC_PHRASES if p in d_clean), None)
                if gen: res = ("ERROR", "Generic / Suggestion", f'Contains suggestion: "**{gen}**".', "generic")
        
        # 5. Check Choices
        if not res:
            chk = check_choices(n_clean, d_clean, source)
            if chk["status"] == "undefined": res = ("ERROR", "Undefined Choice", "Choices implied but no clear list.", "undefined_choice")
            elif chk["status"] == "defined_error_sep": res = ("WARNING", "Defined Choice (Sep)", "Choices not in Name.", "defined_choice_sep")
        
        # 6. Check No Value
        if not res and is_no_value(n_clean, d_clean): res = ("ERROR", "No Value Added", "Description repeats name/fluff.", "novalue")
        
        # 7. Final Status
        if not res: res = ("VALID", "Valid Item", "Everything looks good!", "none")

        # Display Results
        if len(res) == 5: # If SectionMismatch, it has 5 elements (rtype, title, msg, key, suggestion)
            rtype, title, msg, key, suggestion = res
        else:
            rtype, title, msg, key = res
            suggestion = None
            
        if rtype == "VALID": st.success(f"**{title}** - {msg}", icon="✅")
        else:
            if rtype == "ERROR": st.error(f"**{title}** - {msg}", icon="⛔")
            else: st.warning(f"**{title}** - {msg}", icon="⚠️")
            
            action_text = get_action_text(key, source, item_name, suggestion)
            final_comment = generate_comment(title, msg, action_text, source, item_name, key)
            
            col_res1, col_res2 = st.columns([1, 2])
            with col_res1: st.info(f"**Action:** {action_text}")
            with col_res2: st.code(final_comment, language="text")

            # عرض اقتراح Gemini (في حالة الأخطاء)
            if res[0] != "VALID":
                 error_title_msg = f"{title} - {msg}"
                 gemini_suggestion = get_gemini_analysis(item_name, item_desc, error_title_msg)
                 st.markdown(f"---")
                 st.markdown(gemini_suggestion)
                 
        # 8. NEW: Comprehensive Consistency Check (for VALID or WARNING items)
        if res[0] == "VALID" or res[0] == "WARNING":
             with st.spinner('Running Comprehensive Consistency Check (Gemini)...'):
                consistency_check_result = gemini_consistency_check(item_name, item_desc, section_name)
                st.markdown(f"---")
                st.markdown(consistency_check_result)
            
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# FIXED GEMINI CONTAINER (BOTTOM LEFT)
# ==========================================
# Use st.container to create a content block that will be fixed by CSS
with st.container():
    # Inject the fixed container class
    st.markdown('<div class="gemini-fixed-container">', unsafe_allow_html=True)
    
    # FIX: Simplified Title with star logo
    st.markdown("#### ⭐ Gemini ⭐") 
    
    # Language FIX: Placeholders are now English
    fixed_search_query = st.text_input("Ask Gemini anything:", key="fixed_search_query", placeholder="Ask Gemini anything...", label_visibility="collapsed")
    fixed_search_button = st.button("Get Knowledge", key="fixed_search_button", type="secondary")
    
    if fixed_search_button:
        with st.spinner('Searching...'):
            fixed_search_result = gemini_knowledge_search(fixed_search_query)
        st.info(fixed_search_result)
        
    st.markdown("</div>", unsafe_allow_html=True)

# إضافة حقوق النشر (التي لا يمكن إخفاؤها)
st.markdown('<div id="copyright-footer">Copyrights: Aly Maher</div>', unsafe_allow_html=True)

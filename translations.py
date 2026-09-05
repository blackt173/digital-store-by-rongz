MESSAGES = {
    'welcome_user': {
        'km': "សួស្តី {name}! ជម្រាបសួរ 😊\nស្វាគមន៍មកកាន់ហាងយើងខ្ញុំ!\nហាងយើងខ្ញុំមានលក់ផលិតផលឌីជីថល (Digital Products) ជាច្រើនប្រភេទដូចជា គណនី Pro និងផ្សេងៗទៀត។\nតើថ្ងៃនេះចង់រកមើលអីវ៉ាន់អីដែរបង?",
        'en': "Hello {name}!\nWelcome to our store! We sell various digital products, including Pro accounts and more.\nHow can I help you today?"
    },
    'welcome_admin': {
        'km': "សួស្តី មេ {name}! 🫡\nស្វាគមន៍មកកាន់ផ្ទាំងគ្រប់គ្រង (Admin)។",
        'en': "Hello {name} (Admin)!\nWelcome to the dashboard."
    },
    'btn_buy': {
        'km': "🛒 ទិញអីវ៉ាន់",
        'en': "🛒 Buy Products"
    },
    'btn_cart': {
        'km': "🛍️ កន្ត្រករបស់ខ្ញុំ",
        'en': "🛍️ My Cart"
    },
    'btn_orders': {
        'km': "📦 ប្រវត្តិទិញ",
        'en': "📦 My Orders"
    },
    'btn_support': {
        'km': "📞 ឆាតសួរAdmin",
        'en': "📞 Support"
    },
    'btn_dashboard': {
        'km': "📊 Dashboard",
        'en': "📊 Dashboard"
    },
    'btn_products': {
        'km': "📦 គ្រប់គ្រងអីវ៉ាន់",
        'en': "📦 Products"
    },
    'btn_add_product': {
        'km': "➕ បង្កើតអីវ៉ាន់ថ្មី",
        'en': "➕ Add Product"
    },
    'btn_add_stock': {
        'km': "📥 ថែមស្តុក",
        'en': "📥 Add Stock"
    },
    'btn_users': {
        'km': "👥 ភ្ញៀវទាំងអស់",
        'en': "👥 Users"
    },
    'btn_all_orders': {
        'km': "📈 ប្រវត្តិលក់ចេញ",
        'en': "📈 All Orders"
    },
    'btn_back': {
        'km': "🔙 ត្រឡប់ក្រោយ",
        'en': "🔙 Back"
    },
    'menu_title': {
        'km': "ម៉ឺនុយ:",
        'en': "Main Menu:"
    },
    'language_changed': {
        'km': "✅ ប្តូរមកប្រើភាសាខ្មែររួចរាល់ហើយបង។",
        'en': "✅ Language has been successfully changed to English."
    },
    'request_prompt': {
        'km': "📝 បងចង់ឱ្យមានលក់អីបន្ថែមទៀតដែរ? វាយប្រាប់មកបង:",
        'en': "📝 Please type the name of the service or product you want to request:"
    },
    'request_success': {
        'km': "✅ បានបញ្ជូនទៅ Admin ហើយ! អរគុណបង ពួកយើងនឹងពិនិត្យមើលឆាប់ៗនេះ។",
        'en': "✅ Your request has been successfully sent to the admins! We will review it shortly."
    },
    'request_cancelled': {
        'km': "❌ ខេនសល (បោះបង់) ហើយបង។",
        'en': "❌ Request cancelled."
    },
    'feedback_select_product': {
        'km': "⭐ សូមរើសអីវ៉ាន់ដែលបងចង់ដាក់ពិន្ទុអោយ:",
        'en': "⭐ Please select a product to provide feedback:"
    },
    'feedback_no_products': {
        'km': "❌ បងមិនទាន់បានទិញអីវ៉ាន់ណាមួយនៅឡើយទេ អញ្ចឹងអត់ទាន់អាចអោយពិន្ទុបានទេ។ ជួយទិញសិនទៅណា៎! 😄",
        'en': "❌ You don't have any purchased products to review yet. Please make a purchase first."
    },
    'feedback_ask_rating': {
        'km': "អោយ {product_name} ប៉ុន្មានផ្កាយដែរអូនបង? ⭐",
        'en': "How many stars would you give to {product_name}?"
    },
    'feedback_ask_comment': {
        'km': "📝 មានមតិយោបល់អីប្រាប់បានណា៎ សម្រាប់ {product_name}:",
        'en': "📝 Please write your comment/feedback for {product_name}:"
    },
    'feedback_success': {
        'km': "✅ អរគុណច្រើនបង សម្រាប់មតិយោបល់! ពួកយើងនឹងខិតខំធ្វើឱ្យកាន់តែល្អជាងមុនទៀត។",
        'en': "✅ Thank you for your feedback! It helps us improve our services."
    },
    'feedback_cancelled': {
        'km': "❌ ខេនសល (បោះបង់) ហើយបង។",
        'en': "❌ Feedback submission cancelled."
    },
    'btn_profile': {
        'km': "👤 គណនីខ្ញុំ",
        'en': "👤 Profile"
    },
    'btn_help': {
        'km': "❓ របៀបទិញ",
        'en': "❓ Help"
    },
    'btn_main_menu': {
        'km': "📤 ម៉ឺនុយ",
        'en': "📤 Main Menu"
    }
}

def t(key, lang='km', **kwargs):
    """Translate a given key into the target language."""
    if key not in MESSAGES:
        return key
    
    text = MESSAGES[key].get(lang, MESSAGES[key].get('km', key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text

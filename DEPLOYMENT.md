# 🚀 មគ្គុទ្ទេសក៍ដំឡើង Telegram Bot ឱ្យដំណើរការ ២៤/៧ នៅលើ Apsara Hosting (VPS)
# Guide to Deploy DigitalShop Telegram Bot 24/7 on Apsara Hosting (Ubuntu/Debian VPS)

ឯកសារនេះណែនាំពីជំហានលម្អិតពីដើមដល់ចប់ ក្នុងការដាក់ Telegram Bot ឱ្យដំណើរការ ២៤ ម៉ោងលើ ២៤ ម៉ោងនៅលើ Cloud VPS (Ubuntu/Debian) របស់ Apsara Hosting។

---

## 📋 តម្រូវការជាមុន (Prerequisites)
1. **គណនី VPS ពី Apsara Hosting** (Ubuntu 22.04 LTS ឬ 24.04 LTS ត្រូវបានណែនាំ)
2. **ព័ត៌មានភ្ជាប់ VPS**៖
   - `IP Address` (ឧទាហរណ៍: `103.xxx.xxx.xxx`)
   - `User`: `root`
   - `Password` ឬ `SSH Key`
3. កម្មវិធីសម្រាប់ SSH ដូចជា **Terminal / PowerShell** (Windows/Mac) ឬ **Termius / PuTTY**

---

## 🛠️ ជំហានអនុវត្តជាក់ស្តែង (Step-by-Step Instructions)

### ជំហានទី ១៖ ភ្ជាប់ទៅកាន់ VPS តាមរយៈ SSH (Connect to VPS)
បើក **PowerShell** ឬ **Terminal** នៅលើកុំព្យូទ័ររបស់អ្នក រួចវាយពាក្យបញ្ជា (Command)៖
```bash
ssh root@<IP_របស់_VPS_អ្នក>
```
*ឧទាហរណ៍៖ `ssh root@103.216.50.12`*  
*(ពេលសួរ Password សូមវាយ password ចូលរួចចុច Enter — ចំណាំ: ពេលវាយ password វាមិនបង្ហាញអក្សរទេ)*

---

### ជំហានទី ២៖ Update ប្រព័ន្ធ និងដំឡើង Python3, Git, Pip
ដំណើរការ Command ខាងក្រោមដើម្បី update package និងដំឡើងឧបករណ៍ចាំបាច់៖
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git
```

---

### ជំហានទី ៣៖ ទាញយកកូដពី GitHub មកកាន់ VPS (Clone Repository)
ចូលទៅកាន់ folder `/root` ហើយ clone project របស់អ្នក៖
```bash
cd /root
git clone https://github.com/blackt173/digital-store-by-rongz.git
cd digital-store-by-rongz
```

---

### ជំហានទី ៤៖ បង្កើត Virtual Environment និងដំឡើងបណ្ណាល័យ (Install Dependencies)
បង្កើត Python Virtual Environment ដើម្បីកុំឱ្យជាន់គ្នាជាមួយ system package៖
```bash
# ១. បង្កើត venv
python3 -m venv venv

# ២. បើកដំណើរការ venv
source venv/bin/activate

# ៣. ដំឡើងបណ្ណាល័យទាំងអស់ពី requirements.txt
pip install --upgrade pip
pip install -r requirements.txt
```

---

### ជំហានទី ៥៖ បង្កើត និងកំណត់ឯកសារ `.env` (Configuration)
ចម្លងគំរូ `.env.example` ទៅជា `.env` រួចកែសម្រួលព័ត៌មានសម្ងាត់របស់អ្នក៖
```bash
cp .env.example .env
nano .env
```
ប្រើគ្រាប់ចុចព្រួញចុះក្រោម ហើយបញ្ចូលទិន្នន័យជាក់ស្តែងរបស់អ្នក៖
- `BOT_TOKEN`: Token របស់ Telegram Bot ពី @BotFather
- `ADMIN_IDS`: Telegram User ID របស់អ្នកគ្រប់គ្រង (ឧទាហរណ៍: `123456789`)
- `GROUP_ID`: ID នៃ Telegram Group សម្រាប់ទទួលដំណឹង (ប្រសិនបើមាន)
- `KHQR_ACCOUNT_ID`, `MERCHANT_NAME`, `MERCHANT_CITY`, `BAKONG_TOKEN`: ព័ត៌មានគណនីបាគង KHQR របស់អ្នក

> **គន្លឹះក្នុង nano៖**
> - ចុច `Ctrl + O` រួចចុច `Enter` ដើម្បី Save (រក្សាទុក)
> - ចុច `Ctrl + X` ដើម្បីចេញ (Exit)

---

### ជំហានទី ៦៖ តេស្តដំណើរការ Bot សាកល្បង (Test Run)
ដំណើរការ Bot មើលថាតើមាន Error អ្វីដែរឬទេ៖
```bash
python main.py
```
- បើក Telegram រួចផ្ញើសារ `/start` ទៅកាន់ Bot របស់អ្នក។
- ប្រសិនបើ Bot ឆ្លើយតបធម្មតា មានន័យថាការដំឡើងត្រឹមត្រូវ 100%។
- ចុច `Ctrl + C` នៅលើ Terminal ដើម្បីផ្អាក Bot ជាបណ្តោះអាសន្ន មុននឹងបន្តទៅជំហានទី ៧។

---

### ជំហានទី ៧៖ កំណត់ឱ្យ Bot ដំណើរការ ២៤/៧ ដោយស្វ័យប្រវត្តិ (Run 24/7 with Systemd)
ដើម្បីឱ្យ Bot ដំណើរការជាប់រហូត បើទោះជាអ្នកបិទកុំព្យូទ័រ ឬ Server Restart ក៏ Bot នៅតែបើកវិញដោយស្វ័យប្រវត្ត៖

#### វិធីទី ១៖ ប្រើប្រាស់ `systemd` (វិធីសាស្ត្រស្តង់ដារ និងល្អបំផុត - Recommended)
ឯកសារ `digitalshop.service` មានស្រាប់ក្នុង project៖

```bash
# ១. ចម្លង service file ទៅកាន់ system directory
sudo cp digitalshop.service /etc/systemd/system/

# ២. Reload systemd daemon
sudo systemctl daemon-reload

# ៣. បើកឱ្យ Bot ចាប់ផ្តើមដំណើរការជាមួយម៉ាស៊ីន server (Auto-start on boot)
sudo systemctl enable digitalshop

# ៤. ចាប់ផ្តើមដំណើរការ Bot ភ្លាមៗ
sudo systemctl start digitalshop

# ៥. ពិនិត្យមើលស្ថានភាពរបស់ Bot
sudo systemctl status digitalshop
```

> ប្រសិនបើឃើញពាក្យពណ៌បៃតង **`active (running)`** មានន័យថា Bot កំពុងដំណើរការ ២៤/៧ ដោយជោគជ័យ!

**ពាក្យបញ្ជាសំខាន់ៗសម្រាប់គ្រប់គ្រង Bot៖**
- មើល Log របស់ Bot ផ្ទាល់៖
  ```bash
  journalctl -u digitalshop -f
  ```
- បញ្ឈប់ Bot៖
  ```bash
  sudo systemctl stop digitalshop
  ```
- បើក Bot ឡើងវិញ (Restart)៖
  ```bash
  sudo systemctl restart digitalshop
  ```

---

#### វិធីទី ២៖ ប្រើប្រាស់ `screen` (វិធីសាស្ត្រលឿន និងសាមញ្ញ - Alternative)
ប្រសិនបើមិនចង់ប្រើ systemd អ្នកអាចប្រើ `screen` បាន៖
```bash
# ១. ដំឡើង screen
sudo apt install screen -y

# ២. បង្កើត session ថ្មីឈ្មោះ bot
screen -S bot

# ៣. បើក virtualenv និងដំណើរការ bot
source /root/digital-store-by-rongz/venv/bin/activate
python main.py
```
- ចុច `Ctrl + A` រួចចុច `D` ដើម្បីចាកចេញពី screen (Detached) ដោយ Bot នៅតែដើរដដែល។
- ប្រសិនបើចង់ចូលមកមើលវិញ៖
  ```bash
  screen -r bot
  ```

---

## 🔄 របៀប Update កូដនៅពេលក្រោយ (How to Update Code)
នៅពេលដែលអ្នកកែប្រែកូដនៅលើកុំព្យូទ័រ ហើយ Push ឡើង GitHub រួចរាល់ ដើម្បី Update នៅលើ VPS៖

```bash
cd /root/digital-store-by-rongz
git pull origin main

# Restart service ដើម្បីឱ្យ bot ដំណើរការកូដថ្មី
sudo systemctl restart digitalshop
```

---

🎉 **អបអរសាទរ!** Bot របស់អ្នកឥឡូវនេះដំណើរការ ២៤ ម៉ោង ៧ ថ្ងៃនៅលើ Apsara Hosting ប្រកបដោយសុវត្ថិភាព និងស្ថិរភាពខ្ពស់!

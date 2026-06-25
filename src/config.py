import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load .env if exists
load_dotenv()

class Config:
    """Centralized configuration for the application."""
    
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    
    # Database settings
    DB_NAME = str(DATA_DIR / "auctions.db")
    
    # API Settings
    # Pull from environment. Multiple keys should be comma-separated.
    GEMINI_API_KEYS: List[str] = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k.strip()]
    
    # Scraping Settings
    BASE_URL = "https://www.eauctionsindia.com"
    START_URL = "https://www.eauctionsindia.com/city/pune" # Default
    
    AVAILABLE_CITIES = {
        "Andaman and Nicobar Islands": {
            "South Andaman": "south-andaman",
        },
        "Andhra Pradesh": {
            "Amalapuram": "amalapuram", "Anakapalli": "anakapalli", "Anantapur": "anantapur",
            "Annamayya": "annamayya", "Bapatla": "bapatla", "Chittoor": "chittoor",
            "East Godavari": "east-godavari", "Eluru": "eluru", "Gudivada": "gudivada",
            "Guntur": "guntur", "Jaggaiahpet": "jaggaiahpet", "Kadapa": "kadapa",
            "Kakinada": "kakinada", "Konaseema": "konaseema", "Krishna": "krishna",
            "Kurnool": "kurnool", "Nandyal": "nandyal", "Nellore": "nellore",
            "NTR": "ntr", "Ongole": "ongole", "Palnadu": "palnadu",
            "Prakasam": "prakasam", "Rajahmundry": "rajahmundry",
            "Sri Sathya Sai District": "sri-sathya-sai-district", "Srikakulam": "srikakulam",
            "Thirupathi": "thirupathi", "Vijayawada": "vijayawada",
            "Visakhapatnam": "visakhapatnam", "Vizianagaram": "vizianagaram",
            "West Godavari": "west-godavari",
        },
        "Arunachal Pradesh": {
            "Itanagar": "itanagar", "Papumpare": "papumpare",
        },
        "Assam": {
            "Bongaigaon": "bongaigaon", "Cachar": "cachar", "Dhemaji": "dhemaji",
            "Golaghat": "golaghat", "Guwahati": "guwahati", "Jorhat": "jorhat",
            "Kamrup": "kamrup", "Nagaon": "nagaon", "Sonitpur": "sonitpur",
            "Tinsukia": "tinsukia",
        },
        "Bihar": {
            "Araria": "araria", "Aurangabad-Bihar": "aurangabad-bihar", "Banka": "banka",
            "Begusarai": "begusarai", "Bhagalpur": "bhagalpur", "Bhojpur": "bhojpur",
            "Buxar": "buxar", "Darbhanga": "darbhanga", "East Champaran": "east-champaran",
            "Gaya": "gaya", "Gopalganj": "gopalganj", "Jamui": "jamui",
            "Kaimur": "kaimur", "Kaitpura": "kaitpura", "Katihar": "katihar",
            "Khagaria": "khagaria", "Lakhisarai": "lakhisarai", "Madhepura": "madhepura",
            "Madhubani": "madhubani", "Munger": "munger", "Muzaffarpur": "muzaffarpur",
            "Nalanda": "nalanda", "Nawada": "nawada", "Patna": "patna",
            "Purnia": "purnia", "Purvi Champaran": "purvi-champaran", "Rohtas": "rohtas",
            "Saharsa": "saharsa", "Samastipur": "samastipur", "sapaul": "sapaul",
            "Saran": "saran", "Sheikhpura": "sheikhpura", "Sheohar": "sheohar",
            "Sitamarhi": "sitamarhi", "Siwan": "siwan", "Vaishali": "vaishali",
            "West Champaran": "west-champaran",
        },
        "Chhattisgarh": {
            "Bhatapara": "bhatapara", "Bilaspur": "bilaspur", "Champa": "champa",
            "Dhamtari": "dhamtari", "Durg": "durg",
            "Gaurela-Pendra-Marwahi": "gaurela-pendra-marwahi", "Korba": "korba",
            "Mahasamund": "mahasamund", "Mungeli": "mungeli", "Raigarh": "raigarh",
            "Raipur": "raipur", "Rajnandgaon": "rajnandgaon",
        },
        "Dadra and Nagar Haveli": {
            "Silvassa": "silvassa",
        },
        "Daman and Diu": {
            "Daman and Diu": "daman-and-diu",
        },
        "Delhi": {
            "New Delhi": "new-delhi", "Roop Nagar": "roop-nagar", "Shahdara": "shahdara",
        },
        "Goa": {
            "Goa": "goa", "Panaji": "panaji",
        },
        "Gujarat": {
            "Ahmedabad": "ahmedabad", "Amreli": "amreli", "Anand": "anand",
            "Anjar": "anjar", "Aravalli": "aravalli", "Banaskantha": "banaskantha",
            "Bharuch": "bharuch", "Bhavnagar": "bhavnagar", "Botad": "botad",
            "Chhotaudepur": "chhotaudepur", "Dahod": "dahod",
            "Dev Bhumi Dwarka": "dev-bhumi-dwarka", "Gandhinagar": "gandhinagar",
            "Gir Somnath": "gir-somnath", "Jamnagar": "jamnagar", "Junagadh": "junagadh",
            "Kheda": "kheda", "Kutch": "kutch", "Mahesan": "mahesan",
            "Mahisagar": "mahisagar", "Mehsana": "mehsana", "Morbi": "morbi",
            "Nadiad": "nadiad", "Narmada": "narmada", "Navsari": "navsari",
            "Panchmahal": "panchmahal", "Patan": "patan", "Porbandar": "porbandar",
            "Rajkot": "rajkot", "Sabarkantha": "sabarkantha", "Surat": "surat",
            "Surendranagar": "surendranagar", "Tapi": "tapi", "Vadodara": "vadodara",
            "Valsad": "valsad",
        },
        "Haryana": {
            "Ambala": "ambala", "Bhiwani": "bhiwani", "Charkhi Dadri": "charkhi-dadri",
            "Faridabad": "faridabad", "Fatehabad": "fatehabad", "Gurugram": "gurugram",
            "Hisar": "hisar", "Jhajjar": "jhajjar", "Jind": "jind",
            "Kaithal": "kaithal", "Karnal": "karnal", "Kurukshetra": "kurukshetra",
            "Mahendragarh": "mahendragarh", "Naraingarh": "naraingarh", "Palwal": "palwal",
            "Panchkula": "panchkula", "Panipat": "panipat", "Rewari": "rewari",
            "Rohtak": "rohtak", "Sirsa": "sirsa", "Sonipat": "sonipat",
            "Yamunanagar": "yamunanagar",
        },
        "Himachal Pradesh": {
            "Hamirpur": "hamirpur", "Kangra": "kangra", "Kullu": "kullu",
            "Mandi": "mandi", "Shimla": "shimla", "Sirmour": "sirmour",
            "Solan": "solan", "Una": "una",
        },
        "Jammu and Kashmir": {
            "Anantnag": "anantnag", "Baramulla": "baramulla", "Jammu": "jammu",
            "Kathua": "kathua", "Kulgam": "kulgam", "Srinagar": "srinagar",
        },
        "Jharkhand": {
            "Bokaro": "bokaro", "Deoghar": "deoghar", "Dhanbad": "dhanbad",
            "East Singhbhum": "east-singhbhum", "Hazaribagh": "hazaribagh",
            "Jamshedpur": "jamshedpur", "Mouza-Rasikpur": "mouza-rasikpur",
            "Ramgarh": "ramgarh", "Ranchi": "ranchi",
            "Seraikella Kharswan": "seraikella-kharswan",
            "West Singhbhum": "west-singhbhum",
        },
        "Karnataka": {
            "Anekal": "anekal", "Bagalkot": "bagalkot", "Ballari": "ballari",
            "Belagavi": "belagavi", "Bengaluru": "bengaluru", "Bidar": "bidar",
            "Bijapur": "bijapur", "Chamarajanagar": "chamarajanagar",
            "Channapatna": "channapatna", "Chikkaballapur": "chikkaballapur",
            "Chikmagalur": "chikmagalur", "Chitradurga": "chitradurga",
            "Dakshina Kannada": "dakshina-kannada", "Davanagere": "davanagere",
            "Dharwad": "dharwad", "Gadag": "gadag", "Gulbarga": "gulbarga",
            "Hassan": "hassan", "Haveri": "haveri", "Hospet": "hospet",
            "Hubballi": "hubballi", "Kalaburagi": "kalaburagi", "Kodagu": "kodagu",
            "Kolar": "kolar", "Koppal": "koppal", "Kudgi": "kudgi",
            "Kundagol": "kundagol", "Mandya": "mandya", "Mangalore": "mangalore",
            "Mysuru": "mysuru", "Raichur": "raichur", "Ramanagara": "ramanagara",
            "Shimoga": "shimoga", "Shivamogga": "shivamogga", "Tumkur": "tumkur",
            "Udupi": "udupi", "Uttara Kannada": "uttara-kannada",
            "Vijayanagar": "vijayanagar", "Vijayapura": "vijayapura", "Yadgir": "yadgir",
        },
        "Kerala": {
            "Alappuzha": "alappuzha", "Calicut": "calicut", "Ernakulam": "ernakulam",
            "Idukki": "idukki", "Kannur": "kannur", "Kasaragod": "kasaragod",
            "Kochi": "kochi", "Kollam": "kollam", "Kottarakkara": "kottarakkara",
            "Kottayam": "kottayam", "Kozhikode": "kozhikode", "Malappuram": "malappuram",
            "Palakkad": "palakkad", "Pathanamthitta": "pathanamthitta",
            "Sathamcotta": "sathamcotta", "Thiruvananthapuram": "thiruvananthapuram",
            "Thrissur": "thrissur", "Trichur": "trichur", "tripunithura": "tripunithura",
            "Trivandrum": "trivandrum", "Wayanad": "wayanad",
        },
        "Madhya Pradesh": {
            "Agar Malwa": "agar-malwa", "Alirajpur": "alirajpur", "Ashok Nagar": "ashok-nagar",
            "Balaghat": "balaghat", "Barbanki": "barbanki", "Barwani": "barwani",
            "Betul": "betul", "Bhind": "bhind", "Bhopal": "bhopal",
            "Burhanpur": "burhanpur", "Chhatarpur": "chhatarpur", "Chhindwara": "chhindwara",
            "Damoh": "damoh", "Dewas": "dewas", "Dhar": "dhar",
            "Guna": "guna", "Gwalior": "gwalior", "Harda": "harda",
            "Hoshangabad": "hoshangabad", "Indore": "indore", "Jabalpur": "jabalpur",
            "Jhabua": "jhabua", "Katni": "katni", "Khandwa": "khandwa",
            "Khargone": "khargone", "Mandasur": "mandasur", "Morena": "morena",
            "Narmadapuram": "narmadapuram", "Narsingpur": "narsingpur", "Neemuch": "neemuch",
            "Niwas": "niwas", "Raisen": "raisen", "Rajgarah": "rajgarah",
            "Ratlam": "ratlam", "Rewa": "rewa", "Sagar": "sagar",
            "Sehore": "sehore", "Seoni": "seoni", "Shahdol": "shahdol",
            "Shajapur": "shajapur", "Shivpuri": "shivpuri", "Singrauli": "singrauli",
            "Ujjain": "ujjain", "Vidisha": "vidisha", "Wardha": "wardha",
        },
        "Maharashtra": {
            "Ahmednagar": "ahmednagar", "Akola": "akola", "Amravati": "amravati",
            "Aurangabad": "aurangabad", "Beed": "beed", "Belapur": "belapur",
            "Bhandara": "bhandara", "Bhiwandi": "bhiwandi", "Buldhana": "buldhana",
            "Chandrapur": "chandrapur", "Dharashiv": "dharashiv", "Dhule": "dhule",
            "Dombivali (East)": "dombivali-east", "Gadchiroli": "gadchiroli",
            "Jalgaon": "jalgaon", "Jalna": "jalna", "Kalyan": "kalyan",
            "Khed": "khed", "Khopoli": "khopoli", "Kolhapur": "kolhapur",
            "Latur": "latur", "Manwath": "manwath", "Mumbai": "mumbai",
            "Nagpur": "nagpur", "Nalasopara": "nalasopara", "Nanded": "nanded",
            "Nandurbar": "nandurbar", "Nashik": "nashik", "Navi Mumbai": "navi-mumbai",
            "Osmanabad": "osmanabad", "Palghar": "palghar", "Panvel": "panvel",
            "Pune": "pune", "Raigad": "raigad", "Ratnagiri": "ratnagiri",
            "Sangli": "sangli", "Satara": "satara", "Sindhudurg": "sindhudurg",
            "Solapur": "solapur", "Thane": "thane", "Ulhasnagar": "ulhasnagar",
            "Virar": "virar", "Washim": "washim", "Yavatmal": "yavatmal",
        },
        "Manipur": {
            "Imphal East": "imphal-east", "Imphal West": "imphal-west", "Kakching": "kakching",
        },
        "Meghalaya": {
            "Shillong": "shillong",
        },
        "Mizoram": {
            "kolasib": "kolasib",
        },
        "Nagaland": {
            "Dimapur": "dimapur",
        },
        "Odisha": {
            "Angul": "angul", "Balasore": "balasore", "Bargarh": "bargarh",
            "Bhadrak": "bhadrak", "Bhubaneswar": "bhubaneswar", "Bolangir": "bolangir",
            "Cuttack": "cuttack", "Dhenakal": "dhenakal", "Ganjam": "ganjam",
            "Jagatsinghpur": "jagatsinghpur", "Jajpur": "jajpur",
            "Jharsuguda": "jharsuguda", "Kalahandi": "kalahandi",
            "Kendrapara": "kendrapara", "Keonjhar": "keonjhar", "Khordha": "khordha",
            "Khurda": "khurda", "Koraput": "koraput", "Mayurbhanj": "mayurbhanj",
            "Nayagarh": "nayagarh", "Nowrangpur": "nabarangpur", "Nuapada": "nuapada",
            "Puri": "puri", "Rayagada": "rayagada", "Sambalpur": "sambalpur",
            "Sundargarh": "sundargarh",
        },
        "Puducherry": {
            "Puducherry": "puducherry",
        },
        "Punjab": {
            "Amritsar": "amritsar", "Barnala": "barnala", "Bathinda": "bathinda",
            "Chandigarh": "chandigarh", "Faridkot": "faridkot",
            "Fatehgarh Sahib": "fatehgarh-sahib", "Fazilka": "fazilka",
            "Firozpur": "firozpur", "Gurdaspur": "gurdaspur", "Hoshiarpur": "hoshiarpur",
            "Jalandhar": "jalandhar", "Kapurthala": "kapurthala", "Ludhiana": "ludhiana",
            "Mansa": "mansa", "Moga": "moga", "Mohali": "mohali",
            "Muktsar": "muktsar", "Pathankot": "pathankot", "Patiala": "patiala",
            "Rupnagar": "rupnagar", "Sangrur": "sangrur", "SAS Nagar": "sas-nagar",
            "SBS Nagar": "sbs-nagar",
            "Shaheed Bhagat Singh Nagar": "shaheed-bhagat-singh-nagar",
            "Sri Muktsar Sahib": "sri-muktsar-sahib", "Tarn Taran": "tarn-taran",
        },
        "Rajasthan": {
            "Ajmer": "ajmer", "Alwar": "alwar", "ATOON KALAN": "atoon-kalan",
            "Banswara": "banswara", "Baran": "baran", "Barmer": "barmer",
            "Bharatpur": "bharatpur", "Bhilwara": "bhilwara", "Bikaner": "bikaner",
            "Bundi": "bundi", "Chittorgarh": "chittorgarh", "Churu": "churu",
            "Dausa": "dausa", "Dholpur": "dholpur", "Dungarpur": "dungarpur",
            "Gangapur": "gangapur", "Hanumangarh": "hanumangarh", "Jaipur": "jaipur",
            "Jalore": "jalore", "Jhalawar": "jhalawar", "Jhunjhunu": "jhunjhunu",
            "Jodhpur": "jodhpur", "Kota": "kota", "Nagaur": "nagaur",
            "Pali": "pali", "Pratapgarh": "pratapgarh", "Rajsamand": "rajsamand",
            "Sawai Madhopur": "sawai-madhopur", "Sikar": "sikar", "Sirohi": "sirohi",
            "Sri Ganganagar": "sri-ganganagar", "Sumerpur": "sumerpur", "Tonk": "tonk",
            "Udaipur": "udaipur",
        },
        "Sikkim": {
            "Gangtok": "gangtok",
        },
        "Tamil Nadu": {
            "Ariyalur": "ariyalur", "Chengalpattu": "chengalpattu", "Chennai": "chennai",
            "Chidambaram": "chidambaram", "Coimbatore": "coimbatore", "Cuddalore": "cuddalore",
            "Dharmapuri": "dharmapuri", "Dindigul": "dindigul", "Erode": "erode",
            "Illupur Taluk": "illupur-taluk", "Kallakurichi": "kallakurichi",
            "Kanchipuram": "kanchipuram", "Kanyakumari": "kanyakumari",
            "Karaikudi": "karaikudi", "Karur": "karur", "Krishnagiri": "krishnagiri",
            "Kumbakonam": "kumbakonam", "Madurai": "madurai",
            "Mayiladuthurai": "mayiladuthurai", "Nagapattinam": "nagapattinam",
            "Namakkal": "namakkal", "Nilgiris": "nilgiris", "Palani": "palani",
            "Palayamkottai": "palayamkottai", "Pattukottai": "pattukottai",
            "Perambalur": "perambalur", "Periyakulam": "periyakulam",
            "Pudukkottai": "pudukkottai", "Pudukkottai District": "pudukkottai-district",
            "Ramanathapuram": "ramanathapuram", "Ranipet": "ranipet", "Salem": "salem",
            "Sivaganga": "sivaganga", "Tenkasi": "tenkasi", "Thanjavur": "thanjavur",
            "Theni": "theni", "Thiruchirapalli": "thiruchirapalli",
            "Thiruvarur": "thiruvarur", "Thoothukudi": "thoothukudi",
            "Tindivanam": "tindivanam", "Tiruchirappalli": "tiruchirappalli",
            "Tirunelveli": "tirunelveli", "Tirupathur": "tirupathur",
            "Tiruppur": "tiruppur", "Tiruvallur": "tiruvallur",
            "Tiruvannamalai": "tiruvannamalai", "Tuticorin": "tuticorin",
            "Udumalaipet": "udumalaipet", "Vellore": "vellore",
            "Villupuram": "villupuram", "Virudhunagar": "virudhunagar",
        },
        "Telangana": {
            "Adilabad": "adilabad", "Bhadradri Kothagudem": "bhadradri-kothagudem",
            "Hyderabad": "hyderabad", "Jagtial": "jagtial", "Jangaon": "jangaon",
            "Jayashankar Bhupalpally": "jayashankar-bhupalpally",
            "Jogulamba Gadwal": "jogulamba-gadwal", "Kamareddy": "kamareddy",
            "Karimnagar": "karimnagar", "Khammam": "khammam",
            "Mahabubabad": "mahabubabad", "Mahabubnagar": "mahabubnagar",
            "Mancherial": "mancherial", "Medak": "medak",
            "Medchal-Malkajgiri": "medchal-malkajgiri", "Mulugu": "mulugu",
            "Nagarkurnool": "nagarkurnool", "Nalgonda": "nalgonda", "Nirmal": "nirmal",
            "Nizamabad": "nizamabad", "Peddapalli": "peddapalli",
            "Rajanna Sircilla": "rajanna-sircilla", "Ranga Reddy": "ranga-reddy",
            "Sangareddy": "sangareddy", "Secunderabad": "secunderabad",
            "Siddipet": "siddipet", "Suryapet": "suryapet", "Vikarabad": "vikarabad",
            "Wanaparthy": "wanaparthy", "Warangal": "warangal",
            "Yadadri Bhuvanagiri": "yadadri-bhuvanagiri",
        },
        "Tripura": {
            "Khowai": "khowai", "West Tripura": "west-tripura",
        },
        "Uttar Pradesh": {
            "Agra": "agra", "Aligarh": "aligarh", "Allahabad": "allahabad",
            "Ambedkar Nagar": "ambedkar-nagar", "Amethi": "amethi", "Amroha": "amroha",
            "Auraiya": "auraiya", "Ayodhya": "ayodhya", "Azamgarh": "azamgarh",
            "Baghpat": "baghpat", "Bahraich": "bahraich", "Ballia": "ballia",
            "Balrampur": "balrampur", "Banda": "banda", "Barabanki": "barabanki",
            "Bareilly": "bareilly", "Basti": "basti", "Bhadohi": "bhadohi",
            "Bijnor": "bijnor", "BUDAUN": "budaun", "Bulandshahr": "bulandshahr",
            "Chandauli": "chandauli", "Chitrakoot": "chitrakoot", "Deoria": "deoria",
            "Etah": "etah", "Etawah": "etawah", "Faizabad": "faizabad",
            "Farrukhabad": "farrukhabad", "Fatehpur": "fatehpur", "Firozabad": "firozabad",
            "Gautam Buddha Nagar": "gautam-buddha-nagar", "Ghaziabad": "ghaziabad",
            "Ghazipur": "ghazipur", "Gonda": "gonda", "Gorakhpur": "gorakhpur",
            "Hapur": "hapur", "Hardoi": "hardoi", "Hathras": "hathras",
            "Jaunpur": "jaunpur", "Jhansi": "jhansi", "Kanpur": "kanpur",
            "Kasganj": "kasganj", "kishunpur": "kishunpur", "Kushinagar": "kushinagar",
            "Lakhimpur Kheri": "lakhimpur-kheri", "Lalitpur": "lalitpur",
            "Lucknow": "lucknow", "Maharajganj": "maharajganj", "Mainpuri": "mainpuri",
            "Mathura": "mathura", "Mau": "mau", "Meerut": "meerut",
            "Mirzapur": "mirzapur", "Moradabad": "moradabad",
            "Muzaffarnagar": "muzaffarnagar", "Noida": "noida", "Pilibhit": "pilibhit",
            "Prayagraj": "prayagraj", "Raebareli": "raebareli", "Rampur": "rampur",
            "Saharanpur": "saharanpur", "Sambhal": "sambhal",
            "Sant Kabir Nagar": "sant-kabir-nagar", "Satna": "satna",
            "Shahjahanpur": "shahjahanpur", "Siddharthnagar": "siddharthnagar",
            "Sitapur": "sitapur", "Sonbhadra": "sonbhadra", "Sultanpur": "sultanpur",
            "Unnao": "unnao", "Varanasi": "varanasi",
        },
        "Uttarakhand": {
            "Dehradun": "dehradun", "Haridwar": "haridwar", "Kashipur": "kashipur",
            "Kichha": "kichha", "Nainital": "nainital", "Pauri Garhwal": "pauri-garhwal",
            "Pithoragarh": "pithoragarh", "Udham Singh Nagar": "udham-singh-nagar",
        },
        "West Bengal": {
            "Alipurduar": "alipurduar", "Asansol": "asansol", "Bankura": "bankura",
            "Birbhum": "birbhum", "Burdwan": "burdwan", "Cooch Behar": "cooch-behar",
            "Dakshin Dinajpur": "dakshin-dinajpur", "Darjeeling": "darjeeling",
            "Durgapur": "durgapur", "East Medinipore": "east-medinipore",
            "Hooghly": "hooghly", "Howrah": "howrah", "Jalpaiguri": "jalpaiguri",
            "Jhargram": "jhargram", "Kolkata": "kolkata", "Malda": "malda",
            "Murshidabad": "murshidabad", "Nadia": "nadia",
            "North 24 Parganas": "north-24-parganas",
            "North Dinajpur": "north-dinajpur",
            "Paschim Bardhaman": "paschim-bardhaman",
            "Paschim Medinipur": "paschim-medinipur",
            "Purba Bardhaman": "purba-bardhaman",
            "Purba Medinipur": "purba-medinipur",
            "Purulia": "purulia", "Siliguri": "siliguri",
            "South 24 Parganas": "south-24-parganas",
            "West Midnapore": "west-midnapore",
        },
    }
    
    # Scraper Headers
    HEADERS = {
        "User-Agent": os.getenv(
            "SCRAPER_USER_AGENT",
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.eauctionsindia.com/"
    }

    # Optional Cloudflare cookie string copied from browser after verification
    # Example: "cf_clearance=...; __cf_bm=..."
    EAUCTIONS_COOKIE = os.getenv("EAUCTIONS_COOKIE", "").strip()
    
    # Cache Settings
    MARKET_RATE_CACHE_FILE = str(DATA_DIR / "property_enriched_data.json")
    
    # AI Model Settings
    GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")

    # Security Settings
    JWT_SECRET = os.getenv("JWT_SECRET", "auction_iq_secure_secret_998811")

# Global config instance
config = Config()

# Precomputed city → state lookup (built once at import)
CITY_TO_STATE = {
    city: state
    for state, cities in config.AVAILABLE_CITIES.items()
    for city in cities
}

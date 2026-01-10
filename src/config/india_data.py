"""
India-specific data: states, districts, and government departments.
Used for location parsing and department routing.
"""

# Indian States and Union Territories
INDIAN_STATES_UTS = {
    "Andhra Pradesh": {"type": "state", "code": "AP"},
    "Arunachal Pradesh": {"type": "state", "code": "AR"},
    "Assam": {"type": "state", "code": "AS"},
    "Bihar": {"type": "state", "code": "BR"},
    "Chhattisgarh": {"type": "state", "code": "CG"},
    "Goa": {"type": "state", "code": "GA"},
    "Gujarat": {"type": "state", "code": "GJ"},
    "Haryana": {"type": "state", "code": "HR"},
    "Himachal Pradesh": {"type": "state", "code": "HP"},
    "Jharkhand": {"type": "state", "code": "JH"},
    "Karnataka": {"type": "state", "code": "KA"},
    "Kerala": {"type": "state", "code": "KL"},
    "Madhya Pradesh": {"type": "state", "code": "MP"},
    "Maharashtra": {"type": "state", "code": "MH"},
    "Manipur": {"type": "state", "code": "MN"},
    "Meghalaya": {"type": "state", "code": "ML"},
    "Mizoram": {"type": "state", "code": "MZ"},
    "Nagaland": {"type": "state", "code": "NL"},
    "Odisha": {"type": "state", "code": "OD"},
    "Punjab": {"type": "state", "code": "PB"},
    "Rajasthan": {"type": "state", "code": "RJ"},
    "Sikkim": {"type": "state", "code": "SK"},
    "Tamil Nadu": {"type": "state", "code": "TN"},
    "Telangana": {"type": "state", "code": "TS"},
    "Tripura": {"type": "state", "code": "TR"},
    "Uttar Pradesh": {"type": "state", "code": "UP"},
    "Uttarakhand": {"type": "state", "code": "UK"},
    "West Bengal": {"type": "state", "code": "WB"},
    "Andaman and Nicobar Islands": {"type": "ut", "code": "AN"},
    "Chandigarh": {"type": "ut", "code": "CH"},
    "Dadra and Nagar Haveli and Daman and Diu": {"type": "ut", "code": "DH"},
    "Delhi": {"type": "ut", "code": "DL"},
    "Jammu and Kashmir": {"type": "ut", "code": "JK"},
    "Ladakh": {"type": "ut", "code": "LA"},
    "Lakshadweep": {"type": "ut", "code": "LD"},
    "Puducherry": {"type": "ut", "code": "PY"},
}

# Major Maharashtra Cities (for location parsing)
MAJOR_INDIAN_CITIES = {
    "Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Solapur",
    "Thane", "Kalyan", "Vasai", "Navi Mumbai", "Amravati", "Kolhapur",
    "Sangli", "Jalgaon", "Akola", "Latur", "Dhule", "Ahmednagar",
    "Ichalkaranji", "Jalna", "Bhusawal", "Panvel", "Satara", "Beed",
    "Yavatmal", "Kamptee", "Gondia", "Barshi", "Achalpur", "Osmanabad",
}

# Government Department Categories (Maharashtra-specific)
INDIAN_DEPARTMENTS = {
    "bmc": {
        "name": "Brihanmumbai Municipal Corporation (BMC)",
        "jurisdiction": "city",
        "city_specific": ["Mumbai"],
        "state_specific": ["Maharashtra"],
        "handles": [
            "water supply", "sewage", "garbage", "street lights",
            "road maintenance", "building permits", "property tax",
            "park maintenance", "public toilets", "drainage",
            "municipal services", "civic amenities", "potholes",
            "street cleaning", "solid waste management"
        ]
    },
    "pune_municipal": {
        "name": "Pune Municipal Corporation (PMC)",
        "jurisdiction": "city",
        "city_specific": ["Pune"],
        "state_specific": ["Maharashtra"],
        "handles": [
            "water supply", "sewage", "garbage", "street lights",
            "road maintenance", "building permits", "property tax",
            "park maintenance", "public toilets", "drainage"
        ]
    },
    "nagpur_municipal": {
        "name": "Nagpur Municipal Corporation (NMC)",
        "jurisdiction": "city",
        "city_specific": ["Nagpur"],
        "state_specific": ["Maharashtra"],
        "handles": [
            "water supply", "sewage", "garbage", "street lights",
            "road maintenance", "building permits", "property tax",
            "park maintenance", "public toilets", "drainage"
        ]
    },
    "municipal": {
        "name": "Municipal Corporation",
        "jurisdiction": "city",
        "state_specific": ["Maharashtra"],
        "handles": [
            "water supply", "sewage", "garbage", "street lights",
            "road maintenance", "building permits", "property tax",
            "park maintenance", "public toilets", "drainage"
        ]
    },
    "maharashtra_police": {
        "name": "Maharashtra Police",
        "jurisdiction": "state",
        "state_specific": ["Maharashtra"],
        "handles": [
            "crime", "law enforcement", "traffic violations", "security",
            "harassment", "violence", "theft", "assault", "fraud",
            "cybercrime", "domestic violence", "FIR", "complaint",
            "police", "law and order", "safety"
        ]
    },
    "mumbai_police": {
        "name": "Mumbai Police",
        "jurisdiction": "city",
        "city_specific": ["Mumbai"],
        "state_specific": ["Maharashtra"],
        "handles": [
            "crime", "law enforcement", "traffic violations", "security",
            "harassment", "violence", "theft", "assault", "fraud",
            "cybercrime", "domestic violence", "FIR", "complaint"
        ]
    },
    "fire": {
        "name": "Maharashtra Fire Department",
        "jurisdiction": "city",
        "state_specific": ["Maharashtra"],
        "handles": [
            "fire", "fire safety", "fire hazard", "emergency",
            "rescue", "firefighting", "smoke", "burning",
            "fire brigade", "fire station"
        ]
    },
    "maharashtra_pwd": {
        "name": "Maharashtra Public Works Department (PWD)",
        "jurisdiction": "state",
        "state_specific": ["Maharashtra"],
        "handles": [
            "state highways", "state buildings", "infrastructure",
            "bridge maintenance", "government quarters", "roads",
            "construction", "public infrastructure"
        ]
    },
    "msrtc": {
        "name": "Maharashtra State Road Transport Corporation (MSRTC)",
        "jurisdiction": "state",
        "state_specific": ["Maharashtra"],
        "handles": [
            "bus services", "transport", "state transport", "ST bus",
            "road safety", "public transport", "bus routes"
        ]
    },
    "maharashtra_health": {
        "name": "Maharashtra Health Department",
        "jurisdiction": "state",
        "state_specific": ["Maharashtra"],
        "handles": [
            "government hospitals", "public health", "disease control",
            "vaccination", "health camps", "medical facilities",
            "healthcare", "hospital services"
        ]
    },
    "maharashtra_education": {
        "name": "Maharashtra Education Department",
        "jurisdiction": "state",
        "state_specific": ["Maharashtra"],
        "handles": [
            "government schools", "education policy", "teacher issues",
            "school infrastructure", "scholarships", "education",
            "schools", "colleges"
        ]
    },
    "central_railways": {
        "name": "Indian Railways",
        "jurisdiction": "national",
        "handles": [
            "train services", "railway stations", "ticket issues",
            "railway infrastructure", "railway safety"
        ]
    },
    "central_post": {
        "name": "India Post",
        "jurisdiction": "national",
        "handles": [
            "postal services", "mail delivery", "post office",
            "parcel services"
        ]
    },
    "mseb": {
        "name": "Maharashtra State Electricity Board (MSEB)",
        "jurisdiction": "state",
        "state_specific": ["Maharashtra"],
        "handles": [
            "electricity supply", "power cuts", "billing issues",
            "electrical safety", "meter issues", "power",
            "electricity", "power supply", "load shedding"
        ]
    },
    "central_telecom": {
        "name": "Telecom Regulatory Authority",
        "jurisdiction": "national",
        "handles": [
            "telecom services", "internet issues", "mobile services",
            "telecom complaints"
        ]
    },
    "maharashtra_environment": {
        "name": "Maharashtra Environment Department",
        "jurisdiction": "state",
        "state_specific": ["Maharashtra"],
        "handles": [
            "pollution", "waste management", "environmental clearance",
            "air quality", "water quality", "environment",
            "pollution control"
        ]
    },
    "rural_development": {
        "name": "Rural Development Department",
        "jurisdiction": "state",
        "handles": [
            "rural infrastructure", "village development", "panchayat issues",
            "rural schemes", "agricultural support"
        ]
    },
}

# Issue Category Keywords (for complaint understanding)
ISSUE_CATEGORIES = {
    "infrastructure": ["road", "bridge", "building", "construction", "repair", "maintenance"],
    "utilities": ["water", "electricity", "power", "gas", "supply", "cut", "outage"],
    "sanitation": ["garbage", "waste", "sewage", "drainage", "toilet", "cleanliness"],
    "transport": ["bus", "train", "traffic", "road", "vehicle", "transport", "parking"],
    "health": ["hospital", "health", "medical", "doctor", "medicine", "treatment"],
    "education": ["school", "education", "teacher", "student", "college", "university"],
    "safety": ["crime", "police", "security", "safety", "harassment", "violence"],
    "environment": ["pollution", "air", "water", "noise", "environment", "waste"],
    "governance": ["corruption", "bribery", "delay", "red tape", "bureaucracy"],
    "other": []  # Default category
}


def get_state_code(state_name: str) -> str:
    """Get state/UT code from state name."""
    state_name_normalized = state_name.strip()
    for state, data in INDIAN_STATES_UTS.items():
        if state.lower() == state_name_normalized.lower():
            return data["code"]
    return "UNKNOWN"


def get_department_for_issue(issue_type: str, location: dict) -> str:
    """
    Determine the appropriate Maharashtra department for an issue type.
    
    Args:
        issue_type: Category of the issue
        location: Dictionary with state, city, etc.
    
    Returns:
        Department key
    """
    issue_lower = issue_type.lower()
    state = location.get("state", "").lower()
    city = location.get("city", "").lower()
    
    # Check each department's handles with Maharashtra-specific routing
    for dept_key, dept_info in INDIAN_DEPARTMENTS.items():
        # Check if department is state-specific and matches
        if dept_info.get("state_specific"):
            if "maharashtra" not in state:
                continue
        
        # Check if department is city-specific
        if dept_info.get("city_specific"):
            if city not in [c.lower() for c in dept_info["city_specific"]]:
                continue
        
        # Check if issue matches department handles
        for keyword in dept_info["handles"]:
            if keyword in issue_lower:
                return dept_key
    
    # Maharashtra-specific defaults
    if city == "mumbai":
        return "bmc"
    elif city == "pune":
        return "pune_municipal"
    elif city == "nagpur":
        return "nagpur_municipal"
    elif location.get("city"):
        return "municipal"
    
    # Default to Maharashtra PWD for state-level issues
    if state == "maharashtra" or not state:
        return "maharashtra_pwd"
    
    return "municipal"  # Ultimate default


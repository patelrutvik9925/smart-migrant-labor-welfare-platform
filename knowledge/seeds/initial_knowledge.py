"""
Knowledge base seed data — verified official government sources.
This script populates the knowledge_records table with initial verified content.
Only official government sources are used.
"""

KNOWLEDGE_SEEDS = [
    # ── WELFARE SCHEMES ──────────────────────────────────────────────────────
    {
        "version_number": "1.0.0",
        "category": "welfare",
        "title": "e-Shram Portal — Unorganised Workers Registration",
        "content": (
            "The e-Shram portal (eshram.gov.in) is the national database of unorganised workers "
            "maintained by the Ministry of Labour and Employment, Government of India. "
            "Migrant workers, construction workers, domestic workers, and other unorganised sector "
            "workers can register on the portal. Benefits include: UAN card, accident insurance "
            "coverage of Rs. 2 lakh under PM Suraksha Bima Yojana, and eligibility tracking for "
            "various social security schemes. Registration is free. Required: Aadhaar card linked "
            "with mobile number. Portal: https://eshram.gov.in"
        ),
        "source_name": "Ministry of Labour and Employment, Government of India — e-Shram Portal",
        "source_url": "https://eshram.gov.in",
        "source_type": "official_website",
        "tags": ["eshram", "registration", "unorganised workers", "migrant", "insurance"],
        "structured_data": {
            "eligibility": {
                "age_min": 16,
                "age_max": 59,
                "sector": "unorganised",
                "excluded": ["EPFO members", "ESIC members", "NPS members", "income tax payers"]
            },
            "documents_required": ["Aadhaar card", "Aadhaar-linked mobile number", "Bank account details"],
            "application_steps": [
                "Visit eshram.gov.in",
                "Click 'Register on e-Shram'",
                "Enter Aadhaar-linked mobile number",
                "Enter OTP",
                "Fill personal and employment details",
                "Download UAN card"
            ],
            "benefits": ["UAN card", "Rs. 2 lakh accident insurance", "Social security scheme eligibility"]
        },
    },
    {
        "version_number": "1.0.0",
        "category": "welfare",
        "title": "PM Suraksha Bima Yojana (PMSBY) — Accident Insurance",
        "content": (
            "PM Suraksha Bima Yojana provides accidental death and disability insurance. "
            "Premium: Rs. 20 per year. Coverage: Rs. 2 lakh for accidental death or total permanent "
            "disability; Rs. 1 lakh for partial permanent disability. Eligibility: Savings bank "
            "account holders aged 18-70 years. Auto-debit from bank account. "
            "Source: Ministry of Finance, Government of India."
        ),
        "source_name": "Ministry of Finance, Government of India — PMSBY",
        "source_url": "https://financialservices.gov.in/insurance-divisions/Government-Sponsored-Socially-Oriented-Insurance-Schemes/Pradhan-Mantri-Suraksha-Bima-Yojana(PMSBY)",
        "source_type": "official_website",
        "tags": ["PMSBY", "accident insurance", "insurance", "welfare"],
        "structured_data": {
            "eligibility": {"age_min": 18, "age_max": 70, "requirement": "Savings bank account"},
            "premium": {"amount": 20, "currency": "INR", "period": "annual"},
            "coverage": {"accidental_death": 200000, "total_disability": 200000, "partial_disability": 100000},
            "documents_required": ["Savings bank account", "Aadhaar card"],
        },
    },
    {
        "version_number": "1.0.0",
        "category": "welfare",
        "title": "Building and Other Construction Workers (BOCW) Welfare Scheme — Gujarat",
        "content": (
            "Construction workers in Gujarat can register with the Gujarat Building and Other "
            "Construction Workers Welfare Board. Benefits include: education assistance for children, "
            "maternity benefit, medical assistance, accident benefit, pension, housing loan assistance, "
            "and skill development. Workers must be engaged in building/construction work for at least "
            "90 days in the preceding 12 months. Registration fee is nominal. "
            "Apply at: Labour and Employment Department, Gujarat."
        ),
        "source_name": "Labour and Employment Department, Gujarat — BOCW Board",
        "source_url": "https://labour.gujarat.gov.in",
        "source_type": "official_website",
        "tags": ["BOCW", "construction", "Gujarat", "welfare board", "registration"],
        "structured_data": {
            "eligibility": {
                "occupation": "construction worker",
                "state": "Gujarat",
                "work_days_required": 90,
                "period": "12 months"
            },
            "benefits": [
                "Education assistance", "Maternity benefit", "Medical assistance",
                "Accident benefit", "Pension", "Housing loan assistance", "Skill development"
            ],
            "documents_required": ["Age proof", "Work certificate from contractor", "Residence proof", "Bank account"],
        },
    },

    # ── WAGES ────────────────────────────────────────────────────────────────
    {
        "version_number": "1.0.0",
        "category": "wage",
        "title": "Minimum Wages — Gujarat State (Selected Occupations)",
        "content": (
            "Minimum wages in Gujarat are notified by the Labour and Employment Department, "
            "Government of Gujarat under the Minimum Wages Act, 1948. "
            "NOTE: Exact figures change periodically — always verify at https://labour.gujarat.gov.in "
            "for the latest notification. "
            "General guidance: Unskilled workers typically receive the lowest scheduled rate; "
            "Semi-skilled workers receive a higher rate; Skilled workers receive the highest rate. "
            "Workers earning below the applicable minimum wage should contact the Labour Inspector "
            "for their area. Complaints can be filed at the nearest Labour Office."
        ),
        "source_name": "Labour and Employment Department, Government of Gujarat — Minimum Wages",
        "source_url": "https://labour.gujarat.gov.in/minimum-wages",
        "source_type": "official_website",
        "tags": ["minimum wages", "Gujarat", "unskilled", "skilled", "semi-skilled"],
        "structured_data": {
            "authority": "Labour and Employment Department, Government of Gujarat",
            "act": "Minimum Wages Act, 1948",
            "categories": ["unskilled", "semi-skilled", "skilled", "highly skilled"],
            "verification_required": True,
            "complaint_channel": "Local Labour Office / Labour Inspector",
        },
    },
    {
        "version_number": "1.0.0",
        "category": "wage",
        "title": "National Floor Level Minimum Wage",
        "content": (
            "The Government of India recommends a National Floor Level Minimum Wage. "
            "State governments are expected to fix minimum wages at or above this floor. "
            "Workers can check current state-wise minimum wages at the official labour ministry portal: "
            "https://labour.gov.in/wagecell.php "
            "The Minimum Wages Act, 1948 requires employers to pay at least the applicable scheduled minimum wage."
        ),
        "source_name": "Ministry of Labour and Employment, Government of India — Minimum Wages",
        "source_url": "https://labour.gov.in/wagecell.php",
        "source_type": "official_website",
        "tags": ["national floor wage", "minimum wages", "India", "labour ministry"],
        "structured_data": {
            "authority": "Ministry of Labour and Employment, Government of India",
            "act": "Minimum Wages Act, 1948",
            "portal": "https://labour.gov.in/wagecell.php",
        },
    },

    # ── SAFETY / LABOR ───────────────────────────────────────────────────────
    {
        "version_number": "1.0.0",
        "category": "safety",
        "title": "Inter-State Migrant Workmen Act, 1979 — Worker Rights",
        "content": (
            "The Inter-State Migrant Workmen (Regulation of Employment and Conditions of Service) Act, 1979 "
            "provides protections for inter-state migrant workers. Key rights: "
            "1. Every contractor employing migrant workers must register with the licensing authority. "
            "2. Workers must be issued a passbook with details of employment and wages. "
            "3. Equal wages as local workers for same/similar work. "
            "4. Suitable accommodation during employment. "
            "5. Free medical facilities. "
            "6. Protective clothing in hazardous occupations. "
            "7. Displacement allowance equal to 50% of monthly wages. "
            "8. Journey allowance for travel to and from home state. "
            "Violations can be reported to the nearest Labour Commissioner office."
        ),
        "source_name": "Ministry of Labour and Employment, Government of India — ISMW Act 1979",
        "source_url": "https://labour.gov.in/inter-state-migrant-workmen",
        "source_type": "official_website",
        "tags": ["ISMW Act", "migrant workers", "rights", "inter-state", "contractor"],
        "structured_data": {
            "act": "Inter-State Migrant Workmen Act, 1979",
            "rights": [
                "Equal wages", "Accommodation", "Free medical facilities",
                "Protective clothing", "Displacement allowance", "Journey allowance", "Passbook"
            ],
            "complaint_channel": "Labour Commissioner Office",
        },
    },
    {
        "version_number": "1.0.0",
        "category": "safety",
        "title": "Occupational Safety, Health and Working Conditions Code, 2020",
        "content": (
            "The Occupational Safety, Health and Working Conditions Code, 2020 consolidates and "
            "amends laws relating to occupational safety, health, and working conditions. "
            "Key provisions for migrant workers: "
            "Maximum 8 working hours per day, 48 hours per week. "
            "Overtime: maximum 125 hours in any quarter; overtime paid at twice the regular wage rate. "
            "Weekly rest day mandatory. "
            "Safe working environment is the employer's statutory duty. "
            "Workers have the right to refuse unsafe work without penalty. "
            "Women workers have the right to work in safe conditions."
        ),
        "source_name": "Ministry of Labour and Employment, Government of India — OSH Code 2020",
        "source_url": "https://labour.gov.in/osh-code",
        "source_type": "official_website",
        "tags": ["safety", "working hours", "overtime", "OSH Code", "rights"],
        "structured_data": {
            "act": "Occupational Safety Health and Working Conditions Code 2020",
            "max_hours_per_day": 8,
            "max_hours_per_week": 48,
            "max_overtime_per_quarter": 125,
            "overtime_rate": "2x regular wage",
            "weekly_rest": True,
        },
    },
    {
        "version_number": "1.0.0",
        "category": "safety",
        "title": "Child Labour Prohibition — Laws and Reporting",
        "content": (
            "Child labour is prohibited in India under the Child and Adolescent Labour (Prohibition "
            "and Regulation) Act, 1986, amended in 2016. "
            "Children below 14 years: completely prohibited from employment in any occupation/process. "
            "Adolescents (14-18 years): prohibited from hazardous occupations. "
            "Penalty for employers: imprisonment of 6 months to 2 years and/or fine. "
            "To report child labour: Call 1098 (Childline India Foundation — 24x7 free helpline) "
            "or contact the local District Magistrate / Labour Department."
        ),
        "source_name": "Ministry of Labour and Employment, Government of India — Child Labour",
        "source_url": "https://labour.gov.in/child-labour",
        "source_type": "official_website",
        "tags": ["child labour", "prohibition", "reporting", "childline", "1098"],
        "structured_data": {
            "helpline": "1098",
            "helpline_name": "Childline India Foundation",
            "availability": "24x7",
            "age_limit_any_work": 14,
            "age_limit_hazardous": 18,
        },
    },
    {
        "version_number": "1.0.0",
        "category": "safety",
        "title": "National Helplines for Migrant Workers",
        "content": (
            "Key helplines for migrant workers in distress: "
            "1. National Labour Helpline: 1800-11-2244 (toll-free) "
            "2. Childline India: 1098 (24x7, child labour and abuse) "
            "3. Women Helpline: 181 (for women in distress) "
            "4. Police: 100 "
            "5. Ambulance: 108 "
            "6. Pravasi Bharatiya Sahayata Kendra (PBSK) — NRK-specific assistance "
            "Workers facing trafficking, forced labour, or abuse should contact police (100) "
            "and the Anti-Human Trafficking Unit of the nearest police station."
        ),
        "source_name": "Ministry of Labour and Employment, Government of India — Helplines",
        "source_url": "https://labour.gov.in",
        "source_type": "official_website",
        "tags": ["helpline", "emergency", "labour", "police", "childline", "women"],
        "structured_data": {
            "helplines": {
                "labour": "1800-11-2244",
                "childline": "1098",
                "women": "181",
                "police": "100",
                "ambulance": "108",
            }
        },
    },
]

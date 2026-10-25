"""Company careers sites scanned every day. Each entry: (name, fetcher, args).
A source that errors is reported on the board and skipped; the rest still run.
To add a company, add one line here.
"""
import fetchers as F

WORKDAY = [
    # company,                  host,                                   tenant,            site
    ("NVIDIA",                  "nvidia.wd5.myworkdayjobs.com",         "nvidia",          "NVIDIAExternalCareerSite"),
    ("Intel",                   "intel.wd1.myworkdayjobs.com",          "intel",           "External"),
    ("Marvell",                 "marvell.wd1.myworkdayjobs.com",        "marvell",         "MarvellCareers"),
    ("Micron",                  "micron.wd1.myworkdayjobs.com",         "micron",          "External"),
    ("Analog Devices",          "analogdevices.wd1.myworkdayjobs.com",  "analogdevices",   "External"),
    ("Broadcom",                "broadcom.wd1.myworkdayjobs.com",       "broadcom",        "External_Career"),
    ("Samsung Semiconductor",   "sec.wd3.myworkdayjobs.com",            "sec",             "Samsung_Careers"),
    ("Hewlett Packard Enterprise", "hpe.wd5.myworkdayjobs.com",         "hpe",             "jobsathpe"),
    ("GlobalFoundries",         "globalfoundries.wd1.myworkdayjobs.com", "globalfoundries", "External"),
    ("Cadence",                 "cadence.wd1.myworkdayjobs.com",        "cadence",         "External_Careers"),
    ("Altera",                  "altera.wd1.myworkdayjobs.com",         "altera",          "altera"),
    ("SiFive",                  "sifive.wd1.myworkdayjobs.com",         "sifive",          "sifivecareers"),
    ("NXP",                     "nxp.wd3.myworkdayjobs.com",            "nxp",             "careers"),
    ("Ambarella",               "ambarella.wd108.myworkdayjobs.com",    "ambarella",       "ambarella"),
    ("Ciena",                   "ciena.wd5.myworkdayjobs.com",          "ciena",           "Careers"),
]

GREENHOUSE = [
    ("Astera Labs", "asteraearlycareer2027"),
    ("Tenstorrent", "tenstorrentuniversity"),
    ("Tenstorrent", "tenstorrent"),
    ("Groq", "groq"),
    ("Lightmatter", "lightmatter"),
    ("SambaNova", "sambanovasystems"),
    ("Samsung Research America", "samsungresearchamericainternship"),
    ("Ayar Labs", "ayarlabs"),
    ("xAI", "xai"),
    ("Anthropic", "anthropic"),
]

ASHBY = [
    ("Etched", "Etched"),
    ("d-Matrix", "d-Matrix"),
    ("MatX", "matx"),
    ("Cerebras", "cerebras"),
    ("OpenAI", "openai"),
]

SOURCES = []
for company, host, tenant, site in WORKDAY:
    SOURCES.append((company, F.workday, (company, host, tenant, site)))
SOURCES += [
    ("Qualcomm", F.eightfold, ("Qualcomm", "careers.qualcomm.com", "qualcomm.com")),
    ("Microsoft", F.eightfold, ("Microsoft", "apply.careers.microsoft.com", "microsoft.com")),
    ("AMD", F.amd, ()),
    ("Amazon", F.amazon, ([("intern", "hardware-development"), ("ASIC intern", None), ("silicon intern", None),
                           ("Annapurna intern", None), ("FPGA intern", None), ("hardware intern 2027", None)],)),
    ("Google", F.google, ([("hardware", "United States"), ("silicon", "United States"), ("ASIC", "United States"),
                           ("TPU", "United States"), ("", "Taiwan")],)),
    ("Apple", F.apple, ()),
    ("Meta", F.meta, (["ASIC intern", "silicon intern", "hardware intern", "design verification intern"],)),
    ("Tesla", F.tesla, ()),
    ("Arm", F.arm, ()),
    ("Texas Instruments", F.oracle_hcm, ("Texas Instruments", "edbz.fa.us2.oraclecloud.com", "CX")),
    ("onsemi", F.oracle_hcm, ("onsemi", "hctz.fa.us2.oraclecloud.com", "CX_1001")),
    ("Western Digital", F.smartrecruiters, ("Western Digital", "WesternDigital")),
    ("Sandisk", F.smartrecruiters, ("Sandisk", "Sandisk")),
    ("Cirrus Logic", F.lever, ("Cirrus Logic", "cirrus", "eu")),
]
for company, board in GREENHOUSE:
    SOURCES.append((f"{company} (Greenhouse {board})", F.greenhouse, (company, board)))
for company, org in ASHBY:
    SOURCES.append((company, F.ashby, (company, org)))
SOURCES.append(("104 人力銀行（台灣）", F.job104, (["暑期實習 IC設計", "暑期實習 數位IC", "暑期實習 驗證",
                                                  "暑期實習 硬體", "實習生 晶片設計", "summer intern IC"],)))

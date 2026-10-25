"""Relevance rules shared by every source.

A posting is kept when it is an internship that a rising-senior ECE undergraduate
(hardware design / verification / computer architecture / AI accelerators) can
apply to, located in the US or Taiwan. Each kept posting gets a tier:
  core     - title names front-end silicon, verification, architecture or accelerator work
  related  - neighbouring fields: hardware, embedded, firmware, validation, compilers, ML systems
  stretch  - other hardware-category roles (SimplifyJobs rows only)
"""
import re

CORE = [
    r"\basic\b", r"\brtl\b", r"design verification", r"\bdv\b", r"verification",
    r"digital (ic |circuit )?design", r"logic design", r"\bsilicon\b", r"\bsoc\b",
    r"\bfpga\b", r"emulation", r"pre-?silicon", r"\bvlsi\b", r"\bchip\b",
    r"computer architecture", r"(cpu|gpu|hardware|chip|soc|silicon|ml|ai|accelerator|memory) architect",
    r"micro-?architecture", r"\bcpu\b", r"\bgpu\b", r"\bnpu\b", r"\btpu\b", r"accelerat",
    r"ai hardware", r"ml hardware", r"hardware design", r"ic design", r"\bdft\b", r"design for test",
    r"physical design", r"performance model", r"hardware engineer",
    # Traditional Chinese (104 / Taiwan postings)
    r"ic\s*設計", r"數位\s*ic", r"數位電路", r"晶片", r"驗證", r"硬體設計", r"verilog", r"計算機架構",
]
ADJ = [
    r"hardware", r"validation", r"embedded", r"firmware", r"electrical",
    r"\bcompiler\b", r"\bcuda\b", r"kernel", r"performance", r"\bhpc\b",
    r"ml systems", r"ai infrastructure", r"inference", r"systems engineer",
    r"analog", r"mixed[- ]signal", r"\brf\b", r"circuit", r"semiconductor",
    r"memory", r"\bdram\b", r"\bhbm\b", r"robotics", r"edge ai", r"device",
    r"computer engineer", r"architect",
    r"硬體", r"韌體", r"嵌入式", r"半導體", r"電子工程", r"類比",
]
EXCLUDE_TITLE = [
    r"mechanical", r"civil", r"chemical", r"manufacturing", r"supply chain",
    r"\bsales\b", r"marketing", r"finance", r"accounting", r"\bhr\b", r"recruit",
    r"technician", r"facilit", r"quality engineer", r"process engineer",
    r"\bmba\b", r"product manag", r"program manag", r"business", r"legal",
    r"clinical", r"biolog", r"construction", r"packaging",
    r"業務", r"行銷", r"財務", r"會計", r"人資", r"法務", r"助理", r"作業員",
]
# Extra exclusions for postings that come straight from company sites
# (SimplifyJobs already filters these through its own term/degree fields).
OFFICIAL_EXCLUDE = [
    r"ph\.?\s?d", r"doctoral", r"post-?doc", r"\bmasters?\b", r"master's", r"\bms\b", r"\bm\.s\.",
    r"(?<!under)graduate\b", r"new grad", r"new college grad", r"full[- ]time", r"\bmba\b",
    r"long[- ]term", r"\b1[26][- ]month", r"\bpey\b", r"apprentice",
    r"碩士", r"博士", r"研發替代役", r"\brdss\b",
]
INTERN_RE = re.compile(r"\bintern(s|ship|ships)?\b|\bco-?op\b|\bstudent\b|實習|summer associate", re.I)
BIG = ["nvidia", "apple", "amd", "advanced micro", "qualcomm", "google", "meta", "microsoft", "amazon",
       "intel", "tesla", "broadcom", "marvell", "samsung", "arm", "ibm", "cisco", "texas instruments",
       "analog devices", "micron", "western digital", "sandisk", "globalfoundries", "tsmc", "mediatek",
       "synopsys", "cadence", "astera", "tenstorrent", "cerebras", "groq", "d-matrix", "etched",
       "sambanova", "sifive", "lattice", "altera", "rambus", "nxp", "renesas", "hewlett packard", "hpe",
       "dell", "bytedance", "tiktok", "oracle", "x.ai", "xai", "openai", "anthropic",
       "聯發科", "台積電", "瑞昱", "聯詠", "創意電子", "世芯", "晶心", "群聯", "慧榮", "聯電"]
US_PERSON_COMPANIES = [
    "lockheed", "raytheon", "rtx", "northrop", "l3harris", "bae systems",
    "general dynamics", "anduril", "spacex", "blue origin", "leidos", "booz allen",
    "lincoln laboratory", "sandia", "lawrence livermore", "los alamos", "space dynamics",
    "v2x", "north atlantic industries", "astranis", "cesiumastro", "saic", "caci",
    "mitre", "aerospace corporation", "johns hopkins applied physics", "huntington ingalls",
    "textron", "boeing", "collins aerospace", "pratt & whitney", "honeywell aerospace",
    "sierra nevada", "kratos", "parsons", "peraton", "palantir", "shield ai",
    "united launch", "rocket lab", "firefly", "relativity", "true anomaly", "epirus",
]
TITLE_US_PERSON = [r"clearance", r"\bts/sci\b", r"u\.?s\.? citizen", r"\bitar\b", r"government",
                   r"defense", r"federal", r"\bqgov\b"]

TW_RE = re.compile(r"taiwan|taipei|hsinchu|taichung|tainan|kaohsiung|taoyuan|zhubei|chupei|"
                   r"新竹|台北|臺北|台中|臺中|台南|臺南|高雄|桃園|竹北|台灣|臺灣|竹科|中科|南科", re.I)
NON_US_RE = re.compile(
    r"\bcanada\b|\bontario\b|\btoronto\b|\bvancouver\b|\bottawa\b|\bmontr[eé]al\b|\bmarkham\b|\bwaterloo\b|"
    r"\bcalgary\b|\bburlington, on\b|, bc\b|, qc\b|\bab, can|\bcan\b|"
    r"\buk\b|united kingdom|\blondon\b|\bengland\b|\bscotland\b|\bgermany\b|\bindia\b|\bisrael\b|\bchina\b|"
    r"\bshanghai\b|\bbeijing\b|\bshenzhen\b|\bsingapore\b|\bjapan\b|\btokyo\b|\bkorea\b|\bireland\b|"
    r"\bnetherlands\b|\bfrance\b|\bpoland\b|\bmexico\b|\bswitzerland\b|\bsweden\b|\bspain\b|\bitaly\b|"
    r"\baustralia\b|\bvietnam\b|\bmalaysia\b|\bpenang\b|\bserbia\b|\bbelgrade\b|\bbangalore\b|\bbengaluru\b|"
    r"\bhyderabad\b|\bphilippines\b|\bcosta rica\b|\bbrazil\b|\bdenmark\b|\bfinland\b|\bromania\b|"
    r"\bczech\b|\bhungary\b|\baustria\b|\bbelgium\b|\bportugal\b|\bgreece\b|\begypt\b|\bthailand\b|"
    r"\bindonesia\b|\bhong kong\b|\bmacau\b|\bunited arab\b|\bdubai\b|\bnew zealand\b|\bargentina\b|\bchile\b|"
    r"\bcolombia\b|\bnorway\b|\bturkey\b|\bsaudi\b|\barmenia\b|\bukraine\b|\bwarszawa\b|\bwarsaw\b|\bmunich\b|"
    r"\bdresden\b|\bberlin\b|\bparis\b|\bcambridge, uk|\bst albans\b|\bhaifa\b|\btel aviv\b|\byokneam\b",
    re.I)
US_STATE_CODES = ("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH "
                  "NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC").split()
US_STATE_RE = re.compile(r"(?:^|[\s,(/-])(" + "|".join(US_STATE_CODES) + r")(?:$|[\s,)/-])")
US_WORDS_RE = re.compile(
    r"united states|\busa\b|\bu\.s\.|^us\b|\bus,|, us\b|\bus-|remote.{0,6}\bus\b|"
    r"california|texas|oregon|washington|massachusetts|new york|north carolina|arizona|colorado|idaho|"
    r"minnesota|florida|utah|pennsylvania|michigan|illinois|virginia|maryland|new jersey|\bohio\b|"
    r"wisconsin|vermont|tennessee|alabama|nevada|new mexico|kansas|missouri|indiana\b|kentucky|connecticut|"
    r"delaware|\biowa\b|louisiana|\bmaine\b|mississippi|montana|nebraska|new hampshire|north dakota|"
    r"oklahoma|rhode island|south carolina|south dakota|west virginia|wyoming|hawaii|alaska|arkansas|"
    r"santa clara|san jose|sunnyvale|cupertino|mountain view|palo alto|san diego|seattle|redmond|bellevue|"
    r"austin|hillsboro|folsom|boise|raleigh|durham|morrisville|fort collins|longmont|boulder|westborough|"
    r"boxborough|chandler|phoenix|tempe|irvine|madison|pittsburgh|atlanta|dallas|richardson|plano|houston|"
    r"denver|colorado springs|poughkeepsie|fishkill|orlando|minneapolis|beaverton|portland|fremont|milpitas|"
    r"san francisco|los angeles|knoxville|tucson|sugar land|nampa|norwood|wilmington|secaucus|bridgewater|"
    r"burlington, vt|rochester, (ny|mn)|hudson valley|manassas|kirkland|santa barbara|goleta|ann arbor",
    re.I)


def hit(pats, s):
    return [p for p in pats if re.search(p, s, re.I)]


def label(p):
    return re.sub(r"\\b|\\s\*|\\|\(|\)|\?|-\?", "", p).replace("[- ]", " ").strip()


def classify_location(loc):
    # Workday path segments look like "US-CA-Santa-Clara" or "Taiwan-Hsinchu".
    s = (loc or "").replace("-", " ") if re.match(r"^[A-Za-z]+(-[A-Za-z]+)+$", loc or "") else (loc or "")
    if TW_RE.search(s):
        return "TW"
    if NON_US_RE.search(s):
        return "OTHER"
    if US_WORDS_RE.search(s) or US_STATE_RE.search(s):
        return "US"
    return "UNKNOWN"


def region_for(locations):
    """US if any location is in the US, TW if any is in Taiwan, None if all are elsewhere.
    Unrecognised strings ("2 Locations", "Remote") count as US so they are not lost."""
    kinds = [classify_location(l) for l in (locations or []) if l]
    if not kinds:
        return "US"
    if "US" in kinds:
        return "US"
    if "TW" in kinds:
        return "TW"
    if all(k == "OTHER" for k in kinds):
        return None
    return "US"


def tier_for(title, category=None):
    """Return (tier, keyword labels) or (None, []) when the title is off-field."""
    t = (title or "").lower()
    if hit(EXCLUDE_TITLE, t):
        return None, []
    core = hit(CORE, t)
    adj = hit(ADJ, t)
    if core:
        return "core", [label(p) for p in core][:5]
    if adj:
        return "related", [label(p) for p in adj][:5]
    if category in ("Hardware", "Hardware Engineering"):
        return "stretch", []
    return None, []


def official_ok(title):
    """Internship, undergraduate-eligible, Summer 2027 (or unspecified term)."""
    t = (title or "").lower()
    if not INTERN_RE.search(t):
        return False
    if hit(OFFICIAL_EXCLUDE, t) and not re.search(r"\bbs\b|bachelor|undergrad|大學", t):
        return False
    years = set(re.findall(r"\b20(\d\d)\b", t))
    if years and "27" not in years:
        return False
    if re.search(r"\b(winter|spring|fall|autumn)\b", t) and "summer" not in t:
        return False
    return True


def term_for(title):
    t = (title or "").lower()
    if "summer" in t and "2027" in t:
        return "Summer 2027"
    if "2027" in t:
        return "2027"
    if "summer" in t or "暑期" in t:
        return "Summer"
    return ""


def degrees_for(title):
    t = (title or "").lower()
    if re.search(r"\bbs\b|bachelor|undergrad", t):
        return ["Bachelor's"]
    return []


def us_person_likely(company, title):
    cl = (company or "").lower()
    return any(k in cl for k in US_PERSON_COMPANIES) or bool(hit(TITLE_US_PERSON, (title or "").lower()))


def is_big(company):
    cl = (company or "").lower()
    return any(re.search(r"(?<![a-z])" + re.escape(b) + r"(?![a-z])", cl) for b in BIG)

from ..schemas import BundleItem, BundleResult, Excluded, Profile
from .catalogue import CatalogueProduct, get_catalogue

BASE_IDS = ("P01", "P02", "P03", "P04", "P05", "P06")
LINE_IDS = ("P07", "P08")
SEGMENT_BASES = {"micro": ["P01"], "prof": ["P02", "P01"], "multi": ["P02", "P01"], "mfg": ["P05", "P03", "P02"]}
DOWNGRADES = {"P06": ["P05", "P03", "P02", "P01"], "P05": ["P03", "P02", "P01"], "P03": ["P02", "P01"],
              "P02": ["P01"], "P01": ["P04"], "P04": ["P01"]}
ADD_ONS = {"micro": ["P23", "P22", "P09", "P18"], "prof": ["P11", "P22", "P13", "P08"],
           "multi": ["P25", "P22", "P13", "P08"], "mfg": ["P09", "P23", "P25", "P11"]}
BUNDLE_NAMES = {"micro": "Dukaan Digital", "prof": "Office Pro", "multi": "One Bill Multi-site", "mfg": "Factory Connect"}
NEEDS = ["pos", "cctv", "whatsapp", "sms", "email", "backup", "security", "uptime", "wifi", "phone", "remote",
         "machines", "vehicles", "website", "mobile"]

BENEFITS = {
    "P01": ("Fast, unlimited fibre internet for your shop", "आपकी दुकान के लिए तेज़, अनलिमिटेड फ़ाइबर इंटरनेट"),
    "P02": ("300 Mbps fibre – enough for the whole office", "300 Mbps फ़ाइबर – पूरे ऑफ़िस के लिए काफ़ी"),
    "P03": ("1 Gbps fibre with priority support", "1 Gbps फ़ाइबर, प्रायोरिटी सपोर्ट के साथ"),
    "P04": ("Wireless 5G internet, plug-and-play in 2 days", "वायरलेस 5G इंटरनेट, 2 दिन में चालू"),
    "P05": ("Dedicated internet line with 99.5% uptime promise", "अपनी अलग इंटरनेट लाइन, 99.5% अपटाइम गारंटी"),
    "P06": ("100 Mbps dedicated line with 99.9% uptime promise", "100 Mbps अलग लाइन, 99.9% अपटाइम गारंटी"),
    "P07": ("Business mobile line, 50 GB data, unlimited calls", "बिज़नेस मोबाइल लाइन, 50 GB डेटा, अनलिमिटेड कॉल"),
    "P08": ("Premium line with 150 GB data and roaming", "150 GB डेटा और रोमिंग वाली प्रीमियम लाइन"),
    "P09": ("Backup internet that switches on if the main line drops", "मेन लाइन बंद हो तो अपने-आप चालू होने वाला बैकअप इंटरनेट"),
    "P10": ("Manage internet across all branches from one place", "सभी ब्रांच का इंटरनेट एक जगह से संभालें"),
    "P11": ("Fixed IP to view CCTV or reach your server remotely", "CCTV या सर्वर को दूर से देखने के लिए फ़िक्स्ड IP"),
    "P12": ("Business phone lines with IVR and call recording", "IVR और कॉल रिकॉर्डिंग वाली बिज़नेस फ़ोन लाइनें"),
    "P13": ("1800 toll-free number for your customers", "ग्राहकों के लिए 1800 टोल-फ़्री नंबर"),
    "P14": ("10,000 SMS a month for alerts and offers", "अलर्ट और ऑफ़र के लिए हर महीने 10,000 SMS"),
    "P15": ("Verified WhatsApp with catalogue to reach customers", "ग्राहकों तक पहुँचने के लिए वेरिफ़ाइड WhatsApp और कैटलॉग"),
    "P16": ("Business email, documents and video meetings", "बिज़नेस ईमेल, डॉक्यूमेंट और वीडियो मीटिंग"),
    "P17": ("Automatic 1 TB backup of PCs and phones", "PC और फ़ोन का अपने-आप 1 TB बैकअप"),
    "P18": ("Your own website and domain", "आपकी अपनी वेबसाइट और डोमेन"),
    "P19": ("GST-ready billing with UPI and card payments", "UPI और कार्ड पेमेंट के साथ GST-रेडी बिलिंग"),
    "P20": ("Antivirus and ransomware protection", "एंटीवायरस और रैनसमवेयर से सुरक्षा"),
    "P21": ("Managed firewall watched by our security team", "हमारी सिक्योरिटी टीम द्वारा मैनेज्ड फ़ायरवॉल"),
    "P22": ("Separate free Wi-Fi for customers", "ग्राहकों के लिए अलग फ़्री Wi-Fi"),
    "P23": ("HD camera with 30-day cloud recording on your phone", "फ़ोन पर देखें, 30 दिन क्लाउड रिकॉर्डिंग वाला HD कैमरा"),
    "P24": ("Sensors to track machine uptime and power use", "मशीन अपटाइम और बिजली खपत ट्रैक करने वाले सेंसर"),
    "P25": ("Live GPS tracking for your vehicles", "आपकी गाड़ियों की लाइव GPS ट्रैकिंग"),
}
RULE_TEXT = {
    "tier": ("is available only in tier-1 cities", "सिर्फ़ टियर-1 शहरों में मिलता है"),
    "employees": ("needs at least {n} staff", "कम से कम {n} कर्मचारियों के लिए है"),
    "sites": ("needs at least {n} locations", "कम से कम {n} लोकेशन के लिए है"),
    "gstin": ("needs an active GSTIN", "इसके लिए Active GSTIN ज़रूरी है"),
    "dependency": ("needs an internet connection in the same bundle", "इसके लिए इसी बंडल में इंटरनेट कनेक्शन ज़रूरी है"),
}
SEGMENT_WORDS = {"micro": ("shop", "दुकान"), "prof": ("office", "ऑफ़िस"),
                 "multi": ("multi-branch business", "कई ब्रांच वाले बिज़नेस"), "mfg": ("factory", "फ़ैक्ट्री")}


class IneligibleBundleError(ValueError):
    pass


def inr(n: int) -> str:
    s = str(abs(int(n)))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        s = ",".join(([head] if head else []) + groups) + "," + tail
    return ("-" if n < 0 else "") + "₹" + s


def failed_rules(p: CatalogueProduct, profile: Profile, bundle_ids, check_dependency: bool = True) -> list[str]:
    failed = []
    if profile.city_tier not in p.city_tiers:
        failed.append("tier")
    if profile.employees < p.min_employees:
        failed.append("employees")
    if profile.sites < p.min_sites:
        failed.append("sites")
    if p.requires_gstin and not profile.gstin_active:
        failed.append("gstin")
    if check_dependency and p.requires_one_of and not set(p.requires_one_of) & set(bundle_ids):
        failed.append("dependency")
    return failed


def is_eligible(p: CatalogueProduct, profile: Profile, bundle_ids) -> bool:
    return not failed_rules(p, profile, bundle_ids)


def rule_reason(p: CatalogueProduct, rules: list[str]) -> tuple[str, str]:
    n = {"employees": p.min_employees, "sites": p.min_sites}
    en = " and ".join(RULE_TEXT[r][0].format(n=n.get(r)) for r in rules)
    hi = " और ".join(RULE_TEXT[r][1].format(n=n.get(r)) for r in rules)
    return f"{p.name} {en}.", f"{p.name} {hi}।"


def quantity(p: CatalogueProduct, profile: Profile) -> int:
    emp, sites = profile.employees, profile.sites
    if p.product_id == "P24":
        return 5
    return {
        "site": sites,
        "line": 2 if profile.segment == "micro" else min(emp, 5),
        "user": min(emp, 25),
        "device": min(emp, 25),
        "camera": 2 * sites,
        "counter": sites,
        "channel": max(2, emp // 5),
        "vehicle": max(1, profile.vehicles),
    }.get(p.unit, 1)


class _Builder:
    def __init__(self, profile: Profile):
        self.profile = profile
        self.cat = get_catalogue()
        self.items: dict[str, BundleItem] = {}
        self.excluded: dict[str, Excluded] = {}
        self.unlocks: list[str] = []
        self.notes: list[tuple[str, str]] = []

    def try_add(self, pid: str, *, qty: int | None = None, optional: bool = False, enabled: bool = True,
                silent: bool = False, is_base: bool = False, reason: tuple[str, str] | None = None) -> bool:
        if pid in self.items:
            if not optional and self.items[pid].optional:
                self.items[pid].optional, self.items[pid].enabled = False, True
            return True
        p = self.cat[pid]
        rules = failed_rules(p, self.profile, self.items, check_dependency=False)
        if rules:
            if rules == ["gstin"] and not optional:
                if pid not in self.unlocks:
                    self.unlocks.append(pid)
            elif not silent:
                en, hi = rule_reason(p, rules)
                self.excluded[pid] = Excluded(product_id=pid, name=p.name, reason_en=en, reason_hi=hi, rules=rules)
            return False
        q = qty or quantity(p, self.profile)
        en, hi = reason or BENEFITS[pid]
        self.items[pid] = BundleItem(
            product_id=pid, name=p.name, category=p.category, unit=p.unit, qty=q, unit_price=p.price_min,
            monthly=p.price_min * q, setup=p.setup * q, reason_en=en, reason_hi=hi,
            optional=optional, enabled=enabled, is_base=is_base)
        return True

    def exclude(self, pid: str, rules: list[str]) -> None:
        p = self.cat[pid]
        en, hi = rule_reason(p, rules)
        self.excluded[pid] = Excluded(product_id=pid, name=p.name, reason_en=en, reason_hi=hi, rules=rules)

    def add_base(self) -> None:
        prof = self.profile
        requested = [pid for pid in prof.requested_products if pid in BASE_IDS]
        if prof.cheapest:
            options = sorted(("P01", "P02", "P04"), key=lambda pid: self.cat[pid].price_min)
        elif requested:
            req = requested[0]
            rules = failed_rules(self.cat[req], prof, (), check_dependency=False)
            if rules:
                self.exclude(req, rules)
                options = DOWNGRADES[req]
                if rules == ["gstin"] and req not in self.unlocks:
                    self.unlocks.append(req)
            else:
                options = [req]
        elif prof.segment == "micro" and prof.no_fibre:
            options = ["P04", "P01"]
        else:
            options = SEGMENT_BASES[prof.segment]
        for pid in options:
            if not failed_rules(self.cat[pid], prof, (), check_dependency=False):
                self.try_add(pid, is_base=True)
                if requested and pid != requested[0]:
                    req = self.cat[requested[0]]
                    self.notes.append((f"We've offered {self.cat[pid].name} instead of {req.name}.",
                                       f"{req.name} की जगह {self.cat[pid].name} दिया है।"))
                return
            if failed_rules(self.cat[pid], prof, (), check_dependency=False) == ["gstin"] and pid not in self.unlocks:
                self.unlocks.append(pid)
        self.try_add("P01", is_base=True)

    def add_need(self, need: str) -> None:
        prof, seg = self.profile, self.profile.segment
        match need:
            case "pos":
                self.try_add("P19")
            case "cctv":
                self.try_add("P23")
            case "whatsapp":
                if not self.try_add("P15"):
                    self.try_add("P18")
                    if "P15" in self.unlocks:
                        self.notes.append(("WhatsApp Business API unlocks once you add an active GSTIN.",
                                           "Active GSTIN जोड़ते ही WhatsApp Business API मिल जाएगा।"))
            case "sms":
                self.try_add("P14")
            case "email":
                self.try_add("P16")
            case "backup":
                self.try_add("P17")
            case "security":
                self.try_add("P20")
                if prof.employees >= 10:
                    self.try_add("P21", silent=True)
            case "uptime":
                self.try_add("P09")
            case "wifi":
                self.try_add("P22")
            case "phone":
                self.try_add("P12")
                if seg in ("multi", "prof"):
                    self.try_add("P13", optional=True, enabled=False, silent=True)
            case "remote":
                self.try_add("P11")
            case "machines":
                self.try_add("P24")
            case "vehicles":
                self.try_add("P25")
            case "website":
                self.try_add("P18")
            case "mobile":
                self.try_add("P07")
                if seg in ("prof", "multi"):
                    self.try_add("P08", qty=1, optional=True, enabled=False, silent=True)

    def add_defaults(self) -> None:
        prof = self.profile
        match prof.segment:
            case "micro":
                self.try_add("P07", qty=2)
                self.try_add("P19")
                if not self.try_add("P15"):
                    self.try_add("P18")
            case "prof":
                self.try_add("P09")
                self.try_add("P16")
                self.try_add("P17")
                self.try_add("P20")
                self.try_add("P07", qty=2)
            case "multi":
                self.try_add("P09")
                self.try_add("P23")
                self.try_add("P19")
                self.try_add("P10", silent=True)
            case "mfg":
                self.try_add("P21", silent=True)
                self.try_add("P24", silent=True)
                self.try_add("P16")

    def resolve_dependencies(self) -> None:
        for item in list(self.items.values()):
            p = self.cat[item.product_id]
            if p.requires_one_of and not set(p.requires_one_of) & set(self.items):
                fallback = "P01" if self.profile.segment == "micro" else "P02"
                candidates = [fallback] + [c for c in p.requires_one_of if c != fallback]
                for base in candidates:
                    if base in p.requires_one_of and self.try_add(
                            base, is_base=True, silent=True,
                            reason=(f"Needed to run {p.name}", f"{p.name} चलाने के लिए ज़रूरी")):
                        break


def enforce_dependencies(items: list[BundleItem], profile: Profile) -> list[tuple[str, str]]:
    """Disable enabled items whose required base connection is switched off. Returns warnings."""
    cat = get_catalogue()
    warnings = []
    changed = True
    while changed:
        changed = False
        active = {i.product_id for i in items if i.enabled}
        for item in items:
            p = cat[item.product_id]
            if item.enabled and p.requires_one_of and not set(p.requires_one_of) & active:
                item.enabled = False
                changed = True
                warnings.append((f"{p.name} was removed because it needs an internet connection.",
                                 f"{p.name} हटाया गया, क्योंकि इसके लिए इंटरनेट कनेक्शन ज़रूरी है।"))
    return warnings


def validate(items: list[BundleItem], profile: Profile) -> None:
    cat = get_catalogue()
    active = [i.product_id for i in items if i.enabled]
    for pid in active:
        rules = failed_rules(cat[pid], profile, active)
        if rules:
            raise IneligibleBundleError(f"{pid} is not eligible: {rules}")


def _why(profile: Profile, items: list[BundleItem], monthly: int, setup: int, contract: int) -> tuple[list, list]:
    cat = get_catalogue()
    word_en, word_hi = SEGMENT_WORDS[profile.segment]
    active = [i for i in items if i.enabled]
    base = next((i for i in active if i.is_base), None)
    sites_en = f" across {profile.sites} locations" if profile.sites > 1 else ""
    sites_hi = f" {profile.sites} लोकेशन पर" if profile.sites > 1 else ""
    en, hi = [], []
    if base:
        people_en = "1 person" if profile.employees == 1 else f"{profile.employees} people"
        people_hi = "1 व्यक्ति" if profile.employees == 1 else f"{profile.employees} लोगों"
        en.append(f"For your {word_en} with {people_en}{sites_en}, {base.name} keeps everything online.")
        hi.append(f"{people_hi} वाली आपकी {word_hi} के लिए{sites_hi} {base.name} सब कुछ ऑनलाइन रखेगा।")
    else:
        en.append("You asked only for mobile lines, so this plan has just those – add fibre any time later.")
        hi.append("आपने सिर्फ़ मोबाइल प्लान माँगा है, इसलिए इसमें वही है – फ़ाइबर बाद में कभी भी जोड़ सकते हैं।")
    extras = [i for i in active if not i.is_base and i.product_id not in LINE_IDS][:2]
    if extras:
        en.append(" ".join(f"{cat[i.product_id].name}: {i.reason_en}." for i in extras))
        hi.append(" ".join(f"{cat[i.product_id].name}: {i.reason_hi}।" for i in extras))
    en.append(f"{inr(monthly)}/month + GST, {inr(setup)} one-time setup, {contract}-month contract.")
    hi.append(f"{inr(monthly)}/महीना + GST, {inr(setup)} एक बार का सेटअप, {contract} महीने का कॉन्ट्रैक्ट।")
    return en, hi


def summarise(profile: Profile, items: list[BundleItem], bundle_name: str, excluded=(), unlocks=(),
              notes=()) -> BundleResult:
    validate(items, profile)
    cat = get_catalogue()
    for i in items:
        i.monthly, i.setup = i.unit_price * i.qty, cat[i.product_id].setup * i.qty
    active = [i for i in items if i.enabled]
    monthly = sum(i.monthly for i in active)
    setup = sum(i.setup for i in active)
    contract = max([12] + [cat[i.product_id].min_contract_months for i in active])
    install = max([0] + [cat[i.product_id].install_days for i in active])
    why_en, why_hi = _why(profile, items, monthly, setup, contract)

    savings, s_en, s_hi = None, "", ""
    if profile.current_spend:
        x = profile.current_spend
        savings = x - monthly
        if savings >= 0:
            s_en = f"You pay about {inr(x)} today across vendors → {inr(monthly)} on one bill."
            s_hi = f"आज आप अलग-अलग जगह लगभग {inr(x)} देते हैं → अब एक बिल में {inr(monthly)}।"
        else:
            new = ", ".join([i.name for i in active if not i.is_base and i.product_id not in LINE_IDS][:3]) or "faster internet"
            s_en = f"{inr(-savings)} more per month than today, and you also get {new}."
            s_hi = f"आज से {inr(-savings)} महीना ज़्यादा, और साथ में मिलेगा: {new}।"

    return BundleResult(
        bundle_name=bundle_name, items=items, monthly_total=monthly, setup_total=setup, contract_months=contract,
        install_days=install, excluded=list(excluded), unlocks_with_gstin=list(unlocks), savings_vs_current=savings,
        savings_line_en=s_en, savings_line_hi=s_hi, why_en=why_en, why_hi=why_hi,
        notes_en=[n[0] for n in notes], notes_hi=[n[1] for n in notes])


def recommend_bundle(profile: Profile) -> BundleResult:
    b = _Builder(profile)
    if profile.gstin and profile.gstin_status and not profile.gstin_active:
        b.notes.append((f"Your GSTIN shows as {profile.gstin_status}, so we've treated it as no GSTIN for now.",
                        f"आपका GSTIN {profile.gstin_status} दिख रहा है, इसलिए अभी इसे बिना GSTIN मानकर बंडल बनाया है।"))

    if profile.mobile_only:
        b.try_add("P08" if "P08" in profile.requested_products else "P07")
        b.notes.append(("When you're ready, add Biz Fibre on the same bill – no new paperwork.",
                        "जब चाहें, इसी बिल में Biz Fibre जोड़ें – कोई नया कागज़ नहीं।"))
        name = "Mobile Starter"
    elif profile.cheapest:
        b.add_base()
        b.try_add("P07", qty=1)
        name = "Starter"
    else:
        b.add_base()
        extra_requests = [pid for pid in profile.requested_products if pid not in BASE_IDS]
        for need in profile.needs:
            b.add_need(need)
        for pid in extra_requests:
            b.try_add(pid)
        if profile.use_defaults or (not profile.needs and not extra_requests):
            b.add_defaults()
            name = BUNDLE_NAMES[profile.segment]
            if profile.segment == "micro" and not profile.gstin_active:
                name += " (no-GST starter)"
        else:
            name = "Your custom bundle"
        b.resolve_dependencies()
        for pid in ADD_ONS[profile.segment]:
            b.try_add(pid, qty=1 if pid == "P08" else None, optional=True, enabled=False, silent=True)

    items = [i for i in b.items.values() if not (i.optional and failed_rules(b.cat[i.product_id], profile, b.items))]
    return summarise(profile, items, name, b.excluded.values(), b.unlocks, b.notes)
